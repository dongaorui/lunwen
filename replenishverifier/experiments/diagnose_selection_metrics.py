import argparse
import json
from pathlib import Path

from replenishverifier.experiments.paper_metrics import (
    BASE_METRICS,
    compute_error_type_summary,
    compute_missed_oracle_summary,
    compute_paired_method_comparison,
    compute_selected_method_metrics,
    compute_selection_diagnostics,
    write_csv,
    write_markdown,
)
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _coerce_value(text):
    if text is None:
        return None
    value = str(text).strip()
    if value in {"", "N/A", "None"}:
        return None
    try:
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_markdown_table(path):
    if not Path(path).exists():
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    table_lines = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [part.strip() for part in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != len(headers):
            continue
        rows.append({header: _coerce_value(part) for header, part in zip(headers, parts)})
    return rows


def _load_reported_summary(exp_dir):
    candidates = [
        exp_dir / "main_results_summary.jsonl",
        exp_dir / "reported_main_summary.jsonl",
    ]
    for path in candidates:
        if path.exists():
            rows = read_jsonl(path)
            if rows:
                return rows
    for path in [exp_dir / "summary.md", exp_dir / "main_results.md"]:
        rows = _parse_markdown_table(path)
        if rows and "method" in rows[0]:
            return rows
    return []


def _reported_by_method(rows):
    return {row.get("method") or row.get("method_name"): row for row in rows}


def _compare_metrics(recomputed, reported_rows):
    reported = _reported_by_method(reported_rows)
    comparisons = []
    for row in recomputed:
        method = row["method"]
        reported_row = reported.get(method)
        for metric in BASE_METRICS:
            recomputed_value = row.get(metric)
            if not reported_row or metric not in reported_row:
                status = "MISSING"
                reported_value = None
                delta = None
            else:
                reported_value = reported_row.get(metric)
                try:
                    delta = float(recomputed_value) - float(reported_value)
                except (TypeError, ValueError):
                    delta = None
                status = "OK" if delta is not None and abs(delta) <= 1e-4 else "MISMATCH"
            comparisons.append({
                "method": method,
                "metric": metric,
                "reported": reported_value,
                "recomputed": recomputed_value,
                "delta": delta,
                "status": status,
            })
    return comparisons


def _compare_error_types(recomputed, reported_rows):
    reported = {(row.get("method"), row.get("error_type")): row for row in reported_rows}
    comparisons = []
    for row in recomputed:
        key = (row.get("method"), row.get("error_type"))
        report = reported.get(key)
        if report is None:
            status = "MISSING"
            reported_count = None
            delta = None
        else:
            reported_count = report.get("count")
            delta = int(row.get("count", 0)) - int(reported_count)
            status = "OK" if delta == 0 else "MISMATCH"
        comparisons.append({
            "method": row.get("method"),
            "error_type": row.get("error_type"),
            "reported": reported_count,
            "recomputed": row.get("count"),
            "delta": delta,
            "status": status,
        })
    return comparisons


def diagnose_selection_metrics(exp_dir, candidates_path=None, benchmark_path=None, out_dir=None):
    exp_dir = Path(exp_dir)
    out_dir = Path(out_dir) if out_dir else exp_dir / "selection_metric_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    main_rows = read_jsonl(exp_dir / "main_results.jsonl")
    candidate_path = exp_dir / "candidate_evaluations.jsonl"
    candidate_rows = read_jsonl(candidate_path) if candidate_path.exists() else []
    reported_summary = _load_reported_summary(exp_dir)
    recomputed_metrics = compute_selected_method_metrics(main_rows)
    metric_comparison = _compare_metrics(recomputed_metrics, reported_summary)

    recomputed_errors = compute_error_type_summary(main_rows)
    reported_error_path = exp_dir / "error_type_summary.jsonl"
    reported_errors = read_jsonl(reported_error_path) if reported_error_path.exists() else []
    error_comparison = _compare_error_types(recomputed_errors, reported_errors)

    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows)
    missed_oracle_summary = compute_missed_oracle_summary(main_rows, candidate_rows) if candidate_rows else []
    paired_method_comparison = compute_paired_method_comparison(main_rows)

    write_jsonl(out_dir / "metric_comparison.jsonl", metric_comparison)
    write_csv(out_dir / "metric_comparison.csv", metric_comparison)
    write_markdown(out_dir / "metric_comparison.md", metric_comparison, "Metric Comparison")
    write_jsonl(out_dir / "error_type_comparison.jsonl", error_comparison)
    write_csv(out_dir / "error_type_comparison.csv", error_comparison)
    write_markdown(out_dir / "error_type_comparison.md", error_comparison, "Error Type Comparison")
    write_csv(out_dir / "selection_score_debug.csv", diagnostics["selection_score_debug"])
    write_csv(out_dir / "same_selection_rate.csv", diagnostics["same_selection_rate"])
    write_csv(out_dir / "candidate_rank_distribution.csv", diagnostics["candidate_rank_distribution"])
    write_csv(out_dir / "missed_oracle_summary.csv", missed_oracle_summary)
    write_markdown(out_dir / "missed_oracle_summary.md", missed_oracle_summary, "Missed Oracle Summary")
    write_csv(out_dir / "paired_method_comparison.csv", paired_method_comparison)
    write_markdown(out_dir / "paired_method_comparison.md", paired_method_comparison, "Paired Method Comparison")

    status_counts = {}
    for row in metric_comparison + error_comparison:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    summary = {
        "exp_dir": str(exp_dir),
        "candidates_path": str(candidates_path) if candidates_path else None,
        "benchmark_path": str(benchmark_path) if benchmark_path else None,
        "status_counts": status_counts,
        "note": "objective_correct_posthoc appears only in diagnostics and is not a formal selection signal.",
    }
    (out_dir / "diagnostic_summary.md").write_text(
        "# Selection Metric Diagnostics\n\n```json\n"
        + json.dumps(summary, ensure_ascii=False, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    return {
        "metric_comparison": metric_comparison,
        "error_type_comparison": error_comparison,
        "selection_diagnostics": diagnostics,
        "missed_oracle_summary": missed_oracle_summary,
        "paired_method_comparison": paired_method_comparison,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Diagnose method-specific selection and metric aggregation.")
    parser.add_argument("--exp_dir", required=True)
    parser.add_argument("--candidates", default=None)
    parser.add_argument("--benchmark", default=None)
    parser.add_argument("--out_dir", default=None)
    args = parser.parse_args()
    diagnose_selection_metrics(args.exp_dir, candidates_path=args.candidates, benchmark_path=args.benchmark, out_dir=args.out_dir)


if __name__ == "__main__":
    main()
