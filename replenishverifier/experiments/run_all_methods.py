import argparse
import csv
import logging
from collections import defaultdict
from pathlib import Path

from replenishverifier.experiments.evaluation import (
    benchmark_table,
    save_csv,
    save_markdown_table,
    save_result_bundle,
    summarize_by_difficulty,
    summarize_by_method,
    write_json,
)
from replenishverifier.experiments.methods import (
    APPENDIX_METHODS,
    MAIN_METHODS,
    METHODS,
    build_generic_repair_prompts,
    build_repair_prompts,
    evaluate_all_candidates,
    select_for_method,
)
from replenishverifier.utils.io import read_jsonl, write_jsonl

LOGGER = logging.getLogger("replenishverifier.experiments")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def parse_int_list(text):
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def group_candidates(candidates):
    grouped = defaultdict(list)
    for row in candidates:
        grouped[row.get("problem_id")].append(row)
    return grouped


def _weak_candidate_code(sample, mode):
    params = sample.get("parameters", {})
    problem_type = sample.get("problem_type")
    if mode == "remove_inventory_balance":
        return """
import pulp


def build_model():
    model = pulp.LpProblem('remove_inventory_balance', pulp.LpMinimize)
    Q_0 = pulp.LpVariable('Q_0', lowBound=0)
    I_0 = pulp.LpVariable('I_0', lowBound=0)
    model += Q_0 + I_0, 'total_cost'
    model += Q_0 + I_0 >= 0, 'dummy_nonnegative_0'
    return model
""".strip() + "\n"

    if mode == "remove_capacity_constraint":
        if problem_type != "multi_item_capacity":
            return _weak_candidate_code(sample, "remove_inventory_balance")
        return f"""
import pulp

PARAMS = {params!r}


def build_model():
    params = PARAMS
    N, T = params['items'], params['periods']
    model = pulp.LpProblem('remove_capacity_constraint', pulp.LpMinimize)
    Q = pulp.LpVariable.dicts('Q', ((i, t) for i in range(N) for t in range(T)), lowBound=0)
    I = pulp.LpVariable.dicts('I', ((i, t) for i in range(N) for t in range(T)), lowBound=0)
    model += pulp.lpSum(params['unit_order_cost'][i] * Q[(i, t)] + params['holding_cost'][i] * I[(i, t)] for i in range(N) for t in range(T)), 'total_cost'
    for i in range(N):
        for t in range(T):
            prev = params['initial_inventory'][i] if t == 0 else I[(i, t - 1)]
            model += I[(i, t)] == prev + Q[(i, t)] - params['demand'][i][t], f'inventory_balance_{{i}}_{{t}}'
    return model
""".strip() + "\n"

    if mode == "remove_big_m_constraint":
        if problem_type != "fixed_order_cost_big_m":
            return _weak_candidate_code(sample, "remove_inventory_balance")
        return f"""
import pulp

PARAMS = {params!r}


def build_model():
    params = PARAMS
    T = params['periods']
    model = pulp.LpProblem('remove_big_m_constraint', pulp.LpMinimize)
    Q = pulp.LpVariable.dicts('Q', range(T), lowBound=0)
    I = pulp.LpVariable.dicts('I', range(T), lowBound=0)
    Y = pulp.LpVariable.dicts('Y', range(T), lowBound=0, upBound=1, cat='Binary')
    model += pulp.lpSum(params['unit_order_cost'] * Q[t] + params['holding_cost'] * I[t] + params['fixed_order_cost'] * Y[t] for t in range(T)), 'total_cost'
    for t in range(T):
        prev = params['initial_inventory'] if t == 0 else I[t - 1]
        model += I[t] == prev + Q[t] - params['demand'][t], f'inventory_balance_{{t}}'
    return model
""".strip() + "\n"

    raise ValueError(f"Unknown weak candidate mode: {mode}")


def make_demo_candidates(benchmark_rows):
    """Create CPU-only demo candidates when no LLM candidates are available.

    Each problem receives candidates named correct, remove_inventory_balance,
    remove_capacity_constraint, remove_big_m_constraint, and syntax_error.
    This makes the smoke test exercise both successful and explainable failures.
    """
    candidates = []
    for sample in benchmark_rows:
        pid = sample["id"]
        demo_specs = [
            ("syntax_error", "Non-executable candidate for robustness testing.", "def build_model(:\n    pass\n"),
            ("remove_inventory_balance", "Executable candidate missing inventory-balance-like structure.", _weak_candidate_code(sample, "remove_inventory_balance")),
            ("remove_capacity_constraint", "Executable candidate missing capacity constraints when relevant.", _weak_candidate_code(sample, "remove_capacity_constraint")),
            ("remove_big_m_constraint", "Executable candidate missing Big-M constraints when relevant.", _weak_candidate_code(sample, "remove_big_m_constraint")),
            ("correct", "Reference PuLP model used as a correct candidate.", sample["reference_code"]),
        ]
        for idx, (name, text, code) in enumerate(demo_specs):
            candidates.append({
                "problem_id": pid,
                "candidate_id": f"cand_{idx}_{name}",
                "method": f"demo_{name}",
                "generated_text": text,
                "generated_code": code,
            })
    return candidates


