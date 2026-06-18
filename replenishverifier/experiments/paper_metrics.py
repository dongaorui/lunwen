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
        result.append({
            "method": method,
            "n": len(items),
            "code_validity_rate": rate([row.get("code_output_format_valid") for row in items]),
            "executable_rate": rate([(row.get("execution") or {}).get("executable") for row in items]),
            "optimal_rate": rate([_status(row) == "optimal" for row in items]),
            "solver_status_optimal_rate": rate([status == "optimal" for status in statuses]),
            "solver_status_infeasible_rate": rate([status == "infeasible" for status in statuses]),
            "solver_status_timeout_rate": rate([status == "timeout" for status in statuses]),
            "solver_status_error_rate": rate([status in {"error", "missing", "notrun", "not_run", ""} for status in statuses]),
            "objective_accuracy": mean([row.get("objective_correct", row.get("objective_accuracy")) for row in items]),
            "mean_relative_error": mean(rel_errors),
            "median_relative_error": median(rel_errors),
            "mean_objective_gap": mean(rel_errors),
            "median_objective_gap": median(rel_errors),
            "structure_completeness": mean([row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score")) for row in items]),
            "inventory_balance_accuracy": rate([inventory_balance_hit(row) for row in items], empty=0.0),
            "constraint_coverage": mean([constraint_coverage(row) for row in items]),
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


def candidate_index(candidate_id):
    text = str(candidate_id or "")
    marker = text.rsplit("_k", 1)
    if len(marker) == 2 and marker[1].isdigit():
        return int(marker[1])
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


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
