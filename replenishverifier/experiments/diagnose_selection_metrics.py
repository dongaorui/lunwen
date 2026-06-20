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


def _selection_components(row):
    return row.get("selection_components") or {}


def _component(row, key):
    return _selection_components(row).get(key)


def compute_selector_counterfactuals(main_rows, target_methods=None, baseline_method="Best-of-K"):
    target_methods = target_methods or ["ReplenishVerifier-HybridSafe", "ReplenishVerifier-ConsensusSafe", "ReplenishVerifier-TypeAware-Consensus"]
    selected = _selected_by_method_problem(main_rows)
    baseline = selected.get(baseline_method, {})
    rows = []
    for target_method in target_methods:
        target = selected.get(target_method, {})
        for pid in sorted(set(target) & set(baseline)):
            t = target[pid]
            b = baseline[pid]
            if t.get("candidate_id") == b.get("candidate_id"):
                continue
            tc = _selection_components(t)
            bc = _selection_components(b)
            t_correct = 1.0 if _local_objective_correct(t) else 0.0
            b_correct = 1.0 if _local_objective_correct(b) else 0.0
            rows.append({
                "target_method": target_method,
                "baseline_method": baseline_method,
                "problem_id": pid,
                "target_candidate_id": t.get("candidate_id"),
                "baseline_candidate_id": b.get("candidate_id"),
                "target_objective_correct_posthoc_only": t_correct,
                "baseline_objective_correct_posthoc_only": b_correct,
                "objective_delta_posthoc_only": t_correct - b_correct,
                "target_selector_family": tc.get("selector_family"),
                "target_method_vote_count": tc.get("method_vote_count"),
                "target_consensus_score": tc.get("consensus_score"),
                "baseline_consensus_score": bc.get("consensus_score"),
                "target_critical_missing_count": tc.get("critical_missing_count"),
                "baseline_critical_missing_count": bc.get("critical_missing_count"),
                "target_structure": tc.get("structure_completeness"),
                "baseline_structure": bc.get("structure_completeness"),
                "target_constraint_coverage": tc.get("constraint_coverage"),
                "baseline_constraint_coverage": bc.get("constraint_coverage"),
                "posthoc_only": True,
            })
    return rows


def build_selector_failure_summary(counterfactual_rows):
    lines = [
        "# Selector Failure Summary",
        "",
        "This report is posthoc_only diagnostics and must not be used for formal selection.",
        "",
    ]
    if not counterfactual_rows:
        lines.append("No selector counterfactual failures were found.")
        return "\n".join(lines) + "\n"
    buckets = {
        "objective consensus misled": 0,
        "structure misled": 0,
        "critical penalty misled": 0,
        "selector votes misled": 0,
        "non-reference signals could not distinguish": 0,
    }
    for row in counterfactual_rows:
        if float(row.get("objective_delta_posthoc_only") or 0.0) >= 0.0:
            continue
        if (row.get("target_consensus_score") or 0.0) > (row.get("baseline_consensus_score") or 0.0):
            buckets["objective consensus misled"] += 1
        elif (row.get("target_structure") or 0.0) > (row.get("baseline_structure") or 0.0):
            buckets["structure misled"] += 1
        elif (row.get("target_critical_missing_count") or 0.0) < (row.get("baseline_critical_missing_count") or 0.0):
            buckets["critical penalty misled"] += 1
        elif (row.get("target_method_vote_count") or 0.0) > 0.0:
            buckets["selector votes misled"] += 1
        else:
            buckets["non-reference signals could not distinguish"] += 1
    lines.extend(["| failure_mode | count |", "| --- | --- |"])
    for key, value in buckets.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    return "\n".join(lines)


def _write_selector_counterfactuals_markdown(path, rows):
    write_markdown(path, rows, "Selector Counterfactuals")
    text = Path(path).read_text(encoding="utf-8")
    Path(path).write_text(text + "\nThis table is posthoc_only diagnostics and must not be used for formal selection.\n", encoding="utf-8")



