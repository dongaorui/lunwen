from replenishverifier.experiments.audit_leakage import _audit_rows
from replenishverifier.experiments.build_preference_data import build_preference_pairs
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _row(candidate_id, reference_objective, structure_score, missing, executable=True, status="Optimal"):
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "generated_code": f"# {candidate_id}",
        "generated_text": f"text {candidate_id}",
        "prompt_type": "hidden_verifier",
        "problem_type": "fixed_order_cost_big_m",
        "difficulty": "hard",
        "reference_objective": reference_objective,
        "execution": {"executable": executable, "status": status, "objective": 10.0},
        "structure_score": structure_score,
        "structure_verification": {
            "missing": missing,
            "certificates": [
                {"rule_name": "inventory_balance", "required": True, "passed": "inventory_balance" not in missing, "score": structure_score, "evidence_strength": "strong" if structure_score == 1.0 else "none"}
            ],
        },
    }


def test_preference_pairs_include_metadata_and_no_reference_flag(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [
        _row("good", reference_objective=999.0, structure_score=1.0, missing=[]),
        _row("bad", reference_objective=1.0, structure_score=0.0, missing=["inventory_balance"]),
    ])
    out = exp_dir / "preference_pairs.jsonl"

    pairs = build_preference_pairs(exp_dir, out, min_score_gap=0.01, max_pairs_per_problem=1)

    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["chosen_candidate_id"] == "good"
    assert pair["rejected_candidate_id"] == "bad"
    assert pair["uses_reference_objective_for_preference"] is False
    assert pair["preference_source"] == "replenishment_structure_verifier"
    assert pair["metadata"]["uses_reference_objective_for_preference"] is False
    assert pair["metadata"]["candidate_ids"] == {"chosen": "good", "rejected": "bad"}
    assert pair["chosen_missing_structures"] == []
    assert pair["rejected_missing_structures"] == ["inventory_balance"]
    assert pair["chosen_execution_status"] == "Optimal"
    assert pair["rejected_execution_status"] == "Optimal"
    assert pair["chosen_structure_certificate_summary"]
    assert pair["rejected_structure_certificate_summary"]
    saved = read_jsonl(out)
    assert saved[0]["metadata"]["problem_type"] == "fixed_order_cost_big_m"


def test_preference_construction_ignores_reference_objective_values(tmp_path):
    exp_a = tmp_path / "a"
    exp_b = tmp_path / "b"
    exp_a.mkdir()
    exp_b.mkdir()
    rows_a = [
        _row("good", reference_objective=999.0, structure_score=1.0, missing=[]),
        _row("bad", reference_objective=1.0, structure_score=0.0, missing=["inventory_balance"]),
    ]
    rows_b = [
        _row("good", reference_objective=1.0, structure_score=1.0, missing=[]),
        _row("bad", reference_objective=999.0, structure_score=0.0, missing=["inventory_balance"]),
    ]
    write_jsonl(exp_a / "candidate_evaluations.jsonl", rows_a)
    write_jsonl(exp_b / "candidate_evaluations.jsonl", rows_b)

    pairs_a = build_preference_pairs(exp_a, exp_a / "pairs.jsonl", min_score_gap=0.01, max_pairs_per_problem=1)
    pairs_b = build_preference_pairs(exp_b, exp_b / "pairs.jsonl", min_score_gap=0.01, max_pairs_per_problem=1)

    assert [(p["chosen_candidate_id"], p["rejected_candidate_id"]) for p in pairs_a] == [("good", "bad")]
    assert [(p["chosen_candidate_id"], p["rejected_candidate_id"]) for p in pairs_b] == [("good", "bad")]


def test_no_reference_leakage_audit_still_passes_formal_selection_row():
    rows = [{
        "method_name": "ReplenishVerifier-Full",
        "selected": True,
        "uses_reference_objective_for_selection": False,
        "selection_policy": "Hard Selection Gate over structure signals; no reference objective",
        "score": 1.0,
        "selection_score": 1.0,
        "objective_correct": 0.0,
    }]
    assert _audit_rows(rows, "unit", require_selected=True) == []
