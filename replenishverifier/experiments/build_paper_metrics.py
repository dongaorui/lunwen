import argparse
from pathlib import Path

from replenishverifier.experiments.paper_metrics import (
    add_bootstrap_ci,
    compute_error_type_summary,
    compute_hard_subset_metrics,
    compute_missed_oracle_summary,
    compute_metrics_by_problem_type,
    compute_paired_method_comparison,
    compute_pass_at_k,
    compute_selected_method_metrics,
    compute_selection_collapse_summary,
    compute_selection_diagnostics,
    write_csv,
    write_markdown,
)
from replenishverifier.utils.io import read_jsonl


def parse_k_values(text):
    return [int(part.strip()) for part in str(text).split(",") if part.strip()]


def _select_columns(rows, columns):
    return [{column: row.get(column) for column in columns} for row in rows]


def _write_table(out_dir, name, title, rows):
    write_csv(out_dir / f"{name}.csv", rows)
    write_markdown(out_dir / f"{name}.md", rows, title)


def build_paper_metrics(exp_dir, out_dir, k_values, bootstrap_samples=1000, seed=42):
    exp_dir = Path(exp_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    main_rows = read_jsonl(exp_dir / "main_results.jsonl")
    candidate_path = exp_dir / "candidate_evaluations.jsonl"
    candidate_rows = read_jsonl(candidate_path) if candidate_path.exists() else []

    metrics = compute_selected_method_metrics(main_rows)
    metrics_with_ci = add_bootstrap_ci(metrics, main_rows, samples=bootstrap_samples, seed=seed)
    errors = compute_error_type_summary(main_rows)
    pass_at_k = compute_pass_at_k(candidate_rows, k_values) if candidate_rows else []
    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows) if candidate_rows else {
        "same_selection_rate": [],
        "candidate_rank_distribution": [],
        "selection_score_debug": [],
    }
    missed_oracle = compute_missed_oracle_summary(main_rows, candidate_rows) if candidate_rows else []
    paired_comparison = compute_paired_method_comparison(main_rows, target_method="ReplenishVerifier-TypeAware-Consensus")
    by_problem_type = compute_metrics_by_problem_type(main_rows)
    selection_collapse = compute_selection_collapse_summary(main_rows, candidate_rows)
    hard_subset_stress = compute_hard_subset_metrics(main_rows)

    selector_v2_methods = {"ReplenishVerifier-ConsensusSafe", "ReplenishVerifier-HybridSafe", "ReplenishVerifier-FullV2", "ReplenishVerifier-TypeAware-Consensus", "ReplenishVerifier-Full", "Best-of-K"}
    tables = {
        "table_main_metrics": _select_columns(metrics, ["method", "n", "code_validity_rate", "executable_rate", "optimal_rate", "objective_accuracy", "objective_accuracy_count", "objective_accuracy_total", "structure_completeness", "structure_complete_count", "structure_complete_total", "constraint_coverage", "objective_term_coverage"]),
        "table_selector_v2_main": _select_columns([row for row in metrics if row.get("method") in selector_v2_methods], ["method", "n", "objective_accuracy", "structure_completeness", "constraint_coverage", "objective_term_coverage", "average_runtime_sec"]),
        "table_solver_status": _select_columns(metrics, ["method", "n", "solver_status_optimal_rate", "solver_status_infeasible_rate", "solver_status_timeout_rate", "solver_status_error_rate"]),
        "table_objective_gap": _select_columns(metrics, ["method", "n", "objective_accuracy", "mean_relative_error", "median_relative_error", "mean_objective_gap", "median_objective_gap"]),
        "table_structure_metrics": _select_columns(metrics, ["method", "n", "structure_completeness", "inventory_balance_accuracy", "constraint_coverage"]),
        "table_objective_terms": _select_columns(metrics, ["method", "n", "objective_term_surface_coverage", "objective_term_lp_coefficient_coverage", "objective_term_coverage"]),
        "table_pass_at_k_oracle": pass_at_k,
        "table_selection_diagnostics": diagnostics["candidate_rank_distribution"],
        "table_missed_oracle_summary": missed_oracle,
        "table_paired_method_comparison": paired_comparison,
        "table_error_taxonomy": errors,
        "table_runtime_cost": _select_columns(metrics, ["method", "n", "average_runtime_sec", "median_runtime_sec", "average_repair_feedback_count"]),
        "table_bootstrap_ci": metrics_with_ci,
        "table_by_problem_type": by_problem_type,
        "table_selection_collapse": selection_collapse,
        "table_hard_subset_stress": hard_subset_stress,
    }

    titles = {
        "table_main_metrics": "Table: Main Paper Metrics",
        "table_selector_v2_main": "Table: Selector V2 Main Metrics",
        "table_solver_status": "Table: Solver Status Metrics",
        "table_objective_gap": "Table: Objective Accuracy and Gap",
        "table_structure_metrics": "Table: Structure Metrics",
        "table_objective_terms": "Table: Objective Term Coverage",
        "table_pass_at_k_oracle": "Table: Pass@K and Oracle Upper Bounds",
        "table_selection_diagnostics": "Table: Selection Diagnostics",
        "table_missed_oracle_summary": "Table: Missed Oracle Summary",
        "table_paired_method_comparison": "Table: Paired Method Comparison",
        "table_error_taxonomy": "Table: Error Taxonomy",
        "table_runtime_cost": "Table: Runtime and Repair Feedback Cost",
        "table_bootstrap_ci": "Table: Bootstrap Confidence Intervals",
        "table_by_problem_type": "Table: Metrics by Problem Type",
        "table_selection_collapse": "Table: Selection Collapse Diagnostics",
        "table_hard_subset_stress": "Table: Hard Subset / Stress Test Metrics",
    }
    for name, rows in tables.items():
        _write_table(out_dir, name, titles[name], rows)
    return {"exp_dir": str(exp_dir), "out_dir": str(out_dir), "tables": list(tables)}


def main():
    parser = argparse.ArgumentParser(description="Build paper-grade metric tables from an existing experiment directory.")
    parser.add_argument("--exp_dir", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--k_values", default="1,2,4")
    parser.add_argument("--bootstrap_samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    build_paper_metrics(args.exp_dir, args.out_dir, parse_k_values(args.k_values), bootstrap_samples=args.bootstrap_samples, seed=args.seed)


if __name__ == "__main__":
    main()
