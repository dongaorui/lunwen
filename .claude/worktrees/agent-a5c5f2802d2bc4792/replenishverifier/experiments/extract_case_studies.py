import argparse
import csv
from pathlib import Path

from replenishverifier.experiments.evaluation import save_markdown_table
from replenishverifier.utils.io import read_jsonl, write_jsonl


BASELINE_METHODS = [
    "Solver-Filter",
    "OR-R1-like Voting",
    "OR-R1-like Voting",
    "SIRL-like LP-Stats",
    "OptArgus-like Audit",
    "OptiRepair-like Repair-Prompt",
]


STRONG_BASELINE_METHODS = [
    "SIRL-like LP-Stats",
    "OptArgus-like Audit",
    "OptiRepair-like Repair-Prompt",
]


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def short_feedback(row):
    text = row.get("feedback") or row.get("generic_repair_feedback") or ""
    return text[:800]


def _case_from_pair(pid, full, base, why_interesting):
    return {
        "problem_id": pid,
        "problem_type": full.get("problem_type"),
        "difficulty": full.get("difficulty"),
        "baseline_method": base.get("method_name"),
        "baseline_candidate": base.get("candidate_id"),
        "baseline_selection_policy": base.get("selection_policy"),
        "baseline_structure_score": base.get("structure_score"),
        "baseline_objective_correct": base.get("objective_correct"),
        "baseline_missing_structures": (base.get("structure_verification") or {}).get("missing"),
        "baseline_feedback": short_feedback(base),
        "full_candidate": full.get("candidate_id"),
        "full_structure_score": full.get("structure_score"),
        "full_objective_correct": full.get("objective_correct"),
        "why_interesting": why_interesting,
    }


def extract_case_studies(exp_dir, max_cases=20):
    exp_dir = Path(exp_dir)
    rows = [row for row in read_jsonl(exp_dir / "main_results.jsonl") if row.get("selected")]
    by_problem_method = {(row.get("problem_id"), row.get("method_name")): row for row in rows}
    problem_ids = sorted({row.get("problem_id") for row in rows})

    cases = []
    strong_cases = []
    solver_filter_cases = []
    for pid in problem_ids:
        full = by_problem_method.get((pid, "ReplenishVerifier-Full"))
        if not full:
            continue
        full_ok = (full.get("structure_score", 0.0) >= 0.999) and bool(full.get("execution", {}).get("executable"))
        if not full_ok:
            continue

        for method in STRONG_BASELINE_METHODS:
            base = by_problem_method.get((pid, method))
            if not base:
                continue
            base_bad = base.get("structure_score", 0.0) < 0.999 or not base.get("execution", {}).get("executable")
            if base_bad:
                strong_cases.append(_case_from_pair(
                    pid,
                    full,
                    base,
                    "Strong baseline selected a candidate with missing replenishment structures, while ReplenishVerifier-Full selected a structurally complete candidate.",
                ))

        solver_filter = by_problem_method.get((pid, "Solver-Filter"))
        if solver_filter:
            base_bad = solver_filter.get("structure_score", 0.0) < 0.999 or not solver_filter.get("execution", {}).get("executable")
            if base_bad:
                solver_filter_cases.append(_case_from_pair(
                    pid,
                    full,
                    solver_filter,
                    "Solver-only baseline selected a candidate with missing replenishment structures, while ReplenishVerifier-Full selected a structurally complete candidate.",
                ))

    seen = set()
    for case in strong_cases + solver_filter_cases:
        key = (case["problem_id"], case["baseline_method"])
        if key in seen:
            continue
        cases.append(case)
        seen.add(key)
        if len(cases) >= max_cases:
            break

    write_jsonl(exp_dir / "case_studies.jsonl", cases)
    write_csv(exp_dir / "case_studies.csv", cases)
    save_markdown_table(exp_dir / "case_studies.md", cases, title="Case Studies")
    return cases


def main():
    parser = argparse.ArgumentParser(description="Extract case studies where ReplenishVerifier improves over generic baselines.")
    parser.add_argument("--exp_dir", required=True)
    parser.add_argument("--max_cases", type=int, default=20)
    args = parser.parse_args()
    cases = extract_case_studies(args.exp_dir, max_cases=args.max_cases)
    print(f"Wrote {len(cases)} case studies to {args.exp_dir}")


if __name__ == "__main__":
    main()
