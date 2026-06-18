import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from replenishverifier.experiments.baselines import classify_error_type
from replenishverifier.experiments.evaluation import save_markdown_table
from replenishverifier.utils.io import read_jsonl, write_jsonl


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


def analyze_error_types(exp_dir):
    exp_dir = Path(exp_dir)
    rows = read_jsonl(exp_dir / "main_results.jsonl")
    if not rows:
        raise ValueError(f"No main_results.jsonl found in {exp_dir}")

    detailed = []
    grouped = defaultdict(Counter)
    for row in rows:
        if not row.get("selected"):
            continue
        error_type = classify_error_type(row)
        detailed_row = {
            "method": row.get("method_name"),
            "problem_id": row.get("problem_id"),
            "candidate_id": row.get("candidate_id"),
            "problem_type": row.get("problem_type"),
            "difficulty": row.get("difficulty"),
            "error_type": error_type,
            "objective_correct": row.get("objective_correct"),
            "structure_score": row.get("structure_score"),
            "feedback": row.get("feedback"),
        }
        detailed.append(detailed_row)
        grouped[row.get("method_name")][error_type] += 1

    summary = []
    for method, counter in sorted(grouped.items()):
        total = sum(counter.values())
        for error_type, count in sorted(counter.items()):
            summary.append({
                "method": method,
                "error_type": error_type,
                "count": count,
                "rate": count / total if total else 0.0,
                "total": total,
            })

    write_jsonl(exp_dir / "error_type_details.jsonl", detailed)
    write_csv(exp_dir / "error_type_details.csv", detailed)
    save_markdown_table(exp_dir / "error_type_details.md", detailed[:100], title="Error Type Details")

    write_jsonl(exp_dir / "error_type_summary.jsonl", summary)
    write_csv(exp_dir / "error_type_summary.csv", summary)
    save_markdown_table(exp_dir / "error_type_summary.md", summary, title="Error Type Summary")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Analyze selected-candidate error types for ReplenishVerifier experiments.")
    parser.add_argument("--exp_dir", required=True)
    args = parser.parse_args()
    summary = analyze_error_types(args.exp_dir)
    print(f"Wrote error type analysis with {len(summary)} summary rows to {args.exp_dir}")


if __name__ == "__main__":
    main()
