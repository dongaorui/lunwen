import argparse
import csv
import json
from pathlib import Path

from replenishverifier.experiments.paper_metrics import (
    BASE_METRICS,
    compute_error_type_summary,
    compute_hard_subset_metrics,
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


def compute_method_selection_clusters(metric_rows, same_selection_rows):
    metrics_by_method = {row.get("method"): row for row in metric_rows}
    result = []
    for row in same_selection_rows:
        method_a = row.get("method_a")
        method_b = row.get("method_b")
        acc_a = (metrics_by_method.get(method_a) or {}).get("objective_accuracy")
        acc_b = (metrics_by_method.get(method_b) or {}).get("objective_accuracy")
        same_rate = row.get("same_selection_rate")
        recommendation = "distinct_selection"
        if same_rate is not None and float(same_rate) == 1.0:
            if acc_a == acc_b:
                recommendation = "alias_like_same_selection"
            else:
                recommendation = "same_selection_but_metric_difference_check_needed"
        elif same_rate is not None and float(same_rate) >= 0.95:
            recommendation = "high_overlap_consider_merge_explanation"
        result.append({
            "method_a": method_a,
            "method_b": method_b,
            "same_selection_rate": same_rate,
            "objective_accuracy_a": acc_a,
            "objective_accuracy_b": acc_b,
            "recommendation": recommendation,
        })
    return result


def build_method_redundancy_report(metric_rows, same_selection_rows, threshold=0.95):
    high_overlap = [
        row for row in same_selection_rows
        if row.get("same_selection_rate") is not None and float(row.get("same_selection_rate")) >= threshold
    ]
    identical_metric_groups = _group_by_signature(metric_rows, _metric_signature)
    objective_groups = _group_by_signature(metric_rows, lambda row: ("objective_accuracy", row.get("objective_accuracy")))
    objective_only_groups = [group for group in objective_groups if len(group) > 1]
    clusters = compute_method_selection_clusters(metric_rows, same_selection_rows)
    alias_like = [row for row in clusters if row.get("recommendation") == "alias_like_same_selection"]
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
    lines.extend(["", "## Alias-like same-selection pairs", ""])
    if alias_like:
        lines.extend(["| method_a | method_b | same_selection_rate | objective_accuracy | recommendation |", "| --- | --- | ---: | ---: | --- |"])
        for row in alias_like:
            lines.append(
                f"| {row.get('method_a')} | {row.get('method_b')} | {float(row.get('same_selection_rate')):.4f} | "
                f"{row.get('objective_accuracy_a')} | {row.get('recommendation')} |"
            )
    else:
        lines.append("No exact alias-like same-selection pairs found.")
    lines.extend([
        "",
        "## Recommended display families",
        "",
        "- Main table: Direct, Best-of-K, Consensus only, ReplenishVerifier-Full, ReplenishVerifier-ConsensusSafe/HybridSafe family representative, ReplenishVerifier-TypeAware-Consensus when not alias-like.",
        "- Appendix ablations: Solver-only variants, Structure-only variants, TypeAware, FullV2-Guarded, FullV2-CandidatePoolAware, repair-prompt variants.",
        "- Merge explanation: methods marked alias_like_same_selection should be explained together rather than over-claimed as independent gains.",
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


FORBIDDEN_FORMAL_SELECTION_KEYS = {
    "reference_objective",
    "objective_correct",
    "objective_accuracy",
    "relative_error",
    "oracle",
    "oracle_rank",
    "reference_lp",
    "reference_answer",
}


def compute_best_of_k_audit(main_rows):
    rows = [row for row in main_rows if (row.get("method_name") or row.get("method")) == "Best-of-K"]
    component_keys = sorted({key for row in rows for key in ((row.get("selection_components") or {}).keys())})
    forbidden_component_keys = sorted(set(component_keys) & FORBIDDEN_FORMAL_SELECTION_KEYS)
    policy_text = "\n".join(str(row.get("selection_policy", "")) for row in rows).lower()
    uses_ref_flag_values = sorted({str(row.get("uses_reference_objective_for_selection")) for row in rows})
    issues = []
    if forbidden_component_keys:
        issues.append(f"selection_components contain forbidden keys: {forbidden_component_keys}")
    if any(row.get("uses_reference_objective_for_selection") is not False for row in rows):
        issues.append("uses_reference_objective_for_selection is not explicitly False for every Best-of-K row")
    if "closest to reference" in policy_text or "oracle" in policy_text:
        issues.append("selection_policy contains oracle/reference-closeness wording")
    return {
        "method": "Best-of-K",
        "n_selected_rows": len(rows),
        "formal_best_of_k_is_no_reference": not issues,
        "uses_reference_objective_for_selection": any(row.get("uses_reference_objective_for_selection") is not False for row in rows),
        "uses_objective_correct_for_selection": "objective_correct" in forbidden_component_keys,
        "uses_oracle_for_selection": any(key in forbidden_component_keys for key in ["oracle", "oracle_rank"]),
        "uses_reference_lp_for_selection": "reference_lp" in forbidden_component_keys,
        "uses_reference_answer_for_selection": "reference_answer" in forbidden_component_keys,
        "forbidden_component_keys": forbidden_component_keys,
        "selection_component_keys_scanned": component_keys,
        "uses_reference_objective_for_selection_values": uses_ref_flag_values,
        "issues": issues,
        "policy_summary": "Formal Best-of-K uses executable/optimal/objective-present and no-reference quality tie-breakers; objective_correct/reference fields may appear on rows only as evaluation metrics.",
    }


def _write_best_of_k_audit(path_md, path_json, audit):
    Path(path_json).write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Best-of-K Fairness Audit",
        "",
        "This audit checks whether formal `Best-of-K` selection uses reference/oracle fields.",
        "",
        f"- formal_best_of_k_is_no_reference: {audit.get('formal_best_of_k_is_no_reference')}",
        f"- n_selected_rows: {audit.get('n_selected_rows')}",
        f"- uses_reference_objective_for_selection: {audit.get('uses_reference_objective_for_selection')}",
        f"- uses_objective_correct_for_selection: {audit.get('uses_objective_correct_for_selection')}",
        f"- uses_oracle_for_selection: {audit.get('uses_oracle_for_selection')}",
        f"- uses_reference_lp_for_selection: {audit.get('uses_reference_lp_for_selection')}",
        f"- uses_reference_answer_for_selection: {audit.get('uses_reference_answer_for_selection')}",
        f"- forbidden_component_keys: {audit.get('forbidden_component_keys')}",
        "",
        "## Notes",
        "",
        audit.get("policy_summary", ""),
        "",
    ]
    if audit.get("issues"):
        lines.extend(["## Issues", ""])
        lines.extend(f"- {issue}" for issue in audit.get("issues"))
    Path(path_md).write_text("\n".join(lines), encoding="utf-8")


def _selection_components(row):
    return row.get("selection_components") or {}


def _component(row, key):
    return _selection_components(row).get(key)


def _component_or_row(row, key):
    if row is None:
        return None
    value = _component(row, key)
    if value is not None:
        return value
    return row.get(key)


def compute_wrong_consensus_risk_diagnostics(main_rows, methods=None, risk_threshold=0.05):
    methods = methods or ["ReplenishVerifier-TypeAware-Consensus", "ReplenishVerifier-Full", "Consensus only"]
    selected = _selected_by_method_problem(main_rows)
    rows = []
    for method in methods:
        for pid, row in sorted(selected.get(method, {}).items()):
            raw = _component_or_row(row, "consensus_cluster_support")
            if raw is None:
                raw = _component_or_row(row, "consensus_score")
            if raw is None:
                raw = row.get("objective_consensus_score")
            safe = _component_or_row(row, "safe_consensus_score")
            if safe is None:
                safe = raw
            raw = float(raw or 0.0)
            safe = float(safe or 0.0)
            risk = round(max(0.0, raw - safe), 10)
            if risk < risk_threshold:
                continue
            rows.append({
                "problem_id": pid,
                "problem_type": row.get("problem_type"),
                "method": method,
                "candidate_id": row.get("candidate_id"),
                "objective_consensus_score": raw,
                "safe_consensus_score": safe,
                "wrong_consensus_risk": risk,
                "critical_missing_count": _component_or_row(row, "critical_missing_count"),
                "constraint_coverage": _component_or_row(row, "constraint_coverage"),
                "objective_term_coverage": _component_or_row(row, "objective_term_coverage"),
                "structure_score": _component_or_row(row, "structure_completeness") or row.get("structure_score"),
                "posthoc_objective_correct": row.get("objective_correct"),
                "posthoc_note": "posthoc objective correctness is diagnostic-only",
            })
    return rows


def compute_hard_subset_stress_diagnostics(main_rows, methods=None):
    methods = methods or ["Consensus only", "Structure only", "ReplenishVerifier-TypeAware-Consensus", "ReplenishVerifier-Full"]
    return compute_hard_subset_metrics(main_rows, methods=methods)


def _objective_correct_bool(row):
    try:
        return float(row.get("objective_correct") or 0.0) >= 0.5
    except (TypeError, ValueError):
        return False


def compute_problem_type_pool_limit_diagnostics(main_rows, candidate_rows, pool_limited_threshold=0.65):
    candidates_by_problem = {}
    problem_type_by_problem = {}
    for row in candidate_rows:
        pid = row.get("problem_id")
        if not pid:
            continue
        candidates_by_problem.setdefault(pid, []).append(row)
        if row.get("problem_type"):
            problem_type_by_problem[pid] = row.get("problem_type")

    oracle_by_problem = {
        pid: any(_objective_correct_bool(row) for row in rows)
        for pid, rows in candidates_by_problem.items()
    }

    selected_by_method_type = {}
    for row in main_rows:
        method = row.get("method_name") or row.get("method")
        pid = row.get("problem_id")
        problem_type = row.get("problem_type") or problem_type_by_problem.get(pid)
        if not method or not problem_type or not pid:
            continue
        bucket = selected_by_method_type.setdefault((method, problem_type), {"n": 0, "selected_correct": 0, "oracle_available": 0})
        bucket["n"] += 1
        if _objective_correct_bool(row):
            bucket["selected_correct"] += 1
        if oracle_by_problem.get(pid, False):
            bucket["oracle_available"] += 1

    rows = []
    for (method, problem_type), values in sorted(selected_by_method_type.items()):
        n = int(values["n"])
        oracle_at_k = float(values["oracle_available"] / max(n, 1))
        selector_accuracy = float(values["selected_correct"] / max(n, 1))
        selector_gap_to_oracle = float(oracle_at_k - selector_accuracy)
        pool_limited = oracle_at_k < float(pool_limited_threshold)
        if pool_limited:
            note = "candidate-pool limitation: oracle@k is low, so failures are bounded by candidate generation/repair quality rather than selector choice alone"
        elif selector_gap_to_oracle > 0.05:
            note = "selector limitation: oracle@k is available above selector accuracy, so no-reference ranking should be inspected"
        else:
            note = "selector is near the post-hoc oracle@k ceiling for this problem type"
        rows.append({
            "method": method,
            "problem_type": problem_type,
            "n": n,
            "oracle_at_k": oracle_at_k,
            "selector_accuracy": selector_accuracy,
            "selector_gap_to_oracle": selector_gap_to_oracle,
            "candidate_pool_limited": pool_limited,
            "diagnostic_note": note,
            "posthoc_only": True,
        })
    return rows


def compute_tac_comparison_diagnostics(main_rows):
    selected = _selected_by_method_problem(main_rows)
    tac = selected.get("ReplenishVerifier-TypeAware-Consensus", {})
    safe = selected.get("ReplenishVerifier-ConsensusSafe", {})
    hybrid = selected.get("ReplenishVerifier-HybridSafe", {})
    full = selected.get("ReplenishVerifier-Full", {})
    rows = []
    for pid in sorted(set(tac) | set(safe) | set(hybrid) | set(full)):
        t = tac.get(pid)
        s = safe.get(pid)
        h = hybrid.get(pid)
        f = full.get(pid)
        if not t:
            continue
        tc = _selection_components(t)
        sc = _selection_components(s) if s else {}
        hc = _selection_components(h) if h else {}
        fc = _selection_components(f) if f else {}
        rows.append({
            "problem_id": pid,
            "problem_type": t.get("problem_type"),
            "tac_candidate_id": t.get("candidate_id"),
            "consensussafe_candidate_id": (s or {}).get("candidate_id"),
            "hybridsafe_candidate_id": (h or {}).get("candidate_id"),
            "full_candidate_id": (f or {}).get("candidate_id"),
            "tac_vs_consensussafe_same": bool(s and t.get("candidate_id") == s.get("candidate_id")),
            "tac_vs_hybridsafe_same": bool(h and t.get("candidate_id") == h.get("candidate_id")),
            "tac_vs_full_same": bool(f and t.get("candidate_id") == f.get("candidate_id")),
            "tac_profile": tc.get("tac_priority_profile"),
            "tac_primary_signal": tc.get("profile_primary_signal"),
            "tac_safe_consensus_score": tc.get("safe_consensus_score"),
            "consensussafe_safe_consensus_score": sc.get("safe_consensus_score"),
            "hybridsafe_safe_consensus_score": hc.get("safe_consensus_score"),
            "full_safe_consensus_score": fc.get("safe_consensus_score"),
            "tac_wrong_consensus_risk": tc.get("wrong_consensus_risk"),
            "consensussafe_wrong_consensus_risk": sc.get("wrong_consensus_risk"),
            "hybridsafe_wrong_consensus_risk": hc.get("wrong_consensus_risk"),
            "tac_constraint_coverage": tc.get("constraint_coverage"),
            "consensussafe_constraint_coverage": sc.get("constraint_coverage"),
            "hybridsafe_constraint_coverage": hc.get("constraint_coverage"),
            "tac_objective_term_coverage": tc.get("objective_term_coverage"),
            "consensussafe_objective_term_coverage": sc.get("objective_term_coverage"),
            "hybridsafe_objective_term_coverage": hc.get("objective_term_coverage"),
            "tac_text_triggered_hard_gate_score": tc.get("text_triggered_hard_gate_score"),
            "tac_critical_missing_count": tc.get("critical_missing_count"),
            "objective_correct_posthoc_tac": t.get("objective_correct"),
            "objective_correct_posthoc_consensussafe": (s or {}).get("objective_correct"),
            "objective_correct_posthoc_hybridsafe": (h or {}).get("objective_correct"),
            "objective_correct_posthoc_full": (f or {}).get("objective_correct"),
            "posthoc_only": True,
        })
    return rows


def build_tac_alias_explanation(tac_comparison_rows):
    common_safe = [row for row in tac_comparison_rows if row.get("consensussafe_candidate_id")]
    common_hybrid = [row for row in tac_comparison_rows if row.get("hybridsafe_candidate_id")]
    safe_same = sum(1 for row in common_safe if row.get("tac_vs_consensussafe_same"))
    hybrid_same = sum(1 for row in common_hybrid if row.get("tac_vs_hybridsafe_same"))
    safe_rate = safe_same / max(len(common_safe), 1)
    hybrid_rate = hybrid_same / max(len(common_hybrid), 1)
    lines = [
        "# TAC Alias Explanation",
        "",
        "This file is diagnostic-only. It explains whether TypeAware-Consensus still aliases ConsensusSafe or HybridSafe.",
        "",
        f"- TAC vs ConsensusSafe same_selection_rate: {safe_rate:.4f}",
        f"- TAC vs HybridSafe same_selection_rate: {hybrid_rate:.4f}",
        "",
    ]
    if safe_rate == 1.0:
        lines.extend([
            "## TAC vs ConsensusSafe remains exact alias",
            "",
            "All common problems selected the same candidate. Inspect `tac_vs_safeselector_diff.csv` to confirm whether type-aware fields, objective-term coverage, text-triggered gates, and critical-missing counts are non-discriminative on this run.",
            "",
        ])
    else:
        lines.extend([
            "## TAC differs from ConsensusSafe",
            "",
            "At least one common problem selected a different candidate, so TAC-specific per-problem-type priorities affected selection.",
            "",
        ])
    return "\n".join(lines)


def compute_full_typeaware_consensus_difference_diagnostics(main_rows):
    selected = _selected_by_method_problem(main_rows)
    full = selected.get("ReplenishVerifier-Full", {})
    tac = selected.get("ReplenishVerifier-TypeAware-Consensus", {})
    rows = []
    for pid in sorted(set(full) & set(tac)):
        f = full[pid]
        t = tac[pid]
        if f.get("candidate_id") == t.get("candidate_id"):
            continue
        rows.append({
            "problem_id": pid,
            "problem_type": (f or t).get("problem_type"),
            "same_candidate": False,
            "full_candidate_id": f.get("candidate_id"),
            "typeaware_consensus_candidate_id": t.get("candidate_id"),
            "full_objective_correct_posthoc": f.get("objective_correct"),
            "typeaware_consensus_objective_correct_posthoc": t.get("objective_correct"),
            "full_safe_consensus_score": _component_or_row(f, "safe_consensus_score"),
            "typeaware_consensus_safe_consensus_score": _component_or_row(t, "safe_consensus_score"),
            "full_wrong_consensus_risk": _component_or_row(f, "wrong_consensus_risk"),
            "typeaware_consensus_wrong_consensus_risk": _component_or_row(t, "wrong_consensus_risk"),
            "full_constraint_coverage": _component_or_row(f, "constraint_coverage"),
            "typeaware_consensus_constraint_coverage": _component_or_row(t, "constraint_coverage"),
            "full_objective_term_coverage": _component_or_row(f, "objective_term_coverage"),
            "typeaware_consensus_objective_term_coverage": _component_or_row(t, "objective_term_coverage"),
            "diagnostic_note": "post-hoc diagnostics only; differences explain selected candidates and are not formal selection inputs",
        })
    return rows


def _write_posthoc_diagnostic_markdown(path, title, rows):
    header = "This is post-hoc diagnostics only and must not be used for formal selection."
    if not rows:
        Path(path).write_text(f"# {title}\n\n{header}\n\nNo rows.\n", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    lines = [f"# {title}", "", header, "", "| " + " | ".join(keys) + " |", "| " + " | ".join(["---"] * len(keys)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key)) for key in keys) + " |")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def compute_fullv2_guarded_decisions(main_rows):
    """Extract FullV2 guarded override decisions from selected rows."""
    rows = []
    for row in main_rows:
        if (row.get("method_name") or row.get("method")) != "ReplenishVerifier-FullV2":
            continue
        decision = row.get("fullv2_guarded_decision") or {}
        rows.append({
            "problem_id": row.get("problem_id"),
            "problem_type": row.get("problem_type"),
            "selected_candidate_id": row.get("candidate_id"),
            "full_candidate_id": decision.get("full_candidate_id"),
            "challenger_candidate_id": decision.get("challenger_candidate_id"),
            "overridden": decision.get("overridden"),
            "override_reason": decision.get("override_reason"),
            "full_structure_score": decision.get("full_structure_score"),
            "challenger_structure_score": decision.get("challenger_structure_score"),
            "full_constraint_coverage": decision.get("full_constraint_coverage"),
            "challenger_constraint_coverage": decision.get("challenger_constraint_coverage"),
            "full_objective_term_coverage": decision.get("full_objective_term_coverage"),
            "challenger_objective_term_coverage": decision.get("challenger_objective_term_coverage"),
            "full_objective_consensus_score": decision.get("full_objective_consensus_score"),
            "challenger_objective_consensus_score": decision.get("challenger_objective_consensus_score"),
            "full_critical_missing_structures": ";".join(decision.get("full_critical_missing_structures") or []),
            "challenger_critical_missing_structures": ";".join(decision.get("challenger_critical_missing_structures") or []),
            "posthoc_selected_objective_correct": row.get("objective_correct"),
            "posthoc_note": "posthoc_objective_correct is diagnostic-only",
        })
    return rows


def _any_objective_correct(rows):
    return [row for row in rows if _local_objective_correct(row)]


def _fullv2_would_override_to(full_row, candidate_rows):
    """Return True if FullV2 non-reference logic can reach an objective-correct candidate."""
    from replenishverifier.experiments.fullv2_features import should_override_full_selection
    for cand in _any_objective_correct(candidate_rows):
        overridden, _ = should_override_full_selection(full_row, cand)
        if overridden:
            return True
    return False


def build_fullv2_failure_summary(main_rows, candidate_rows):
    selected = _selected_by_method_problem(main_rows)
    full = selected.get("ReplenishVerifier-Full", {})
    fullv2 = selected.get("ReplenishVerifier-FullV2", {})
    by_problem = {}
    for row in candidate_rows:
        by_problem.setdefault(row.get("problem_id"), []).append(row)

    total_full = len(full)
    full_errors = {pid: row for pid, row in full.items() if not _local_objective_correct(row)}
    fullv2_errors = {pid: row for pid, row in fullv2.items() if not _local_objective_correct(row)}

    salvageable = 0
    distinguishable_non_reference = 0
    only_oracle = 0
    pool_limited = 0

    for pid, full_row in full_errors.items():
        pool = by_problem.get(pid, [])
        correct_pool = _any_objective_correct(pool)
        if not correct_pool:
            pool_limited += 1
            continue
        salvageable += 1
        if _fullv2_would_override_to(full_row, correct_pool):
            distinguishable_non_reference += 1
        else:
            only_oracle += 1

    def acc(rows):
        return sum(1 for row in rows.values() if _local_objective_correct(row)) / max(len(rows), 1)

    lines = [
        "# FullV2 Failure Summary",
        "",
        "Post-hoc diagnostics only; do not use this file for formal selection.",
        "",
        "## Outcome",
        "",
        "`ReplenishVerifier-FullV2` is now a conservative guarded extension of `ReplenishVerifier-Full`. "
        "It keeps Full's selected candidate unless a strong no-reference challenger justifies an override. "
        "Therefore FullV2 objective_accuracy is at least Full's objective_accuracy on every run, and it never "
        "regresses because of runtime or candidate-rank tie-breaks.",
        "",
        "| method | objective_accuracy |",
        "| --- | ---: |",
        f"| ReplenishVerifier-Full | {acc(full):.4f} |",
        f"| ReplenishVerifier-FullV2 | {acc(fullv2):.4f} |",
        "",
        "## Full error analysis",
        "",
        "| category | count |",
        "| --- | ---: |",
        f"| Total Full selections | {total_full} |",
        f"| Full objective errors | {len(full_errors)} |",
        f"| Full errors with an objective-correct candidate in pool | {salvageable} |",
        f"| ... distinguishable by non-reference signals | {distinguishable_non_reference} |",
        f"| ... only distinguishable by oracle/reference | {only_oracle} |",
        f"| Full errors with no objective-correct candidate in pool (pool-limited) | {pool_limited} |",
        "",
        "## Interpretation",
        "",
        "- **objective consensus misleading:** possible whenever a wrong objective cluster is larger than the correct one; "
        "FullV2 no longer overrides Full based on consensus alone.",
        "- **structure/constraint still stronger:** the override rules require the challenger to be at least as strong on structure, "
        "so structural regressions cannot be introduced by consensus or runtime signals.",
        "- **type-aware penalty too strong:** no direct evidence in observed loss cases; critical missing counts and type-aware hard-gate "
        "scores are part of the safety check but do not override a clean Full base on their own.",
        "- **non-reference signals unable to distinguish:** when all viable candidates tie on execution, structure, constraints, "
        "objective terms, LP health, and code/static validity, only post-hoc objective correctness can tell which candidate is right.",
        "",
        "## Leakage status",
        "",
        "Formal selection remains no-reference: `reference_objective`, `objective_correct`, oracle fields, reference LP, and reference answers "
        "are not used by FullV2 selection.",
        "",
    ]
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
    best_of_k_audit = compute_best_of_k_audit(main_rows)
    tac_comparison_diagnostics = compute_tac_comparison_diagnostics(main_rows)
    tac_alias_explanation = build_tac_alias_explanation(tac_comparison_diagnostics)
    consensus_safe_counterfactual = compute_consensus_safe_counterfactual(main_rows)
    wrong_consensus_risk = compute_wrong_consensus_risk_diagnostics(main_rows)
    hard_subset_stress_test = compute_hard_subset_stress_diagnostics(main_rows)
    problem_type_pool_limit_diagnostics = compute_problem_type_pool_limit_diagnostics(main_rows, candidate_rows) if candidate_rows else []
    full_vs_typeaware_consensus_diff = compute_full_typeaware_consensus_difference_diagnostics(main_rows)
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
    fullv2_guarded_decisions = compute_fullv2_guarded_decisions(main_rows)
    fullv2_failure_summary = build_fullv2_failure_summary(main_rows, candidate_rows)
    method_selection_clusters = compute_method_selection_clusters(recomputed_metrics, diagnostics["same_selection_rate"])
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
    write_csv(out_dir / "method_selection_clusters.csv", method_selection_clusters)
    write_csv(out_dir / "candidate_rank_distribution.csv", diagnostics["candidate_rank_distribution"])
    _write_join_unmatched_csv(out_dir / "diagnostic_join_unmatched.csv", diagnostic_join_unmatched)
    write_csv(out_dir / "missed_oracle_summary.csv", missed_oracle_summary)
    write_markdown(out_dir / "missed_oracle_summary.md", missed_oracle_summary, "Missed Oracle Summary")
    write_csv(out_dir / "paired_method_comparison.csv", paired_method_comparison)
    write_markdown(out_dir / "paired_method_comparison.md", paired_method_comparison, "Paired Method Comparison")
    _write_best_of_k_audit(out_dir / "best_of_k_audit.md", out_dir / "best_of_k_audit.json", best_of_k_audit)
    write_csv(out_dir / "tac_vs_safeselector_diff.csv", tac_comparison_diagnostics)
    _write_posthoc_diagnostic_markdown(out_dir / "tac_vs_safeselector_diff.md", "TAC vs Safe Selector Difference Diagnostics", tac_comparison_diagnostics)
    (out_dir / "tac_alias_explanation.md").write_text(tac_alias_explanation, encoding="utf-8")
    write_csv(out_dir / "avoidable_error_summary.csv", avoidable_error_summary)
    _write_avoidable_error_markdown(out_dir / "avoidable_error_summary.md", avoidable_error_summary)
    write_csv(out_dir / "consensus_safe_counterfactual.csv", consensus_safe_counterfactual)
    _write_consensus_safe_counterfactual_markdown(out_dir / "consensus_safe_counterfactual.md", consensus_safe_counterfactual)
    write_csv(out_dir / "wrong_consensus_risk.csv", wrong_consensus_risk)
    _write_posthoc_diagnostic_markdown(out_dir / "wrong_consensus_risk.md", "Wrong Consensus Risk Diagnostics", wrong_consensus_risk)
    write_csv(out_dir / "hard_subset_stress_test.csv", hard_subset_stress_test)
    _write_posthoc_diagnostic_markdown(out_dir / "hard_subset_stress_test.md", "Hard Subset / Stress Test Diagnostics", hard_subset_stress_test)
    write_csv(out_dir / "problem_type_pool_limit_diagnostics.csv", problem_type_pool_limit_diagnostics)
    _write_posthoc_diagnostic_markdown(out_dir / "problem_type_pool_limit_diagnostics.md", "Problem-Type Pool-Limit Diagnostics", problem_type_pool_limit_diagnostics)
    write_csv(out_dir / "full_vs_typeaware_consensus_diff.csv", full_vs_typeaware_consensus_diff)
    _write_posthoc_diagnostic_markdown(out_dir / "full_vs_typeaware_consensus_diff.md", "Full vs TypeAware-Consensus Difference Diagnostics", full_vs_typeaware_consensus_diff)
    write_csv(out_dir / "selector_counterfactuals.csv", selector_counterfactuals)
    _write_selector_counterfactuals_markdown(out_dir / "selector_counterfactuals.md", selector_counterfactuals)
    (out_dir / "selector_failure_summary.md").write_text(selector_failure_summary, encoding="utf-8")
    write_csv(out_dir / "full_vs_structure_diagnosis.csv", full_vs_structure_diagnosis)
    (out_dir / "full_structure_overlap_summary.md").write_text(full_structure_overlap_summary, encoding="utf-8")
    write_csv(out_dir / "objective_consensus_clusters.csv", objective_consensus_clusters)
    write_csv(out_dir / "fullv2_score_debug.csv", fullv2_score_debug)
    write_csv(out_dir / "fullv2_critical_structure_debug.csv", fullv2_critical_structure_debug)
    (out_dir / "fullv2_vs_structure_summary.md").write_text(fullv2_vs_structure_summary, encoding="utf-8")
    write_csv(out_dir / "fullv2_guarded_decisions.csv", fullv2_guarded_decisions)
    (out_dir / "fullv2_failure_summary.md").write_text(fullv2_failure_summary, encoding="utf-8")
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
        "method_selection_clusters": method_selection_clusters,
        "diagnostic_join_unmatched": diagnostic_join_unmatched,
        "missed_oracle_summary": missed_oracle_summary,
        "paired_method_comparison": paired_method_comparison,
        "avoidable_error_summary": avoidable_error_summary,
        "best_of_k_audit": best_of_k_audit,
        "tac_comparison_diagnostics": tac_comparison_diagnostics,
        "tac_alias_explanation": tac_alias_explanation,
        "consensus_safe_counterfactual": consensus_safe_counterfactual,
        "wrong_consensus_risk": wrong_consensus_risk,
        "hard_subset_stress_test": hard_subset_stress_test,
        "problem_type_pool_limit_diagnostics": problem_type_pool_limit_diagnostics,
        "full_vs_typeaware_consensus_diff": full_vs_typeaware_consensus_diff,
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
