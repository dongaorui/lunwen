import argparse
import csv
import statistics
from pathlib import Path

from replenishverifier.utils.io import read_jsonl, write_jsonl

RUNTIME_FIELDS = [
    "code_execution_time",
    "solver_lp_export_time",
    "solver_time",
    "lp_parse_time",
    "structure_check_time",
    "total_candidate_evaluation_time",
]


def _coerce_number(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _field_value(row, field):
    if field in row:
        return _coerce_number(row.get(field))
    runtime = row.get("runtime") or {}
    return _coerce_number(runtime.get(field))


def _summary(values):
    present = [value for value in values if value is not None]
    missing = len(values) - len(present)
    if not present:
        return {"mean": None, "median": None, "count_present": 0, "count_missing": missing}
    return {
        "mean": float(sum(present) / len(present)),
        "median": float(statistics.median(present)),
        "count_present": len(present),
        "count_missing": missing,
    }


def _format(value):
    if value is None:
        return "NA"
    return f"{value:.6f}"


def _write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = ["problem_id", "candidate_id", *RUNTIME_FIELDS]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _write_markdown(path, report):
    lines = [
        "# Runtime Overhead Report",
        "",
        f"Candidate count: {report['candidate_count']}",
        "",
        "| Metric | Mean seconds | Median seconds | Present | Missing |",
        "|---|---:|---:|---:|---:|",
    ]
    labels = {
        "total_candidate_evaluation_time": "Total candidate evaluation time",
        "lp_parse_time": "LP parse time",
        "structure_check_time": "Structure check time",
        "code_execution_time": "Code execution time",
        "solver_lp_export_time": "Solver LP export time",
        "solver_time": "Solver time",
    }
    for field in ["total_candidate_evaluation_time", "lp_parse_time", "structure_check_time", "code_execution_time", "solver_lp_export_time", "solver_time"]:
        item = report["metrics"][field]
        lines.append(
            f"| {labels[field]} | {_format(item['mean'])} | {_format(item['median'])} | {item['count_present']} | {item['count_missing']} |"
        )
    lines.extend([
        "",
        "Missing or unavailable fields are reported as NA. No runtime values are inferred or fabricated.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_runtime_overhead(exp_dir):
    exp_dir = Path(exp_dir)
    rows = read_jsonl(exp_dir / "candidate_evaluations.jsonl")
    normalized = []
    for row in rows:
        out = {"problem_id": row.get("problem_id"), "candidate_id": row.get("candidate_id")}
        for field in RUNTIME_FIELDS:
            out[field] = _field_value(row, field)
        normalized.append(out)

    metrics = {field: _summary([row[field] for row in normalized]) for field in RUNTIME_FIELDS}
    report = {"exp_dir": str(exp_dir), "candidate_count": len(normalized), "metrics": metrics}

    write_jsonl(exp_dir / "runtime_overhead.jsonl", normalized)
    _write_csv(exp_dir / "runtime_overhead.csv", normalized)
    _write_markdown(exp_dir / "runtime_overhead.md", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Analyze runtime overhead from candidate_evaluations.jsonl.")
    parser.add_argument("--exp_dir", required=True)
    args = parser.parse_args()
    report = analyze_runtime_overhead(args.exp_dir)
    print(f"Wrote runtime overhead report for {report['candidate_count']} candidates to {args.exp_dir}")


if __name__ == "__main__":
    main()
