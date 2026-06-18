import argparse
from pathlib import Path

from replenishverifier.experiments.evaluation import count_feedback_items, mean, write_json
from replenishverifier.utils.io import read_jsonl


STRUCTURES_FOR_MISSING_RATE = [
    "inventory_balance",
    "big_m_constraint",
    "fixed_order_cost",
    "capacity_constraint",
]


def _row_key(row):
    return (row.get("problem_id"), row.get("source_candidate_id") or row.get("candidate_id"))


def _structure(row):
    return row.get("structure_verification") or {}


def _missing(row, key):
    structure = _structure(row)
    missing = set(structure.get("missing") or [])
    required = structure.get("required_structures")
    if required is None:
        expected = structure.get("expected") or {}
        required = [name for name, value in expected.items() if value]
    if required and key not in set(required):
        return 0.0
    return 1.0 if key in missing else 0.0


def summarize_repair_rows(rows):
    rows = list(rows)
    if not rows:
        out = {
            "n": 0,
            "objective_accuracy": 0.0,
            "structure_completeness": 0.0,
            "inventory_balance_accuracy": 0.0,
            "average_repair_feedback_count": 0.0,
        }
    else:
        inv_hits = []
        for row in rows:
            structure = _structure(row)
            expected = structure.get("expected") or {}
            detected = structure.get("detected") or {}
            if expected.get("inventory_balance"):
                inv_hits.append(1.0 if detected.get("inventory_balance") else 0.0)
        out = {
            "n": len(rows),
            "objective_accuracy": mean([float(row.get("objective_correct", 0.0) or 0.0) for row in rows]),
            "structure_completeness": mean([float(row.get("structure_score", _structure(row).get("structure_score", 0.0)) or 0.0) for row in rows]),
            "inventory_balance_accuracy": mean(inv_hits),
            "average_repair_feedback_count": mean([count_feedback_items(row) for row in rows]),
        }
    for key in STRUCTURES_FOR_MISSING_RATE:
        out[f"missing_{key}_rate"] = mean([_missing(row, key) for row in rows]) if rows else 0.0
    return out


def compare_repair_results(before_path, after_path, out_path=None):
    before_rows = read_jsonl(before_path)
    after_rows = read_jsonl(after_path)
    before_by_key = {_row_key(row): row for row in before_rows}
    paired_before = []
    paired_after = []
    for row in after_rows:
        key = _row_key(row)
        before = before_by_key.get(key)
        if before is not None:
            paired_before.append(before)
            paired_after.append(row)

    result = {
        "before_path": str(before_path),
        "after_path": str(after_path),
        "number_of_repaired_candidates": len(after_rows),
        "number_of_paired_candidates": len(paired_after),
        "before": summarize_repair_rows(paired_before),
        "after": summarize_repair_rows(paired_after),
        "note": "This script only compares evaluated candidate files. It does not generate or assume repair success.",
    }
    if out_path:
        write_json(out_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Compare evaluated candidates before and after real second-round repair.")
    parser.add_argument("--before", required=True, help="Before-repair candidate_evaluations.jsonl")
    parser.add_argument("--after", required=True, help="After-repair candidate_evaluations.jsonl")
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    args = parser.parse_args()
    result = compare_repair_results(args.before, args.after, args.out)
    if not args.out:
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
