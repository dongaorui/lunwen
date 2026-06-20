import argparse
import csv
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


def _metric_signature(row):
    ignored = {"method", "n"}
    return tuple(sorted((key, row.get(key)) for key in row if key not in ignored))


def _group_by_signature(rows, signature_fn):
    groups = {}
    for row in rows:
        groups.setdefault(signature_fn(row), []).append(row.get("method"))
    return [sorted(methods) for methods in groups.values() if len(methods) > 1]


def build_method_redundancy_report(metric_rows, same_selection_rows, threshold=0.95):
    high_overlap = [
        row for row in same_selection_rows
        if row.get("same_selection_rate") is not None and float(row.get("same_selection_rate")) >= threshold
    ]
    identical_metric_groups = _group_by_signature(metric_rows, _metric_signature)
    objective_groups = _group_by_signature(metric_rows, lambda row: ("objective_accuracy", row.get("objective_accuracy")))
    objective_only_groups = [group for group in objective_groups if len(group) > 1]
    lines = [
        "# Method Redundancy Report",
        "",
        "This report is diagnostic only and does not affect formal selection.",
        "",
        f"## Method pairs with same_selection_rate >= {threshold:.2f}",
        "",
    ]
    if high_overlap:
        lines.extend(["| method_a | method_b | n_common | same_count | same_selection_rate |", "| --- | --- | --- | --- | --- |"])
        for row in high_overlap:
            lines.append(
                f"| {row.get('method_a')} | {row.get('method_b')} | {row.get('n_common')} | "
                f"{row.get('same_count')} | {float(row.get('same_selection_rate')):.4f} |"
            )
    else:
        lines.append("No method pairs reached the threshold.")
    lines.extend(["", "## Metrics-identical method groups", ""])
    if identical_metric_groups:
        for group in identical_metric_groups:
            lines.append("- " + ", ".join(group))
    else:
        lines.append("No metrics-identical groups found.")
    lines.extend(["", "## Same objective_accuracy but different selection groups", ""])
    if objective_only_groups:
        for group in objective_only_groups:
            lines.append("- " + ", ".join(group))
    else:
        lines.append("No objective_accuracy groups found.")
    lines.extend([
        "",
        "## Recommended display families",
        "",
        "- Solver family: Solver only, Solver-Filter",
        "- Structure family: Structure only, Structure-Only",
        "- Consensus family: Consensus only, OR-R1-like Voting, Solver + Consensus",
        "- Full verifier family: ReplenishVerifier-Full, ReplenishVerifier-Repair, Structure-Grounded Consistency",
        "",
    ])
    return "\n".join(lines)


def build_metric_saturation_report(metric_rows, same_selection_rows, low_unique_threshold=2):
    metric_names = sorted({key for row in metric_rows for key in row if key not in {"method", "n"}})
    lines = [
        "# Metric Saturation Report",
        "",
        "This report is diagnostic only and does not affect formal selection.",
        "",
        "## Metric unique-value counts",
        "",
        "| metric | unique_values | saturated | values |",
        "| --- | --- | --- | --- |",
    ]
    saturated = []
    for metric in metric_names:
        values = sorted({row.get(metric) for row in metric_rows}, key=lambda value: str(value))
        is_saturated = len(values) <= low_unique_threshold
        if is_saturated:
            saturated.append(metric)
        lines.append(f"| {metric} | {len(values)} | {is_saturated} | {values} |")
    lines.extend(["", "## Saturated metrics", ""])
    lines.append(", ".join(saturated) if saturated else "No saturated metrics found.")
    lines.extend([
        "",
        "## High-overlap method pairs",
        "",
        "High same_selection_rate can make headline metrics identical even when method names differ.",
        "",
    ])
    high_overlap = [
        row for row in same_selection_rows
        if row.get("same_selection_rate") is not None and float(row.get("same_selection_rate")) >= 0.95
    ]
    if high_overlap:
        for row in high_overlap:
            lines.append(f"- {row.get('method_a')} / {row.get('method_b')}: same_selection_rate={float(row.get('same_selection_rate')):.4f}")
    else:
        lines.append("No high-overlap pairs found.")
    lines.append("")
    return "\n".join(lines)


def _selected_by_method_problem(rows):
    out = {}
    for row in rows:
        if not row.get("selected", False):
            continue
        out.setdefault(row.get("method_name") or row.get("method"), {})[row.get("problem_id")] = row
    return out


def _local_objective_correct(row):
    try:
        return float(row.get("objective_correct", row.get("objective_accuracy", 0.0)) or 0.0) == 1.0
    except (TypeError, ValueError):
        return False


def _local_missing(row, structure_name):
    return structure_name in set(((row.get("structure_verification") or {}).get("missing") or []))