def compute_consensus_safe_counterfactual(main_rows):
    """Post-hoc Best-of-K vs ConsensusSafe diagnostic rows.

    This explains where ConsensusSafe differs from Best-of-K using selected-row
    evaluation labels only in the diagnostic output. It is not a selection input.
    """
    selected = _selected_by_method_problem(main_rows)
    best_rows = selected.get("Best-of-K", {})
    safe_rows = selected.get("ReplenishVerifier-ConsensusSafe", {})
    result = []
    for pid in sorted(set(best_rows) & set(safe_rows)):
        best = best_rows[pid]
        safe = safe_rows[pid]
        if best.get("candidate_id") == safe.get("candidate_id"):
            continue
        safe_correct = 1.0 if _local_objective_correct(safe) else 0.0
        best_correct = 1.0 if _local_objective_correct(best) else 0.0
        result.append({
            "problem_id": pid,
            "consensus_safe_candidate_id": safe.get("candidate_id"),
            "best_of_k_candidate_id": best.get("candidate_id"),
            "consensus_safe_objective_correct_posthoc": safe_correct,
            "best_of_k_objective_correct_posthoc": best_correct,
            "objective_delta_vs_best_of_k": safe_correct - best_correct,
            "consensus_safe_consensus": _component(safe, "consensus_score"),
            "best_of_k_consensus": _component(best, "consensus_score"),
            "consensus_safe_lp_health": _component(safe, "lp_health_score"),
            "best_of_k_lp_health": _component(best, "lp_health_score"),
            "consensus_safe_critical_missing": _component(safe, "critical_missing_count"),
            "best_of_k_critical_missing": _component(best, "critical_missing_count"),
            "consensus_safe_constraint_coverage": _component(safe, "constraint_coverage"),
            "best_of_k_constraint_coverage": _component(best, "constraint_coverage"),
            "consensus_safe_objective_term_coverage": _component(safe, "objective_term_coverage"),
            "best_of_k_objective_term_coverage": _component(best, "objective_term_coverage"),
            "consensus_safe_structure": _component(safe, "structure_completeness"),
            "best_of_k_structure": _component(best, "structure_completeness"),
            "diagnostic_note": "post-hoc diagnostics only; non-reference signal columns explain the selected candidate difference",
        })
    return result


def _write_consensus_safe_counterfactual_markdown(path, rows):
    header = "This is post-hoc diagnostics only and must not be used for formal selection."
    if not rows:
        Path(path).write_text(f"# ConsensusSafe Counterfactual Diagnostics\n\n{header}\n\nNo differing ConsensusSafe / Best-of-K selections.\n", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    lines = ["# ConsensusSafe Counterfactual Diagnostics", "", header, "", "| " + " | ".join(keys) + " |", "| " + " | ".join(["---"] * len(keys)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key)) for key in keys) + " |")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _rank_from_candidate_id(candidate_id):
    try:
        from replenishverifier.experiments.paper_metrics import parse_candidate_rank
        return parse_candidate_rank(candidate_id)
    except Exception:
        return None


def _selected_method_row(selected, method, pid):
    return selected.get(method, {}).get(pid)


def _diag_value(row, key, component_key=None):
    if row is None:
        return None
    if key in row:
        return row.get(key)
    components = row.get("selection_components") or {}
    return components.get(component_key or key)


def _diagnostic_reason(full, struct, best):
    if not full or not struct:
        return "only_reference_can_distinguish_posthoc"
    same = full.get("candidate_id") == struct.get("candidate_id")
    full_correct = _local_objective_correct(full)
    struct_correct = _local_objective_correct(struct)
    best_correct = _local_objective_correct(best) if best else False
    if same and abs(float(_diag_value(full, "structure_score") or 0.0) - float(_diag_value(struct, "structure_score") or 0.0)) <= 1e-12:
        return "same_candidate_due_to_structure_dominance"
    if same:
        return "same_candidate_due_to_identical_score_tuple"
    if best_correct and not full_correct:
        return "bestofk_selected_different_correct_candidate"
    if struct_correct and not full_correct:
        return "full_selected_wrong_objective"
    if full_correct and not struct_correct:
        return "structure_selected_wrong_objective"
    if (_diag_value(full, "objective_consensus_score") or 0.0) != (_diag_value(struct, "objective_consensus_score") or 0.0):
        return "objective_consensus_disagrees_with_structure"
    if (_diag_value(full, "objective_term_coverage") or 0.0) != (_diag_value(struct, "objective_term_coverage") or 0.0):
        return "objective_terms_disagree_with_structure"
    if (full.get("selection_components") or {}).get("critical_structure_penalty") != (struct.get("selection_components") or {}).get("critical_structure_penalty"):
        return "critical_structure_disagrees_with_structure"
    return "only_reference_can_distinguish_posthoc"


