import csv

from replenishverifier.experiments.diagnose_run import diagnose_run
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _eval_row(problem_id, candidate_id, *, objective_correct, structure_score, missing, objective=10.0, method="k"):
    return {
        "problem_id": problem_id,
        "candidate_id": candidate_id,
        "candidate_index": int(candidate_id[-1]),
        "problem_type": "multi_item_capacity",
        "method_name": method,
        "generated_code": "import pulp\n\ndef build_model():\n    pass\n",
        "execution": {"executable": True, "status": "Optimal", "objective": objective, "lp_path": "x.lp"},
        "objective_correct": 1.0 if objective_correct else 0.0,
        "structure_score": structure_score,
        "structure_verification": {
            "structure_score": structure_score,
            "required_structures": ["inventory_balance", "capacity_constraint"],
            "missing": missing,
            "detected": {
                "inventory_balance": "inventory_balance" not in missing,
                "capacity_constraint": "capacity_constraint" not in missing,
            },
        },
        "static_validation_errors": ["missing_build_model"] if candidate_id.endswith("0") else [],
        "feedback": "repair feedback",
        "reference_objective": 10.0,
    }


def test_diagnose_run_writes_expected_outputs_and_oracle_fields(tmp_path):
    benchmark = tmp_path / "benchmark.jsonl"
    evaluations = tmp_path / "candidate_evaluations.jsonl"
    main = tmp_path / "main_results.jsonl"
    out_dir = tmp_path / "diagnostics"

    write_jsonl(benchmark, [{"id": "p0", "problem_type": "multi_item_capacity", "reference_objective": 10.0}])
    write_jsonl(evaluations, [
        _eval_row("p0", "c0", objective_correct=False, structure_score=0.5, missing=["capacity_constraint"], objective=99.0),
        _eval_row("p0", "c1", objective_correct=True, structure_score=1.0, missing=[], objective=10.0),
    ])
    selected = _eval_row("p0", "c0", objective_correct=False, structure_score=0.5, missing=["capacity_constraint"], objective=99.0)
    selected["method_name"] = "ReplenishVerifier-Full"
    write_jsonl(main, [selected])

    result = diagnose_run(benchmark, evaluations, main, out_dir)

    for name in [
        "problem_diagnostics.jsonl",
        "problem_type_summary.csv",
        "candidate_diversity.csv",
        "missing_structure_distribution.csv",
        "failure_examples.jsonl",
        "summary.md",
    ]:
        assert (out_dir / name).exists()

    diagnostic = read_jsonl(out_dir / "problem_diagnostics.jsonl")[0]
    assert diagnostic["any_candidate_objective_correct"] is True
    assert diagnostic["selector_missed_oracle_objective"] is True
    assert diagnostic["selected_missing_structures"] == ["capacity_constraint"]
    assert diagnostic["unique_objective_value_count"] == 2

    examples = read_jsonl(out_dir / "failure_examples.jsonl")
    assert examples[0]["reference_objective"] == 10.0
    assert examples[0]["generated_code_excerpt"].startswith("import pulp")

    with (out_dir / "problem_type_summary.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["problem_type"] == "multi_item_capacity"
    assert float(rows[0]["objective_accuracy"]) == 0.0
    assert result["problem_diagnostics"][0]["selector_missed_oracle_structure"] is True
