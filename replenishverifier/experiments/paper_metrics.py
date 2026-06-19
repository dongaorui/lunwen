import csv
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from replenishverifier.experiments.baselines import classify_error_type


BASE_METRICS = [
    "executable_rate",
    "optimal_rate",
    "objective_accuracy",
    "structure_completeness",
    "inventory_balance_accuracy",
    "constraint_coverage",
    "average_runtime_sec",
    "average_repair_feedback_count",
]


def safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values):
    vals = [safe_float(v) for v in values]
    vals = [v for v in vals if v is not None]
    return None if not vals else float(sum(vals) / len(vals))


def median(values):
    vals = [safe_float(v) for v in values]
    vals = [v for v in vals if v is not None]
    return None if not vals else float(statistics.median(vals))


def rate(values, empty=None):
    vals = [v for v in values if v is not None]
    return empty if not vals else float(sum(1.0 if v else 0.0 for v in vals) / len(vals))


def truthy_count(values):
    vals = [v for v in values if v is not None]
    return int(sum(1 for v in vals if bool(safe_float(v) if not isinstance(v, bool) else v)))


def observed_count(values):
    return int(len([v for v in values if v is not None]))


def feedback_count(row):
    if row.get("repair_feedback_count") is not None:
        return row.get("repair_feedback_count")
    structure = row.get("structure_verification") or {}
    return len(structure.get("missing") or [])


def constraint_coverage(row):
    structure = row.get("structure_verification") or {}
    expected = structure.get("expected") or {}
    detected = structure.get("detected") or {}
    values = []
    for key, needed in expected.items():
        if needed:
            values.append(1.0 if detected.get(key) else 0.0)
    if values:
        return float(sum(values) / len(values))
    required = structure.get("required_structures") or []
    missing = set(structure.get("missing") or [])
    if required:
        return float(len([key for key in required if key not in missing]) / len(required))
    return safe_float(row.get("structure_score", structure.get("structure_score")))


def inventory_balance_hit(row):
    structure = row.get("structure_verification") or {}
    expected = structure.get("expected") or {}
    if not expected.get("inventory_balance"):
        return None
    detected = structure.get("detected") or {}
    return bool(detected.get("inventory_balance"))


def selected_rows(rows):
    return [row for row in rows if row.get("selected", False)]


def group_selected_by_method(rows):
    grouped = defaultdict(list)
    for row in selected_rows(rows):
        grouped[row.get("method_name") or row.get("method") or "unknown"].append(row)
    return grouped


def _status(row):
    return str((row.get("execution") or {}).get("status") or "").strip().lower()