def compute_full_vs_structure_diagnosis(main_rows):
    selected = _selected_by_method_problem(main_rows)
    pids = sorted(set(selected.get("ReplenishVerifier-Full", {})) | set(selected.get("Structure only", {})))
    rows = []
    for pid in pids:
        full = _selected_method_row(selected, "ReplenishVerifier-Full", pid)
        struct = _selected_method_row(selected, "Structure only", pid)
        best = _selected_method_row(selected, "Best-of-K", pid)
        rows.append({
            "problem_id": pid,
            "problem_type": (full or struct or {}).get("problem_type"),
            "full_candidate_id": (full or {}).get("candidate_id"),
            "full_candidate_rank": _rank_from_candidate_id((full or {}).get("candidate_id")),
            "structure_candidate_id": (struct or {}).get("candidate_id"),
            "structure_candidate_rank": _rank_from_candidate_id((struct or {}).get("candidate_id")),
            "same_candidate": bool(full and struct and full.get("candidate_id") == struct.get("candidate_id")),
            "full_objective_correct_posthoc": (full or {}).get("objective_correct"),
            "structure_objective_correct_posthoc": (struct or {}).get("objective_correct"),
            "full_objective_value": ((full or {}).get("execution") or {}).get("objective"),
            "structure_objective_value": ((struct or {}).get("execution") or {}).get("objective"),
            "full_structure_score": _diag_value(full, "structure_score"),
            "structure_structure_score": _diag_value(struct, "structure_score"),
            "full_constraint_coverage": _diag_value(full, "constraint_coverage"),
            "structure_constraint_coverage": _diag_value(struct, "constraint_coverage"),
            "full_objective_consensus_score": _diag_value(full, "objective_consensus_score"),
            "structure_objective_consensus_score": _diag_value(struct, "objective_consensus_score"),
            "full_objective_cluster_size": _diag_value(full, "objective_cluster_size"),
            "structure_objective_cluster_size": _diag_value(struct, "objective_cluster_size"),
            "full_objective_term_coverage": _diag_value(full, "objective_term_coverage"),
            "structure_objective_term_coverage": _diag_value(struct, "objective_term_coverage"),
            "full_objective_term_lp_coefficient_coverage": _diag_value(full, "objective_term_lp_coefficient_coverage"),
            "structure_objective_term_lp_coefficient_coverage": _diag_value(struct, "objective_term_lp_coefficient_coverage"),
            "full_static_validation_score": _diag_value(full, "static_validation_score"),
            "structure_static_validation_score": _diag_value(struct, "static_validation_score"),
            "full_type_aware_score": _diag_value(full, "type_aware_score"),
            "structure_type_aware_score": _diag_value(struct, "type_aware_score"),
            "full_solver_status": ((full or {}).get("execution") or {}).get("status"),
            "structure_solver_status": ((struct or {}).get("execution") or {}).get("status"),
            "full_runtime": (full or {}).get("runtime_sec"),
            "structure_runtime": (struct or {}).get("runtime_sec"),
            "diagnostic_reason": _diagnostic_reason(full, struct, best),
        })
    return rows


