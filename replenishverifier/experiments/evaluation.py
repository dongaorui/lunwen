import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from replenishverifier.data.structure_schema import STRUCTURE_KEYS
from replenishverifier.experiments.paper_metrics import constraint_coverage as row_constraint_coverage
from replenishverifier.utils.io import write_jsonl


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def mean(values):
    values = [v for v in values if v is not None]
    if not values:
        return 0.0
    return float(np.mean(values))


def count_feedback_items(row):
    structure = row.get("structure_verification") or {}
    missing = structure.get("missing") or []
    return len(missing)


def flatten_row(row):
    execution = row.get("execution") or {}
    structure = row.get("structure_verification") or {}
    flat = {
        "method": row.get("method_name"),
        "problem_id": row.get("problem_id"),
        "candidate_id": row.get("candidate_id"),
        "problem_type": row.get("problem_type"),
        "difficulty": row.get("difficulty"),
        "selected": row.get("selected", False),
        "executable": execution.get("executable", False),
        "status": execution.get("status"),
        "objective": execution.get("objective"),
        "reference_objective": row.get("reference_objective"),
        "score": row.get("score"),
        "objective_correct": row.get("objective_correct"),
        "relative_error": row.get("relative_error"),
        "structure_score": row.get("structure_score", structure.get("structure_score")),
        "semantic_consistency_score": row.get("semantic_consistency_score"),
        "sirl_like_lp_stats_score": row.get("sirl_like_lp_stats_score"),
        "optargus_like_audit_score": row.get("optargus_like_audit_score"),
        "optirepair_like_repair_score": row.get("optirepair_like_repair_score"),
        "or_r1_like_voting_score": row.get("or_r1_like_voting_score"),
        "objective_consensus_score": row.get("objective_consensus_score"),
        "selection_policy": row.get("selection_policy"),
        "uses_reference_objective_for_selection": row.get("uses_reference_objective_for_selection"),
        "runtime_sec": row.get("runtime_sec"),
        "repair_feedback_count": count_feedback_items(row),
        "error": execution.get("error") or row.get("error"),
    }
    detected = structure.get("detected") or {}
    expected = structure.get("expected") or {}
    for key in STRUCTURE_KEYS:
        flat[f"expected_{key}"] = expected.get(key)
        flat[f"detected_{key}"] = detected.get(key)
    return flat


def save_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flat_rows = [flatten_row(row) for row in rows]
    if not flat_rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)


def save_markdown_table(path, rows, title=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text("No rows.\n", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = []
    if title:
        lines.extend([f"# {title}", ""])
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        vals = []
        for h in headers:
            value = row.get(h, "")
            if isinstance(value, float):
                vals.append(f"{value:.4f}")
            else:
                vals.append(str(value).replace("\n", "<br>"))
        lines.append("| " + " | ".join(vals) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_result_bundle(prefix, rows, summary_rows=None, title=None):
    prefix = Path(prefix)
    write_jsonl(prefix.with_suffix(".jsonl"), rows)
    save_csv(prefix.with_suffix(".csv"), rows)
    if summary_rows is None:
        summary_rows = summarize_by_method(rows)
    save_markdown_table(prefix.with_suffix(".md"), summary_rows, title=title)


def summarize_by_method(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row.get("selected", False):
            grouped[row.get("method_name", "unknown")].append(row)

    summary = []
    for method, items in grouped.items():
        summary.append(summarize_rows(items, method=method))
    return sorted(summary, key=lambda row: row["method"])


def summarize_rows(rows, method=None, group_name=None):
    rows = list(rows)
    if not rows:
        return {}

    executable = []
    optimal = []
    objective_correct = []
    structure_scores = []
    inventory_balance_hits = []
    runtime = []
    feedback_counts = []
    coverage_values = []

    for row in rows:
        execution = row.get("execution") or {}
        structure = row.get("structure_verification") or {}
        expected = structure.get("expected") or {}
        detected = structure.get("detected") or {}

        executable.append(1.0 if execution.get("executable") else 0.0)
        optimal.append(1.0 if execution.get("status") == "Optimal" else 0.0)
        objective_correct.append(float(row.get("objective_correct", 0.0) or 0.0))
        structure_scores.append(float(row.get("structure_score", structure.get("structure_score", 0.0)) or 0.0))
        runtime.append(row.get("runtime_sec", 0.0))
        feedback_counts.append(count_feedback_items(row))

        if expected.get("inventory_balance"):
            inventory_balance_hits.append(1.0 if detected.get("inventory_balance") else 0.0)

        coverage = row_constraint_coverage(row)
        if coverage is not None:
            coverage_values.append(coverage)

    out = {
        "method": method or "all",
        "n": len(rows),
        "executable_rate": mean(executable),
        "optimal_rate": mean(optimal),
        "objective_accuracy": mean(objective_correct),
        "structure_completeness": mean(structure_scores),
        "inventory_balance_accuracy": mean(inventory_balance_hits),
        "constraint_coverage": mean(coverage_values),
        "average_runtime_sec": mean(runtime),
        "average_repair_feedback_count": mean(feedback_counts),
    }
    if group_name is not None:
        out["group"] = group_name
    return out


def summarize_by_difficulty(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row.get("selected", False):
            grouped[(row.get("method_name", "unknown"), row.get("difficulty", "unknown"))].append(row)
    result = []
    for (method, difficulty), items in grouped.items():
        row = summarize_rows(items, method=method, group_name=difficulty)
        row["difficulty"] = difficulty
        result.append(row)
    return sorted(result, key=lambda item: (item["method"], item.get("difficulty", "")))


def benchmark_table(benchmark_rows):
    by_type = defaultdict(list)
    for row in benchmark_rows:
        by_type[row.get("problem_type", "unknown")].append(row)

    table = []
    for problem_type, items in sorted(by_type.items()):
        expected_counts = defaultdict(int)
        for item in items:
            for key, value in item.get("expected_structures", {}).items():
                if value:
                    expected_counts[key] += 1
        table.append({
            "problem_type": problem_type,
            "difficulty": items[0].get("difficulty", "unknown"),
            "n": len(items),
            "avg_n_required_structures": mean([sum(1 for v in item.get("expected_structures", {}).values() if v) for item in items]),
            "inventory_balance": expected_counts["inventory_balance"],
            "shortage": expected_counts["shortage_variable"],
            "capacity": expected_counts["capacity_constraint"],
            "binary_big_m": expected_counts["big_m_constraint"],
        })
    return table


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