def write_summary_bundle(prefix, summary_rows, title):
    prefix = Path(prefix)
    write_jsonl(prefix.with_suffix(".jsonl"), summary_rows)
    save_summary_csv(prefix.with_suffix(".csv"), summary_rows)
    save_markdown_table(prefix.with_suffix(".md"), summary_rows, title=title)


def save_summary_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_experiments(benchmark_path, candidates_path, out_dir, k_values, timeout=30, max_k=None, demo_if_empty=True, use_objective_consensus=False, allow_feasible_selection=False, appendix_methods_in_main=False):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = out_dir / "candidate_runs"

    benchmark_rows = read_jsonl(benchmark_path)
    benchmark = {row["id"]: row for row in benchmark_rows}
    if not benchmark:
        raise ValueError(f"No benchmark rows found: {benchmark_path}")

    candidates = read_jsonl(candidates_path)
    if not candidates and demo_if_empty:
        LOGGER.warning("Candidate file is empty or missing. Generating demo candidates for CPU smoke run: %s", candidates_path)
        candidates = make_demo_candidates(benchmark_rows)
        demo_path = out_dir / "demo_candidates.generated.jsonl"
        write_jsonl(demo_path, candidates)
        LOGGER.info("Wrote demo candidates to %s", demo_path)
    if not candidates:
        raise ValueError(f"No candidate rows found: {candidates_path}")

    LOGGER.info("Loaded %d benchmark rows and %d candidate rows", len(benchmark), len(candidates))
    candidates_by_problem = group_candidates(candidates)

    LOGGER.info("Evaluating all candidates with solver and LP structure verifier")
    evaluated_by_problem = evaluate_all_candidates(
        benchmark,
        candidates_by_problem,
        work_dir=work_dir,
        timeout=timeout,
        max_k=max_k,
        use_objective_consensus=use_objective_consensus,
        allow_feasible_selection=allow_feasible_selection,
    )
    all_evaluated = [row for rows in evaluated_by_problem.values() for row in rows]
    save_result_bundle(out_dir / "candidate_evaluations", all_evaluated, title="All Candidate Evaluations")

    main_methods = METHODS if appendix_methods_in_main else MAIN_METHODS
    LOGGER.info("Selecting candidates for main methods: %s", ", ".join(main_methods))
    main_rows = []
    for method in main_methods:
        main_rows.extend(select_for_method(method, evaluated_by_problem, benchmark, allow_feasible_selection=allow_feasible_selection))
    main_summary = summarize_by_method(main_rows)
    save_result_bundle(out_dir / "main_results", main_rows, summary_rows=main_summary, title="Main Results")

    repair_prompts = build_repair_prompts(all_evaluated)
    write_jsonl(out_dir / "repair_prompts.jsonl", repair_prompts)
    save_summary_csv(out_dir / "repair_prompts.csv", repair_prompts)
    save_markdown_table(out_dir / "repair_prompts.md", repair_prompts[:50], title="Repair Prompts")

    generic_repair_prompts = build_generic_repair_prompts(all_evaluated)
    write_jsonl(out_dir / "generic_repair_prompts.jsonl", generic_repair_prompts)
    save_summary_csv(out_dir / "generic_repair_prompts.csv", generic_repair_prompts)
    save_markdown_table(out_dir / "generic_repair_prompts.md", generic_repair_prompts[:50], title="Generic Repair Prompts")

    LOGGER.info("Running ablation study")
    ablation_methods = [
        "Direct",
        "Best-of-K",
        "Solver only",
        "Structure only",
        "Consensus only",
        "Solver + Structure",
        "Solver + Consensus",
        "Structure + Consensus",
        "Solver + Structure + Consensus",
        "ReplenishVerifier full",
        "Solver-Filter",
        "OR-R1-like Voting",
        "Structure-Grounded Consistency",
        "Structure-Only",
        "ReplenishVerifier-TypeAware",
        "ReplenishVerifier-TypeAware-Consensus",
        "ReplenishVerifier-Full",
    ]
    ablation_rows = []
    for method in ablation_methods:
        ablation_rows.extend(select_for_method(method, evaluated_by_problem, benchmark, allow_feasible_selection=allow_feasible_selection))
    ablation_summary = summarize_by_method(ablation_rows)
    save_result_bundle(out_dir / "ablation_results", ablation_rows, summary_rows=ablation_summary, title="Ablation Results")

    LOGGER.info("Running low-resource K analysis: %s", k_values)
    low_resource_rows = []
    low_resource_summary = []
    for k in k_values:
        LOGGER.info("Evaluating K=%d", k)
        eval_k = evaluate_all_candidates(
            benchmark,
            candidates_by_problem,
            work_dir=out_dir / f"candidate_runs_k{k}",
            timeout=timeout,
            max_k=k,
            use_objective_consensus=use_objective_consensus,
            allow_feasible_selection=allow_feasible_selection,
        )
        for method in [
            "Best-of-K",
            "Solver-Filter",
            "OR-R1-like Voting",
            "Structure-Grounded Consistency",
            "SIRL-like LP-Stats",
            "OptArgus-like Audit",
            "OptiRepair-like Repair-Prompt",
            "Structure-Only",
            "ReplenishVerifier-TypeAware",
            "ReplenishVerifier-TypeAware-Consensus",
            "ReplenishVerifier-ConsensusSafe",
            "ReplenishVerifier-HybridSafe",
            "ReplenishVerifier-Full",
        ]:
            selected_k = select_for_method(method, eval_k, benchmark, allow_feasible_selection=allow_feasible_selection)
            for row in selected_k:
                row["k"] = k
            low_resource_rows.extend(selected_k)
            summary = summarize_by_method(selected_k)[0]
            summary["k"] = k
            low_resource_summary.append(summary)
    save_result_bundle(out_dir / "low_resource_results", low_resource_rows, summary_rows=low_resource_summary, title="Low-Resource K Analysis")

    difficulty_summary = summarize_by_difficulty(main_rows)
    write_summary_bundle(out_dir / "difficulty_results", difficulty_summary, title="Difficulty-wise Results")

    bench_table = benchmark_table(benchmark_rows)
    write_summary_bundle(out_dir / "benchmark_summary", bench_table, title="Benchmark Summary")

    save_markdown_table(out_dir / "summary.md", main_summary, title="Experiment Summary")

    manifest = {
        "benchmark_path": str(benchmark_path),
        "candidates_path": str(candidates_path),
        "out_dir": str(out_dir),
        "n_benchmark": len(benchmark_rows),
        "n_candidates": len(candidates),
        "methods": METHODS,
        "main_methods": main_methods,
        "appendix_methods": APPENDIX_METHODS,
        "appendix_methods_in_main": bool(appendix_methods_in_main),
        "k_values": k_values,
        "use_objective_consensus": use_objective_consensus,
        "files": {
            "candidate_evaluations": str(out_dir / "candidate_evaluations.jsonl"),
            "main_results": str(out_dir / "main_results.jsonl"),
            "ablation_results": str(out_dir / "ablation_results.jsonl"),
            "low_resource_results": str(out_dir / "low_resource_results.jsonl"),
            "difficulty_results": str(out_dir / "difficulty_results.jsonl"),
            "repair_prompts": str(out_dir / "repair_prompts.jsonl"),
            "generic_repair_prompts": str(out_dir / "generic_repair_prompts.jsonl"),
        },
    }
    write_json(out_dir / "manifest.json", manifest)
    LOGGER.info("Experiment completed. Results saved to %s", out_dir)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Run all ReplenishVerifier paper-style experiment methods.")
    parser.add_argument("--benchmark", required=True, help="Benchmark JSONL path.")
    parser.add_argument("--candidates", required=True, help="Candidate JSONL path.")
    parser.add_argument("--out_dir", default="runs/exp_main", help="Output directory.")
    parser.add_argument("--k_values", default="1,2,4,8", help="Comma-separated K values for low-resource analysis.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds per candidate.")
    parser.add_argument("--max_k", type=int, default=None, help="Optional cap for main-method candidates per problem.")
    parser.add_argument("--no_demo_if_empty", action="store_true", help="Fail instead of generating demo candidates when candidate file is empty.")
    parser.add_argument(
        "--use_objective_consensus",
        action="store_true",
        help="Blend candidate objective-consensus into ReplenishVerifier-Full selection without using reference objectives.",
    )
    parser.add_argument(
        "--allow_feasible_selection",
        action="store_true",
        default=False,
        help="Allow executable Feasible (non-Optimal) candidates through the Hard Selection Gate. Default false: only executable + Optimal candidates can be selected.",
    )
    parser.add_argument(
        "--appendix_methods_in_main",
        action="store_true",
        default=False,
        help="Include all legacy/appendix methods in main_results instead of the concise MAIN_METHODS set.",
    )
    args = parser.parse_args()

    setup_logging()
    run_experiments(
        benchmark_path=args.benchmark,
        candidates_path=args.candidates,
        out_dir=args.out_dir,
        k_values=parse_int_list(args.k_values),
        timeout=args.timeout,
        max_k=args.max_k,
        demo_if_empty=not args.no_demo_if_empty,
        use_objective_consensus=args.use_objective_consensus,
        allow_feasible_selection=args.allow_feasible_selection,
        appendix_methods_in_main=args.appendix_methods_in_main,
    )


if __name__ == "__main__":
    main()