def _is_structure_complete(row):
    return safe_float(row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score"))) == 1.0


def compute_selected_method_metrics(rows):
    result = []
    for method, items in sorted(group_selected_by_method(rows).items()):
        statuses = [_status(row) for row in items]
        rel_errors = [row.get("relative_error") for row in items]
        objective_values = [row.get("objective_correct", row.get("objective_accuracy")) for row in items]
        structure_values = [row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score")) for row in items]
        result.append({
            "method": method,
            "n": len(items),
            "objective_accuracy_count": truthy_count(objective_values),
            "objective_accuracy_total": observed_count(objective_values),
            "structure_complete_count": truthy_count([safe_float(value) == 1.0 if value is not None else None for value in structure_values]),
            "structure_complete_total": observed_count(structure_values),
            "code_validity_rate": rate([row.get("code_output_format_valid") for row in items]),
            "executable_rate": rate([(row.get("execution") or {}).get("executable") for row in items]),
            "optimal_rate": rate([_status(row) == "optimal" for row in items]),
            "solver_status_optimal_rate": rate([status == "optimal" for status in statuses]),
            "solver_status_infeasible_rate": rate([status == "infeasible" for status in statuses]),
            "solver_status_timeout_rate": rate([status == "timeout" for status in statuses]),
            "solver_status_error_rate": rate([status in {"error", "missing", "notrun", "not_run", ""} for status in statuses]),
            "objective_accuracy": mean(objective_values),
            "mean_relative_error": mean(rel_errors),
            "median_relative_error": median(rel_errors),
            "mean_objective_gap": mean(rel_errors),
            "median_objective_gap": median(rel_errors),
            "structure_completeness": mean(structure_values),
            "inventory_balance_accuracy": rate([inventory_balance_hit(row) for row in items], empty=0.0),
            "constraint_coverage": mean([constraint_coverage(row) for row in items]),
            "objective_term_surface_coverage": mean([row.get("objective_term_surface_coverage") for row in items]),
            "objective_term_lp_coefficient_coverage": mean([row.get("objective_term_lp_coefficient_coverage") for row in items]),
            "objective_term_coverage": mean([row.get("objective_term_coverage") for row in items]),
            "average_runtime_sec": mean([row.get("runtime_sec", row.get("total_candidate_evaluation_time")) for row in items]),
            "median_runtime_sec": median([row.get("runtime_sec", row.get("total_candidate_evaluation_time")) for row in items]),
            "average_repair_feedback_count": mean([feedback_count(row) for row in items]),
        })
    return result


def compute_error_type_summary(rows):
    result = []
    for method, items in sorted(group_selected_by_method(rows).items()):
        counts = Counter(classify_error_type(row) for row in items)
        total = len(items)
        for error_type, count in sorted(counts.items()):
            result.append({"method": method, "error_type": error_type, "count": count, "rate": float(count / total) if total else None})
    return result


DEFAULT_PAPER_METHODS = [
    "Direct",
    "Best-of-K",
    "Consensus only",
    "ReplenishVerifier-Full",
    "ReplenishVerifier-TypeAware",
    "ReplenishVerifier-TypeAware-Consensus",
]


def compute_metrics_by_problem_type(rows, methods=None):
    methods = set(methods or DEFAULT_PAPER_METHODS)
    grouped = defaultdict(list)
    for row in selected_rows(rows):
        method = row.get("method_name") or row.get("method") or "unknown"
        if method not in methods:
            continue
        problem_type = row.get("problem_type") or "unknown"
        grouped[(method, problem_type)].append(row)
    result = []
    for (method, problem_type), items in sorted(grouped.items()):
        result.append({
            "method": method,
            "problem_type": problem_type,
            "n": len(items),
            "executable_rate": rate([(row.get("execution") or {}).get("executable") for row in items]),
            "optimal_rate": rate([_status(row) == "optimal" for row in items]),
            "objective_accuracy": mean([row.get("objective_correct", row.get("objective_accuracy")) for row in items]),
            "structure_completeness": mean([row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score")) for row in items]),
            "constraint_coverage": mean([constraint_coverage(row) for row in items]),
            "objective_term_coverage": mean([row.get("objective_term_coverage") for row in items]),
        })
    return result


def _metric_duplicate_signature(row):
    keys = ["objective_accuracy", "structure_completeness", "constraint_coverage", "executable_rate", "optimal_rate"]
    return tuple((key, row.get(key)) for key in keys)


def compute_selection_collapse_summary(main_rows, candidate_rows=None, threshold=0.95):
    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows or [])
    rows = []
    for row in diagnostics["same_selection_rate"]:
        rate_value = row.get("same_selection_rate")
        if rate_value is not None and float(rate_value) >= threshold:
            rows.append({
                "diagnostic_type": "high_same_selection_pair",
                "method_a": row.get("method_a"),
                "method_b": row.get("method_b"),
                "methods": f"{row.get('method_a')}; {row.get('method_b')}",
                "n_common": row.get("n_common"),
                "same_selection_rate": rate_value,
                "count": row.get("same_count"),
                "detail": "Methods select the same candidate on nearly all shared problems.",
            })
    metric_rows = compute_selected_method_metrics(main_rows)
    groups = defaultdict(list)
    for row in metric_rows:
        groups[_metric_duplicate_signature(row)].append(row.get("method"))
    for methods in groups.values():
        if len(methods) > 1:
            rows.append({
                "diagnostic_type": "metric_duplicate_group",
                "method_a": "",
                "method_b": "",
                "methods": "; ".join(sorted(methods)),
                "n_common": "",
                "same_selection_rate": "",
                "count": len(methods),
                "detail": "Methods have identical headline metric values.",
            })
    for row in diagnostics["candidate_rank_distribution"]:
        rows.append({
            "diagnostic_type": "candidate_rank_distribution",
            "method_a": row.get("method"),
            "method_b": "",
            "methods": row.get("method"),
            "n_common": row.get("n"),
            "same_selection_rate": "",
            "count": row.get("n"),
            "detail": f"k0={row.get('k0')}, k1={row.get('k1')}, k2={row.get('k2')}, k3={row.get('k3')}, k_ge_4={row.get('k_ge_4')}",
        })
    if not rows:
        rows.append({
            "diagnostic_type": "no_selection_collapse_detected",
            "method_a": "",
            "method_b": "",
            "methods": "",
            "n_common": "",
            "same_selection_rate": "",
            "count": 0,
            "detail": "No high-overlap or duplicate-metric groups were detected at the configured threshold.",
        })
    return rows


def candidate_index(candidate_id):
    text = str(candidate_id or "")
    marker = text.rsplit("_k", 1)
    if len(marker) == 2 and marker[1].isdigit():
        return int(marker[1])
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def _objective_correct_bool(row):
    return bool(safe_float(row.get("objective_correct", row.get("objective_accuracy"))) == 1.0)


def _missing_structure(row, structure_name):
    structure = row.get("structure_verification") or {}
    return structure_name in set(structure.get("missing") or [])


def _selected_by_method_problem(rows):
    out = defaultdict(dict)
    for row in selected_rows(rows):
        out[row.get("method_name") or row.get("method") or "unknown"][row.get("problem_id")] = row
    return out


def compute_missed_oracle_summary(main_rows, candidate_rows):
    by_problem = defaultdict(list)
    for row in candidate_rows:
        by_problem[row.get("problem_id")].append(row)
    oracle = {}
    for pid, rows in by_problem.items():
        objective_available = any(_objective_correct_bool(row) for row in rows)
        structure_available = any(_is_structure_complete(row) for row in rows)
        both_available = any(_objective_correct_bool(row) and _is_structure_complete(row) for row in rows)
        oracle[pid] = {
            "objective_available": objective_available,
            "structure_available": structure_available,
            "both_available": both_available,
        }

    result = []
    for method, rows_by_problem in sorted(_selected_by_method_problem(main_rows).items()):
        common = [pid for pid in rows_by_problem if pid in oracle]
        objective_available = [pid for pid in common if oracle[pid]["objective_available"]]
        structure_available = [pid for pid in common if oracle[pid]["structure_available"]]
        both_available = [pid for pid in common if oracle[pid]["both_available"]]
        missed_objective = [pid for pid in objective_available if not _objective_correct_bool(rows_by_problem[pid])]
        missed_structure = [pid for pid in structure_available if not _is_structure_complete(rows_by_problem[pid])]
        missed_both = [pid for pid in both_available if not (_objective_correct_bool(rows_by_problem[pid]) and _is_structure_complete(rows_by_problem[pid]))]
        result.append({
            "method": method,
            "n_common": len(common),
            "oracle_objective_available_count": len(objective_available),
            "missed_oracle_objective_count": len(missed_objective),
            "missed_oracle_objective_rate": float(len(missed_objective) / len(objective_available)) if objective_available else 0.0,
            "oracle_structure_available_count": len(structure_available),
            "missed_oracle_structure_count": len(missed_structure),
            "missed_oracle_structure_rate": float(len(missed_structure) / len(structure_available)) if structure_available else 0.0,
            "oracle_both_available_count": len(both_available),
            "missed_oracle_both_count": len(missed_both),
            "missed_oracle_both_rate": float(len(missed_both) / len(both_available)) if both_available else 0.0,
        })
    return result


def compute_paired_method_comparison(rows, target_method="ReplenishVerifier-TypeAware", baseline_methods=None):
    baseline_methods = baseline_methods or ["Direct", "Best-of-K", "ReplenishVerifier-Full"]
    by_method = _selected_by_method_problem(rows)
    target = by_method.get(target_method, {})
    result = []
    for baseline_method in baseline_methods:
        baseline = by_method.get(baseline_method, {})
        common = sorted(set(target) & set(baseline))
        objective_win = objective_loss = objective_tie = 0
        structure_win = structure_loss = structure_tie = 0
        missing_capacity_reduction = missing_capacity_increase = 0
        objective_mismatch_reduction = objective_mismatch_increase = 0
        for pid in common:
            t = target[pid]
            b = baseline[pid]
            t_obj = _objective_correct_bool(t)
            b_obj = _objective_correct_bool(b)
            if t_obj and not b_obj:
                objective_win += 1
            elif b_obj and not t_obj:
                objective_loss += 1
            else:
                objective_tie += 1

            t_struct = safe_float(t.get("structure_score", (t.get("structure_verification") or {}).get("structure_score"))) or 0.0
            b_struct = safe_float(b.get("structure_score", (b.get("structure_verification") or {}).get("structure_score"))) or 0.0
            if t_struct > b_struct:
                structure_win += 1
            elif b_struct > t_struct:
                structure_loss += 1
            else:
                structure_tie += 1

            t_missing_capacity = _missing_structure(t, "capacity_constraint")
            b_missing_capacity = _missing_structure(b, "capacity_constraint")
            if b_missing_capacity and not t_missing_capacity:
                missing_capacity_reduction += 1
            elif t_missing_capacity and not b_missing_capacity:
                missing_capacity_increase += 1

            t_objective_mismatch = not t_obj
            b_objective_mismatch = not b_obj
            if b_objective_mismatch and not t_objective_mismatch:
                objective_mismatch_reduction += 1
            elif t_objective_mismatch and not b_objective_mismatch:
                objective_mismatch_increase += 1

        result.append({
            "target_method": target_method,
            "baseline_method": baseline_method,
            "n_common": len(common),
            "objective_win_count": objective_win,
            "objective_loss_count": objective_loss,
            "objective_tie_count": objective_tie,
            "structure_win_count": structure_win,
            "structure_loss_count": structure_loss,
            "structure_tie_count": structure_tie,
            "missing_capacity_reduction_count": missing_capacity_reduction,
            "missing_capacity_increase_count": missing_capacity_increase,
            "objective_mismatch_reduction_count": objective_mismatch_reduction,
            "objective_mismatch_increase_count": objective_mismatch_increase,
        })
    return result


def compute_pass_at_k(candidate_rows, k_values):
    by_problem = defaultdict(list)
    for row in candidate_rows:
        by_problem[row.get("problem_id")].append(row)
    result = []
    for k in k_values:
        objective_hits = []
        structure_hits = []
        both_hits = []
        for rows in by_problem.values():
            top = sorted(rows, key=lambda row: candidate_index(row.get("candidate_id")))[:k]
            has_obj = any(bool(safe_float(row.get("objective_correct", 0.0))) for row in top)
            has_struct = any(_is_structure_complete(row) for row in top)
            objective_hits.append(has_obj)
            structure_hits.append(has_struct)
            both_hits.append(has_obj and has_struct)
        result.append({
            "k": k,
            "pass_at_k_objective": rate(objective_hits),
            "pass_at_k_structure": rate(structure_hits),
            "pass_at_k_both": rate(both_hits),
            "oracle_objective_accuracy_at_k": rate(objective_hits),
            "oracle_structure_completeness_at_k": rate(structure_hits),
            "oracle_both_success_at_k": rate(both_hits),
            "uses_reference_for_oracle_metrics": True,
            "formal_selection_metric": False,
        })
    return result


def compute_selection_diagnostics(main_rows, candidate_rows):
    selected_by_method = defaultdict(dict)
    for row in selected_rows(main_rows):
        selected_by_method[row.get("method_name")][row.get("problem_id")] = row.get("candidate_id")
    methods = sorted(selected_by_method)
    same_rows = []
    for i, method_a in enumerate(methods):
        for method_b in methods[i + 1:]:
            common = sorted(set(selected_by_method[method_a]) & set(selected_by_method[method_b]))
            same = sum(1 for pid in common if selected_by_method[method_a][pid] == selected_by_method[method_b][pid])
            same_rows.append({
                "method_a": method_a,
                "method_b": method_b,
                "n_common": len(common),
                "same_count": same,
                "same_selection_rate": float(same / len(common)) if common else None,
            })
    distribution = []
    for method in methods:
        counts = Counter(candidate_index(cid) for cid in selected_by_method[method].values())
        row = {"method": method, "n": sum(counts.values())}
        for idx in range(4):
            row[f"k{idx}"] = counts.get(idx, 0)
        row["k_ge_4"] = sum(count for idx, count in counts.items() if idx >= 4)
        distribution.append(row)
    selected_keys = {(row.get("method_name"), row.get("problem_id"), row.get("candidate_id")) for row in selected_rows(main_rows)}
    debug = []
    by_problem = defaultdict(list)
    for row in candidate_rows:
        by_problem[row.get("problem_id")].append(row)
    for method in methods:
        for pid, rows in sorted(by_problem.items()):
            for row in sorted(rows, key=lambda item: candidate_index(item.get("candidate_id"))):
                execution = row.get("execution") or {}
                debug.append({
                    "method": method,
                    "problem_id": pid,
                    "candidate_id": row.get("candidate_id"),
                    "executable": bool(execution.get("executable")),
                    "solver_status": execution.get("status"),
                    "objective_correct_posthoc": row.get("objective_correct"),
                    "structure_score": row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score")),
                    "consensus_score": row.get("objective_consensus_score"),
                    "selection_score": row.get("selection_score", row.get("score")),
                    "selected": (method, pid, row.get("candidate_id")) in selected_keys,
                })
    return {"same_selection_rate": same_rows, "candidate_rank_distribution": distribution, "selection_score_debug": debug}


def bootstrap_ci_for_metric(items, metric_fn, samples=1000, seed=42):
    if not items:
        return (None, None)
    rng = random.Random(seed)
    values = []
    for _ in range(samples):
        sampled = [items[rng.randrange(len(items))] for _ in items]
        value = metric_fn(sampled)
        if value is not None:
            values.append(value)
    if not values:
        return (None, None)
    values.sort()
    low_idx = int(0.025 * (len(values) - 1))
    high_idx = int(0.975 * (len(values) - 1))
    return (float(values[low_idx]), float(values[high_idx]))


def add_bootstrap_ci(metric_rows, selected_input_rows, metrics=None, samples=1000, seed=42):
    metrics = metrics or ["objective_accuracy", "structure_completeness", "constraint_coverage"]
    grouped = group_selected_by_method(selected_input_rows)
    out = []
    for metric_row in metric_rows:
        row = dict(metric_row)
        items = grouped.get(row["method"], [])
        for metric in metrics:
            if metric == "objective_accuracy":
                fn = lambda sample: mean([item.get("objective_correct", item.get("objective_accuracy")) for item in sample])
            elif metric == "structure_completeness":
                fn = lambda sample: mean([item.get("structure_score", (item.get("structure_verification") or {}).get("structure_score")) for item in sample])
            elif metric == "constraint_coverage":
                fn = lambda sample: mean([constraint_coverage(item) for item in sample])
            else:
                continue
            low, high = bootstrap_ci_for_metric(items, fn, samples=samples, seed=seed)
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
        out.append(row)
    return out


def format_metric_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path, rows, title):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text(f"# {title}\n\nNo rows.\n", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(format_metric_value(row.get(header)) for header in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