def build_full_structure_overlap_summary(rows, main_rows):
    selected = _selected_by_method_problem(main_rows)
    lines = ["# Full vs Structure Overlap Summary", "", "Posthoc-only diagnostics; do not use for formal selection.", ""]
    same = sum(1 for row in rows if row.get("same_candidate"))
    full_beats = sum(1 for row in rows if row.get("full_objective_correct_posthoc") == 1.0 and row.get("structure_objective_correct_posthoc") != 1.0)
    structure_beats = sum(1 for row in rows if row.get("structure_objective_correct_posthoc") == 1.0 and row.get("full_objective_correct_posthoc") != 1.0)
    both_correct = sum(1 for row in rows if row.get("full_objective_correct_posthoc") == 1.0 and row.get("structure_objective_correct_posthoc") == 1.0)
    both_wrong = sum(1 for row in rows if row.get("full_objective_correct_posthoc") != 1.0 and row.get("structure_objective_correct_posthoc") != 1.0)
    best = selected.get("Best-of-K", {})
    full = selected.get("ReplenishVerifier-Full", {})
    struct = selected.get("Structure only", {})
    best_full = sum(1 for pid, row in best.items() if _local_objective_correct(row) and pid in full and not _local_objective_correct(full[pid]))
    best_struct = sum(1 for pid, row in best.items() if _local_objective_correct(row) and pid in struct and not _local_objective_correct(struct[pid]))
    for label, value in [
        ("Full vs Structure same candidate count", same),
        ("Full beats Structure count", full_beats),
        ("Structure beats Full count", structure_beats),
        ("Both correct count", both_correct),
        ("Both wrong count", both_wrong),
        ("Best-of-K correct while Full wrong count", best_full),
        ("Best-of-K correct while Structure wrong count", best_struct),
    ]:
        lines.append(f"- {label}: {value}")
    lines.append("")
    return "\n".join(lines)


def _candidate_selected_flags(row, selected):
    pid = row.get("problem_id")
    cid = row.get("candidate_id")
    return {
        "selected_by_full": cid == (selected.get("ReplenishVerifier-Full", {}).get(pid) or {}).get("candidate_id"),
        "selected_by_structure_only": cid == (selected.get("Structure only", {}).get(pid) or {}).get("candidate_id"),
        "selected_by_fullv2": cid == (selected.get("ReplenishVerifier-FullV2", {}).get(pid) or {}).get("candidate_id"),
        "selected_by_bestofk": cid == (selected.get("Best-of-K", {}).get(pid) or {}).get("candidate_id"),
    }


def compute_objective_consensus_cluster_debug(candidate_rows, main_rows):
    selected = _selected_by_method_problem(main_rows)
    rows = []
    for row in candidate_rows:
        out = {
            "problem_id": row.get("problem_id"),
            "candidate_id": row.get("candidate_id"),
            "candidate_rank": _rank_from_candidate_id(row.get("candidate_id")),
            "solver_ok": bool((row.get("execution") or {}).get("executable") and (row.get("execution") or {}).get("status") == "Optimal"),
            "objective_value": (row.get("execution") or {}).get("objective"),
            "objective_cluster_id": row.get("objective_cluster_id"),
            "objective_cluster_size": row.get("objective_cluster_size"),
            "objective_consensus_score": row.get("objective_consensus_score"),
            "objective_density_score": row.get("objective_density_score"),
            "objective_cluster_median": row.get("objective_cluster_median"),
            "distance_to_cluster_median": row.get("distance_to_cluster_median"),
        }
        out.update(_candidate_selected_flags(row, selected))
        rows.append(out)
    return rows


def compute_fullv2_debug_rows(candidate_rows, main_rows):
    selected = _selected_by_method_problem(main_rows)
    rows = []
    from replenishverifier.experiments.methods import fullv2_selection_components
    for row in candidate_rows:
        components = row.get("selection_components") or fullv2_selection_components(row)
        out = {
            "problem_id": row.get("problem_id"),
            "problem_type": row.get("problem_type"),
            "candidate_id": row.get("candidate_id"),
            "candidate_rank": _rank_from_candidate_id(row.get("candidate_id")),
            "solver_ok": components.get("solver_ok"),
            "has_objective": components.get("has_objective"),
            "objective_value": (row.get("execution") or {}).get("objective"),
            "objective_consensus_score": row.get("objective_consensus_score"),
            "objective_cluster_size": row.get("objective_cluster_size"),
            "objective_density_score": row.get("objective_density_score"),
            "distance_to_cluster_median": row.get("distance_to_cluster_median"),
            "objective_term_coverage": row.get("objective_term_coverage"),
            "objective_term_lp_coefficient_coverage": row.get("objective_term_lp_coefficient_coverage"),
            "critical_structure_penalty": components.get("critical_structure_penalty"),
            "missing_critical_structures": ";".join(components.get("missing_critical_structures") or []),
            "type_aware_hard_gate_score": components.get("type_aware_hard_gate_score"),
            "type_aware_missing_critical_count": components.get("type_aware_missing_critical_count"),
            "structure_score": row.get("structure_score"),
            "constraint_coverage": row.get("constraint_coverage"),
            "static_validation_score": row.get("static_validation_score"),
            "code_validity_score": 1.0 if row.get("code_output_format_valid") else 0.0,
            "runtime": row.get("runtime_sec"),
            "full_score_tuple": components.get("score_tuple_debug"),
            "structure_only_score_tuple": "structure_score,constraint_coverage,critical_structure_pass,inventory_balance,candidate_rank",
            "bestofk_score_tuple": "solver,objective,structure,constraint,code,static,runtime,candidate_rank",
            "posthoc_objective_correct": row.get("objective_correct"),
            "posthoc_note": "posthoc_objective_correct is diagnostic-only",
        }
        out.update(_candidate_selected_flags(row, selected))
        rows.append(out)
    return rows


