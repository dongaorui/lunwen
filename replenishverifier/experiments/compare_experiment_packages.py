import argparse
import csv
import json
from pathlib import Path

from replenishverifier.utils.io import read_jsonl


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
    path = Path(path)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
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


def _objective_correct(row):
    try:
        return 1.0 if float(row.get("objective_correct", row.get("objective_accuracy", 0.0)) or 0.0) == 1.0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _load_selected_rows(exp_dir):
    path = Path(exp_dir) / "main_results.jsonl"
    return read_jsonl(path) if path.exists() else []


def _load_summary_rows(exp_dir):
    exp_dir = Path(exp_dir)
    for path in [exp_dir / "main_results_summary.jsonl", exp_dir / "reported_main_summary.jsonl"]:
        if path.exists():
            rows = read_jsonl(path)
            if rows:
                return rows
    for path in [exp_dir / "main_results.md", exp_dir / "summary.md"]:
        rows = _parse_markdown_table(path)
        if rows:
            return rows
    selected = _load_selected_rows(exp_dir)
    by_method = {}
    for row in selected:
        if not row.get("selected", True):
            continue
        method = row.get("method_name") or row.get("method")
        by_method.setdefault(method, []).append(row)
    summary = []
    for method, rows in sorted(by_method.items()):
        summary.append({
            "method": method,
            "n": len(rows),
            "objective_accuracy": sum(_objective_correct(row) for row in rows) / max(len(rows), 1),
        })
    return summary


def _write_csv(path, rows):
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
        writer.writerows(rows)


def _selected_changes(old_rows, new_rows):
    old_map = {(row.get("method_name") or row.get("method"), row.get("problem_id")): row for row in old_rows if row.get("selected", True)}
    new_map = {(row.get("method_name") or row.get("method"), row.get("problem_id")): row for row in new_rows if row.get("selected", True)}
    changes = []
    for key in sorted(set(old_map) & set(new_map)):
        old = old_map[key]
        new = new_map[key]
        if old.get("candidate_id") == new.get("candidate_id"):
            continue
        changes.append({
            "method": key[0],
            "problem_id": key[1],
            "old_candidate_id": old.get("candidate_id"),
            "new_candidate_id": new.get("candidate_id"),
            "old_objective_correct_posthoc_only": old.get("objective_correct"),
            "new_objective_correct_posthoc_only": new.get("objective_correct"),
            "posthoc_only": True,
        })
    return changes


def compare_experiment_packages(old_dir, new_dir, out_dir):
    old_dir = Path(old_dir)
    new_dir = Path(new_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    old_summary = {row.get("method") or row.get("method_name"): row for row in _load_summary_rows(old_dir)}
    new_summary = {row.get("method") or row.get("method_name"): row for row in _load_summary_rows(new_dir)}
    method_regressions = []
    for method in sorted(set(old_summary) & set(new_summary)):
        old_acc = _coerce_value(old_summary[method].get("objective_accuracy"))
        new_acc = _coerce_value(new_summary[method].get("objective_accuracy"))
        if old_acc is None or new_acc is None:
            continue
        delta = float(new_acc) - float(old_acc)
        method_regressions.append({
            "method": method,
            "old_objective_accuracy_posthoc_only": float(old_acc),
            "new_objective_accuracy_posthoc_only": float(new_acc),
            "objective_accuracy_delta": delta,
            "posthoc_only": True,
        })
    method_regressions.sort(key=lambda row: (row["objective_accuracy_delta"], row["method"]))

    changes = _selected_changes(_load_selected_rows(old_dir), _load_selected_rows(new_dir))
    _write_csv(out_dir / "method_regressions.csv", method_regressions)
    _write_csv(out_dir / "selected_candidate_changes.csv", changes)

    lines = [
        "# Regression Summary",
        "",
        "This report is posthoc_only diagnostics and must not be used for formal selection.",
        "",
        "## Objective accuracy deltas",
        "",
        "| method | old_objective_accuracy_posthoc_only | new_objective_accuracy_posthoc_only | objective_accuracy_delta | posthoc_only |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in method_regressions:
        lines.append(
            f"| {row['method']} | {row['old_objective_accuracy_posthoc_only']:.4f} | "
            f"{row['new_objective_accuracy_posthoc_only']:.4f} | {row['objective_accuracy_delta']:.4f} | True |"
        )
    lines.extend(["", "## Selected candidate changes", "", f"Changed selections: {len(changes)}", ""])
    (out_dir / "regression_summary.md").write_text("\n".join(lines), encoding="utf-8")
    result = {"method_regressions": method_regressions, "selected_candidate_changes": changes}
    (out_dir / "regression_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Compare two experiment package/run directories with posthoc-only diagnostics.")
    parser.add_argument("--old", required=True, dest="old_dir")
    parser.add_argument("--new", required=True, dest="new_dir")
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args()
    compare_experiment_packages(args.old_dir, args.new_dir, args.out_dir)


if __name__ == "__main__":
    main()
