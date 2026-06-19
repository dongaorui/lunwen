import argparse
import json
import sys
from pathlib import Path

from replenishverifier.utils.io import read_jsonl


FORMAL_METHODS = {
    "Direct",
    "Best-of-K",
    "Solver-Filter",
    "Solver only",
    "Structure only",
    "Consensus only",
    "Solver + Structure",
    "Solver + Consensus",
    "Structure + Consensus",
    "Solver + Structure + Consensus",
    "ReplenishVerifier full",
    "OR-R1-like Voting",
    "Structure-Grounded Consistency",
    "SIRL-like LP-Stats",
    "OptArgus-like Audit",
    "OptiRepair-like Repair-Prompt",
    "Structure-Only",
    "ReplenishVerifier-TypeAware",
    "ReplenishVerifier-TypeAware-Consensus",
    "ReplenishVerifier-Full",
    "ReplenishVerifier-Repair",
}

FORBIDDEN_POLICY_PHRASES = [
    "closest to reference",
    "reference_objective",
    "reference objective distance",
    "objective closeness to reference",
    "objective_correct",
    "minimize relative error",
    "ground truth objective",
    "oracle",
]

FORBIDDEN_SELECTION_COMPONENT_KEYS = {
    "reference_objective",
    "objective_correct",
    "objective_accuracy",
    "objective_score",
    "relative_error",
    "reference_lp",
    "reference_answer",
    "objective_gap",
    "oracle",
    "objective_correct_posthoc",
}


def is_posthoc_metric_row(row):
    return row.get("formal_selection_metric") is False or row.get("uses_reference_for_oracle_metrics") is True


def _audit_rows(rows, source_name, require_selected=False):
    issues = []
    for idx, row in enumerate(rows):
        if require_selected and not row.get("selected"):
            continue
        if not require_selected and is_posthoc_metric_row(row):
            continue
        method = row.get("method_name") or row.get("method")
        policy = str(row.get("selection_policy", "")).lower()
        if method in FORMAL_METHODS:
            if row.get("uses_reference_objective_for_selection") is not False:
                issues.append(
                    f"{source_name} row {idx} method={method} uses_reference_objective_for_selection "
                    "must be explicitly False."
                )
            if "reference objective" not in policy or "no reference" not in policy:
                issues.append(f"{source_name} row {idx} method={method} selection_policy is missing no-reference statement: {row.get('selection_policy')}")
            if row.get("selection_score") != row.get("score"):
                issues.append(f"{source_name} row {idx} method={method} score and selection_score differ unexpectedly.")
            if row.get("uses_reference_for_oracle_metrics") is True and row.get("formal_selection_metric") is not False:
                issues.append(f"{source_name} row {idx} method={method} mixes oracle reference metrics into a formal selection row.")
            for phrase in FORBIDDEN_POLICY_PHRASES:
                if phrase in policy and "no reference objective" not in policy:
                    issues.append(f"{source_name} row {idx} method={method} policy contains forbidden reference signal: {phrase}")
            components = row.get("selection_components") or {}
            if isinstance(components, dict):
                bad_keys = sorted(set(components) & FORBIDDEN_SELECTION_COMPONENT_KEYS)
                if bad_keys:
                    issues.append(f"{source_name} row {idx} method={method} selection_components contain forbidden reference/oracle keys: {bad_keys}")

        if "objective_accuracy" in row or "objective_correct" in row or "objective_score" in row:
            if method in FORMAL_METHODS and "no reference" not in policy:
                issues.append(f"{source_name} row {idx} method={method} stores objective metrics without no-reference selection policy.")

    return issues


def audit(exp_dir, write_report=False):
    exp_dir = Path(exp_dir)
    issues = []
    checked_files = []

    main_path = exp_dir / "main_results.jsonl"
    rows = read_jsonl(main_path)
    if not rows:
        issues.append(f"No main_results rows found at {main_path}")
    else:
        checked_files.append(str(main_path))
        issues.extend(_audit_rows(rows, "main_results", require_selected=True))

    candidate_path = exp_dir / "candidate_evaluations.jsonl"
    candidate_rows = read_jsonl(candidate_path)
    if candidate_rows:
        checked_files.append(str(candidate_path))
        # Candidate evaluations can contain objective metrics, but should not
        # claim a reference-based selection policy.
        for idx, row in enumerate(candidate_rows):
            policy = str(row.get("selection_policy", "")).lower()
            for phrase in FORBIDDEN_POLICY_PHRASES:
                if phrase in policy:
                    issues.append(f"candidate_evaluations row {idx} policy contains forbidden phrase: {phrase}")

    expected = [
        "main_results.jsonl",
        "candidate_evaluations.jsonl",
        "ablation_results.jsonl",
        "low_resource_results.jsonl",
        "summary.md",
    ]
    for name in expected:
        if not (exp_dir / name).exists():
            issues.append(f"Missing expected output file: {exp_dir / name}")

    report = {
        "exp_dir": str(exp_dir),
        "checked_files": checked_files,
        "formal_methods": sorted(FORMAL_METHODS),
        "forbidden_policy_phrases": FORBIDDEN_POLICY_PHRASES,
        "passed": not issues,
        "issues": issues,
    }
    if write_report:
        (exp_dir / "no_leakage_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return issues


def main():
    parser = argparse.ArgumentParser(description="Audit experiment outputs for ground-truth objective leakage in formal candidate selection.")
    parser.add_argument("--exp_dir", required=True)
    parser.add_argument("--write_report", action="store_true", help="Write no_leakage_audit.json into exp_dir.")
    args = parser.parse_args()

    issues = audit(args.exp_dir, write_report=args.write_report)
    if issues:
        print("LEAKAGE AUDIT FAILED")
        for issue in issues:
            print(f"WARNING: {issue}")
        sys.exit(1)
    print("LEAKAGE AUDIT PASSED: no reference_objective usage detected in formal selection scores.")


if __name__ == "__main__":
    main()