def build_fullv2_vs_structure_summary(main_rows):
    selected = _selected_by_method_problem(main_rows)
    fullv2 = selected.get("ReplenishVerifier-FullV2", {})
    struct = selected.get("Structure only", {})
    full = selected.get("ReplenishVerifier-Full", {})
    best = selected.get("Best-of-K", {})
    common = sorted(set(fullv2) & set(struct))
    same = sum(1 for pid in common if fullv2[pid].get("candidate_id") == struct[pid].get("candidate_id"))
    def acc(rows):
        return sum(1 for row in rows.values() if _local_objective_correct(row)) / max(len(rows), 1)
    fullv2_beats = sum(1 for pid in common if _local_objective_correct(fullv2[pid]) and not _local_objective_correct(struct[pid]))
    struct_beats = sum(1 for pid in common if _local_objective_correct(struct[pid]) and not _local_objective_correct(fullv2[pid]))
    both_correct = sum(1 for pid in common if _local_objective_correct(fullv2[pid]) and _local_objective_correct(struct[pid]))
    both_wrong = sum(1 for pid in common if not _local_objective_correct(fullv2[pid]) and not _local_objective_correct(struct[pid]))
    best_wrong = sum(1 for pid, row in best.items() if _local_objective_correct(row) and pid in fullv2 and not _local_objective_correct(fullv2[pid]))
    fullv2_best = sum(1 for pid, row in fullv2.items() if _local_objective_correct(row) and pid in best and not _local_objective_correct(best[pid]))
    lines = ["# FullV2 vs Structure Summary", "", "Posthoc-only diagnostics; do not use for formal selection.", ""]
    values = [
        ("Full vs Structure same_selection_rate", sum(1 for pid in set(full) & set(struct) if full[pid].get("candidate_id") == struct[pid].get("candidate_id")) / max(len(set(full) & set(struct)), 1)),
        ("FullV2 vs Structure same_selection_rate", same / max(len(common), 1)),
        ("FullV2 vs Full same_selection_rate", sum(1 for pid in set(fullv2) & set(full) if fullv2[pid].get("candidate_id") == full[pid].get("candidate_id")) / max(len(set(fullv2) & set(full)), 1)),
        ("FullV2 vs Best-of-K same_selection_rate", sum(1 for pid in set(fullv2) & set(best) if fullv2[pid].get("candidate_id") == best[pid].get("candidate_id")) / max(len(set(fullv2) & set(best)), 1)),
        ("Full objective_accuracy", acc(full)),
        ("Structure objective_accuracy", acc(struct)),
        ("FullV2 objective_accuracy", acc(fullv2)),
        ("Best-of-K objective_accuracy", acc(best)),
        ("FullV2 beats Structure count", fullv2_beats),
        ("Structure beats FullV2 count", struct_beats),
        ("Both correct count", both_correct),
        ("Both wrong count", both_wrong),
        ("FullV2 wrong but Best-of-K correct count", best_wrong),
        ("FullV2 correct but Best-of-K wrong count", fullv2_best),
    ]
    for label, value in values:
        lines.append(f"- {label}: {value:.4f}" if isinstance(value, float) else f"- {label}: {value}")
    lines.extend(["", "## Failure modes", "", "- only_reference_can_distinguish_posthoc: reported when non-reference signals are tied or inconclusive.", "- objective_consensus_misled_selection: inspect fullv2_score_debug.csv objective columns.", "- critical_structure_penalty_too_strong: inspect fullv2_critical_structure_debug.csv.", "- objective_terms_not_discriminative: inspect objective-term coverage columns.", "- candidate_pool_limited: compare against pass@k oracle table.", ""])
    return "\n".join(lines)


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
    consensus_safe_counterfactual = compute_consensus_safe_counterfactual(main_rows)
    selector_counterfactuals = compute_selector_counterfactuals(main_rows)
    selector_failure_summary = build_selector_failure_summary(selector_counterfactuals)
    full_vs_structure_diagnosis = compute_full_vs_structure_diagnosis(main_rows)
    full_structure_overlap_summary = build_full_structure_overlap_summary(full_vs_structure_diagnosis, main_rows)
    objective_consensus_clusters = compute_objective_consensus_cluster_debug(candidate_rows, main_rows) if candidate_rows else []
    fullv2_score_debug = compute_fullv2_debug_rows(candidate_rows, main_rows) if candidate_rows else []
    fullv2_critical_structure_debug = [
        {
            "problem_id": row.get("problem_id"),
            "problem_type": row.get("problem_type"),
            "candidate_id": row.get("candidate_id"),
            "candidate_rank": row.get("candidate_rank"),
            "missing_critical_structures": row.get("missing_critical_structures"),
            "critical_structure_count": row.get("type_aware_missing_critical_count"),
            "critical_structure_penalty": row.get("critical_structure_penalty"),
            "structure_score": row.get("structure_score"),
            "constraint_coverage": row.get("constraint_coverage"),
            "objective_term_coverage": row.get("objective_term_coverage"),
            "selected_by_fullv2": row.get("selected_by_fullv2"),
            "selected_by_structure_only": row.get("selected_by_structure_only"),
        }
        for row in fullv2_score_debug
    ]
    fullv2_vs_structure_summary = build_fullv2_vs_structure_summary(main_rows)
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
    write_csv(out_dir / "consensus_safe_counterfactual.csv", consensus_safe_counterfactual)
    _write_consensus_safe_counterfactual_markdown(out_dir / "consensus_safe_counterfactual.md", consensus_safe_counterfactual)
    write_csv(out_dir / "selector_counterfactuals.csv", selector_counterfactuals)
    _write_selector_counterfactuals_markdown(out_dir / "selector_counterfactuals.md", selector_counterfactuals)
    (out_dir / "selector_failure_summary.md").write_text(selector_failure_summary, encoding="utf-8")
    write_csv(out_dir / "full_vs_structure_diagnosis.csv", full_vs_structure_diagnosis)
    (out_dir / "full_structure_overlap_summary.md").write_text(full_structure_overlap_summary, encoding="utf-8")
    write_csv(out_dir / "objective_consensus_clusters.csv", objective_consensus_clusters)
    write_csv(out_dir / "fullv2_score_debug.csv", fullv2_score_debug)
    write_csv(out_dir / "fullv2_critical_structure_debug.csv", fullv2_critical_structure_debug)
    (out_dir / "fullv2_vs_structure_summary.md").write_text(fullv2_vs_structure_summary, encoding="utf-8")
    (out_dir / "fullv2_failure_summary.md").write_text(fullv2_vs_structure_summary, encoding="utf-8")
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
        "consensus_safe_counterfactual": consensus_safe_counterfactual,
        "selector_counterfactuals": selector_counterfactuals,
        "selector_failure_summary": selector_failure_summary,
        "full_vs_structure_diagnosis": full_vs_structure_diagnosis,
        "objective_consensus_clusters": objective_consensus_clusters,
        "fullv2_score_debug": fullv2_score_debug,
        "fullv2_critical_structure_debug": fullv2_critical_structure_debug,
        "fullv2_vs_structure_summary": fullv2_vs_structure_summary,
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
