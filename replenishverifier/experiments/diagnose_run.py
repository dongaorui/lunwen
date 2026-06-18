import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from replenishverifier.experiments.baselines import classify_error_type
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _mean(values):
    values = [float(v) for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0


def _objective_key(value):
    if value is None:
        return "missing"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


def _required_missing(row):
    structure = row.get("structure_verification") or {}
    missing = set(structure.get("missing") or [])
    required = structure.get("required_structures")
    if required is None:
        expected = structure.get("expected") or {}
        required = [key for key, value in expected.items() if value]
    if required:
        missing &= set(required)
    return sorted(missing)


def _structure_complete(row):
    structure = row.get("structure_verification") or {}
    if structure.get("required_structures") or structure.get("expected"):
        return not _required_missing(row)
    return float(row.get("structure_score", structure.get("structure_score", 0.0)) or 0.0) >= 1.0


def _structure_signature(row):
    structure = row.get("structure_verification") or {}
    detected = structure.get("detected") or {}
    if detected:
        return tuple(sorted(key for key, value in detected.items() if value))
    return tuple(_required_missing(row))


def _candidate_index(row):
    if row.get("candidate_index") is not None:
        return int(row.get("candidate_index") or 0)
    cid = str(row.get("candidate_id", ""))
    digits = "".join(ch for ch in cid if ch.isdigit())
    return int(digits) if digits else 0


def _selected_by_problem(main_rows):
    selected = {}
    for row in main_rows:
        selected[row.get("problem_id")] = row
    return selected


def _write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _code_excerpt(row, limit=800):
    code = row.get("generated_code") or row.get("generated_text") or ""
    return str(code)[:limit]


def diagnose_run(benchmark_path, candidate_evaluations_path, main_results_path, out_dir):
    benchmark_rows = read_jsonl(benchmark_path)
    candidate_rows = read_jsonl(candidate_evaluations_path)
    main_rows = read_jsonl(main_results_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    benchmark = {row.get("id") or row.get("problem_id"): row for row in benchmark_rows}
    candidates_by_problem = defaultdict(list)
    for row in candidate_rows:
        candidates_by_problem[row.get("problem_id")].append(row)
    selected = _selected_by_problem(main_rows)

    problem_diagnostics = []
    for pid, reference in benchmark.items():
        rows = candidates_by_problem.get(pid, [])
        selected_row = selected.get(pid, {})
        direct = min(rows, key=_candidate_index) if rows else {}
        oracle_objective = any(float(row.get("objective_correct", 0.0) or 0.0) > 0.0 for row in rows)
        oracle_structure = any(_structure_complete(row) for row in rows)
        selected_objective = float(selected_row.get("objective_correct", 0.0) or 0.0) > 0.0
        selected_structure = _structure_complete(selected_row) if selected_row else False
        objectives = {_objective_key((row.get("execution") or {}).get("objective")) for row in rows}
        signatures = {_structure_signature(row) for row in rows}
        problem_diagnostics.append({
            "problem_id": pid,
            "problem_type": reference.get("problem_type") or selected_row.get("problem_type"),
            "selected_method": selected_row.get("method_name"),
            "selected_candidate_id": selected_row.get("candidate_id"),
            "selected_candidate_index": _candidate_index(selected_row) if selected_row else None,
            "direct_objective_correct": float(direct.get("objective_correct", 0.0) or 0.0) > 0.0,
            "any_candidate_objective_correct": oracle_objective,
            "any_candidate_structurally_complete": oracle_structure,
            "selected_objective_correct": selected_objective,
            "selected_structurally_complete": selected_structure,
            "selector_missed_oracle_objective": oracle_objective and not selected_objective,
            "selector_missed_oracle_structure": oracle_structure and not selected_structure,
            "selected_missing_structures": _required_missing(selected_row),
            "selected_static_validation_errors": selected_row.get("static_validation_errors") or ((selected_row.get("static_validation") or {}).get("static_validation_errors") or []),
            "unique_objective_value_count": len(objectives),
            "unique_structure_signature_count": len(signatures),
            "candidate_count": len(rows),
            "main_error_type": classify_error_type(selected_row) if selected_row else "missing_selection",
        })

    write_jsonl(out_dir / "problem_diagnostics.jsonl", problem_diagnostics)

    by_type = defaultdict(list)
    for row in problem_diagnostics:
        by_type[row.get("problem_type", "unknown")].append(row)
    problem_type_summary = []
    for problem_type, items in sorted(by_type.items()):
        problem_type_summary.append({
            "problem_type": problem_type,
            "n": len(items),
            "objective_accuracy": _mean([item["selected_objective_correct"] for item in items]),
            "structure_completeness": _mean([item["selected_structurally_complete"] for item in items]),
            "oracle_objective_accuracy": _mean([item["any_candidate_objective_correct"] for item in items]),
            "oracle_structure_completeness": _mean([item["any_candidate_structurally_complete"] for item in items]),
            "main_error_type_distribution": json.dumps(dict(Counter(item["main_error_type"] for item in items)), ensure_ascii=False),
        })
    _write_csv(out_dir / "problem_type_summary.csv", problem_type_summary)

    diversity_rows = []
    for pid, rows in sorted(candidates_by_problem.items()):
        diversity_rows.append({
            "problem_id": pid,
            "problem_type": (benchmark.get(pid) or {}).get("problem_type"),
            "candidate_count": len(rows),
            "unique_objective_value_count": len({_objective_key((row.get("execution") or {}).get("objective")) for row in rows}),
            "unique_structure_signature_count": len({_structure_signature(row) for row in rows}),
        })
    _write_csv(out_dir / "candidate_diversity.csv", diversity_rows)

    missing_counts = Counter()
    for row in main_rows:
        for key in _required_missing(row):
            missing_counts[f"missing_{key}"] += 1
    missing_rows = [{"missing_structure": key, "count": count} for key, count in sorted(missing_counts.items())]
    _write_csv(out_dir / "missing_structure_distribution.csv", missing_rows)

    examples = []
    by_error = defaultdict(list)
    for row in main_rows:
        by_error[classify_error_type(row)].append(row)
    for error_type, rows in sorted(by_error.items()):
        for row in rows[:5]:
            execution = row.get("execution") or {}
            examples.append({
                "error_type": error_type,
                "problem_id": row.get("problem_id"),
                "problem_type": row.get("problem_type"),
                "selected_method": row.get("method_name"),
                "selected_candidate_id": row.get("candidate_id"),
                "candidate_objective": execution.get("objective"),
                "reference_objective": row.get("reference_objective"),
                "missing_structures": _required_missing(row),
                "static_validation_errors": row.get("static_validation_errors") or ((row.get("static_validation") or {}).get("static_validation_errors") or []),
                "generated_code_excerpt": _code_excerpt(row),
                "repair_feedback": row.get("feedback", ""),
            })
    write_jsonl(out_dir / "failure_examples.jsonl", examples)

    summary_lines = [
        "# Run Diagnostics",
        "",
        f"Problems: {len(problem_diagnostics)}",
        f"Candidates: {len(candidate_rows)}",
        f"Selected rows: {len(main_rows)}",
        "",
        "## Problem type summary",
        "",
        "| problem_type | n | objective_accuracy | structure_completeness |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in problem_type_summary:
        summary_lines.append(f"| {row['problem_type']} | {row['n']} | {row['objective_accuracy']:.4f} | {row['structure_completeness']:.4f} |")
    summary_lines.extend(["", "Reference objectives are used only for diagnostic display/oracle analysis, not selection."])
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "problem_diagnostics": problem_diagnostics,
        "problem_type_summary": problem_type_summary,
        "candidate_diversity": diversity_rows,
        "missing_structure_distribution": missing_rows,
        "failure_examples": examples,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Diagnose a ReplenishVerifier experiment run.")
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--candidate_evaluations", required=True)
    parser.add_argument("--main_results", required=True)
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args(argv)
    diagnose_run(args.benchmark, args.candidate_evaluations, args.main_results, args.out_dir)


if __name__ == "__main__":
    main()
