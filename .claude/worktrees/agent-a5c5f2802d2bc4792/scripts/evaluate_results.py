import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from replenishverifier.utils.io import read_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--selected-only", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.results)
    if args.selected_only:
        rows = [row for row in rows if row.get("selected")]

    if not rows:
        print("No rows.")
        return

    executable = []
    feasible = []
    obj_scores = []
    struct_scores = []
    total_scores = []
    coverage = defaultdict(list)

    for row in rows:
        execution = row.get("execution")
        if execution is not None:
            executable.append(1.0 if execution.get("executable") else 0.0)
            feasible.append(1.0 if execution.get("status") in {"Optimal", "Feasible"} else 0.0)

        if "objective_score" in row:
            obj_scores.append(row["objective_score"])
        if "structure_score" in row:
            struct_scores.append(row["structure_score"])
        elif "structure_verification" in row and row["structure_verification"]:
            struct_scores.append(row["structure_verification"].get("structure_score", 0.0))

        if "score" in row:
            total_scores.append(row["score"])

        structure_verification = row.get("structure_verification")
        if structure_verification:
            expected = structure_verification.get("expected", {})
            detected = structure_verification.get("detected", {})
            for key, needed in expected.items():
                if needed:
                    coverage[key].append(1.0 if detected.get(key) else 0.0)

    print("==== Evaluation ====")
    print(f"rows: {len(rows)}")
    if executable:
        print(f"executable_rate: {np.mean(executable):.4f}")
    if feasible:
        print(f"feasible_or_optimal_rate: {np.mean(feasible):.4f}")
    if obj_scores:
        print(f"objective_score: {np.mean(obj_scores):.4f}")
    if struct_scores:
        print(f"structure_completeness: {np.mean(struct_scores):.4f}")
    if total_scores:
        print(f"total_score: {np.mean(total_scores):.4f}")

    if coverage:
        print("\n---- Per-structure coverage ----")
        for key in sorted(coverage):
            print(f"{key}: {np.mean(coverage[key]):.4f}  n={len(coverage[key])}")

    if any("problem_type" in row for row in rows):
        counter = Counter(row.get("problem_type", "unknown") for row in rows)
        print("\n---- Problem type count ----")
        for key, value in counter.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