def compute_avoidable_error_summary(main_rows, candidate_rows, methods=None):
    methods = methods or ["ReplenishVerifier-TypeAware", "ReplenishVerifier-TypeAware-Consensus", "Consensus only"]
    by_problem = {}
    for row in candidate_rows:
        by_problem.setdefault(row.get("problem_id"), []).append(row)
    opportunities = {}
    for pid, rows in by_problem.items():
        opportunities[pid] = {
            "objective_correct_available": any(_local_objective_correct(row) for row in rows),
            "capacity_available": any(not _local_missing(row, "capacity_constraint") for row in rows),
            "optimal_available": any(str((row.get("execution") or {}).get("status") or "") == "Optimal" for row in rows),
            "executable_available": any(bool((row.get("execution") or {}).get("executable")) for row in rows),
        }
    selected = _selected_by_method_problem(main_rows)
    result = []
    for method in methods:
        rows_by_problem = selected.get(method, {})
        counts = {
            "method": method,
            "n_selected": len(rows_by_problem),
            "objective_mismatch_with_objective_correct_available": 0,
            "missing_capacity_with_capacity_available": 0,
            "solver_not_optimal_with_optimal_available": 0,
            "execution_error_with_executable_available": 0,
        }
        for pid, row in rows_by_problem.items():
            opp = opportunities.get(pid, {})
            execution = row.get("execution") or {}
            if opp.get("objective_correct_available") and not _local_objective_correct(row):
                counts["objective_mismatch_with_objective_correct_available"] += 1
            if opp.get("capacity_available") and _local_missing(row, "capacity_constraint"):
                counts["missing_capacity_with_capacity_available"] += 1
            if opp.get("optimal_available") and str(execution.get("status") or "") != "Optimal":
                counts["solver_not_optimal_with_optimal_available"] += 1
            if opp.get("executable_available") and not bool(execution.get("executable")):
                counts["execution_error_with_executable_available"] += 1
        result.append(counts)
    return result


def _write_join_unmatched_csv(path, rows):
    fields = [
        "method",
        "problem_id",
        "candidate_id",
        "parsed_candidate_rank",
        "candidate_rank_parse_reason",
        "reason",
        "matched_candidate_id",
        "selected_file_or_source",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def _write_avoidable_error_markdown(path, rows):
    header = "This is post-hoc diagnostics only and must not be used for formal selection."
    if not rows:
        Path(path).write_text(f"# Avoidable Error Summary\n\n{header}\n\nNo rows.\n", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    lines = ["# Avoidable Error Summary", "", header, "", "| " + " | ".join(keys) + " |", "| " + " | ".join(["---"] * len(keys)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key)) for key in keys) + " |")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    diagnostic_join_unmatched = diagnostics.get("diagnostic_join_unmatched", [])
    missed_oracle_summary = compute_missed_oracle_summary(main_rows, candidate_rows) if candidate_rows else []
    paired_method_comparison = compute_paired_method_comparison(main_rows)
    avoidable_error_summary = compute_avoidable_error_summary(main_rows, candidate_rows) if candidate_rows else []
    method_redundancy_report = build_method_redundancy_report(recomputed_metrics, diagnostics["same_selection_rate"])
    metric_saturation_report = build_metric_saturation_report(recomputed_metrics, diagnostics["same_selection_rate"])

    write_jsonl(out_dir / "metric_comparison.jsonl", metric_comparison)
    write_csv(out_dir / "metric_comparison.csv", metric_comparison)
    write_markdown(out_dir / "metric_comparison.md", metric_comparison, "Metric Comparison")
    write_jsonl(out_dir / "error_type_comparison.jsonl", error_comparison)
    write_csv(out_dir / "error_type_comparison.csv", error_comparison)
    write_markdown(out_dir / "error_type_comparison.md", error_comparison, "Error Type Comparison")
    write_csv(out_dir / "selection_score_debug.csv", diagnostics["selection_score_debug"])
    write_csv(out_dir / "same_selection_rate.csv", diagnostics["same_selection_rate"])
    write_csv(out_dir / "candidate_rank_distribution.csv", diagnostics["candidate_rank_distribution"])
    _write_join_unmatched_csv(out_dir / "diagnostic_join_unmatched.csv", diagnostic_join_unmatched)
    write_csv(out_dir / "missed_oracle_summary.csv", missed_oracle_summary)
    write_markdown(out_dir / "missed_oracle_summary.md", missed_oracle_summary, "Missed Oracle Summary")
    write_csv(out_dir / "paired_method_comparison.csv", paired_method_comparison)
    write_markdown(out_dir / "paired_method_comparison.md", paired_method_comparison, "Paired Method Comparison")
    write_csv(out_dir / "avoidable_error_summary.csv", avoidable_error_summary)
    _write_avoidable_error_markdown(out_dir / "avoidable_error_summary.md", avoidable_error_summary)
    (out_dir / "method_redundancy_report.md").write_text(method_redundancy_report, encoding="utf-8")
    (out_dir / "metric_saturation_report.md").write_text(metric_saturation_report, encoding="utf-8")

    status_counts = {}
    for row in metric_comparison + error_comparison:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    summary = {
        "exp_dir": str(exp_dir),
        "candidates_path": str(candidates_path) if candidates_path else None,
        "benchmark_path": str(benchmark_path) if benchmark_path else None,
        "status_counts": status_counts,
        "unmatched_selected_rows": len(diagnostic_join_unmatched),
        "unmatched_reason_counts": {
            reason: len([row for row in diagnostic_join_unmatched if row.get("reason") == reason])
            for reason in sorted({row.get("reason") for row in diagnostic_join_unmatched})
        },
        "join_note": (
            "All selected rows matched candidate evaluations by problem_id + candidate_id/rank."
            if not diagnostic_join_unmatched
            else "See diagnostic_join_unmatched.csv for selected rows that could not be matched."
        ),
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
        "diagnostic_join_unmatched": diagnostic_join_unmatched,
        "missed_oracle_summary": missed_oracle_summary,
        "paired_method_comparison": paired_method_comparison,
        "avoidable_error_summary": avoidable_error_summary,
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
