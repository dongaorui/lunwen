from replenishverifier.experiments.methods import select_for_method


def _row(candidate_id, *, problem_type="multi_item_capacity", score=0.5, structure_score=0.5, missing=None, consensus=0.0, feedback=""):
    structure = {
        "structure_score": structure_score,
        "required_structures": ["inventory_balance", "capacity_constraint"],
        "missing": missing or [],
        "certificates": [
            {"rule_name": "inventory_balance", "score": 0.0 if "inventory_balance" in (missing or []) else 1.0},
            {"rule_name": "capacity_constraint", "score": 0.0 if "capacity_constraint" in (missing or []) else 1.0},
        ],
    }
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "candidate_index": int(str(candidate_id).replace("c", "")),
        "problem_type": problem_type,
        "execution": {"executable": True, "status": "Optimal", "objective": 10.0 + int(str(candidate_id).replace("c", ""))},
        "score": score,
        "raw_inference_score": score,
        "structure_score": structure_score,
        "structure_only_score": structure_score,
        "structure_verification": structure,
        "objective_consensus_score": consensus,
        "static_validation_score": 1.0,
        "feedback": feedback,
    }


def _benchmark(problem_type="multi_item_capacity"):
    return {"p0": {"id": "p0", "problem_type": problem_type}}


def test_direct_still_selects_first_candidate():
    rows = [
        _row("c0", structure_score=0.1, missing=["capacity_constraint"]),
        _row("c1", structure_score=1.0, missing=[]),
    ]

    selected = select_for_method("Direct", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c0"


def test_best_of_k_uses_no_reference_tie_breaker_not_first_viable():
    rows = [
        _row("c0", structure_score=0.2, missing=["capacity_constraint"]),
        _row("c1", structure_score=0.9, missing=[]),
    ]

    selected = select_for_method("Best-of-K", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"


def test_structure_aware_selection_penalizes_critical_missing_structure_over_consensus():
    rows = [
        _row("c0", score=0.95, structure_score=0.8, missing=["capacity_constraint"], consensus=1.0),
        _row("c1", score=0.60, structure_score=0.7, missing=[], consensus=0.0),
    ]

    selected = select_for_method("ReplenishVerifier-Full", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["critical_structure_penalty"]["passed"] is True


def test_generic_or_r1_does_not_apply_replenishment_critical_penalty():
    rows = [
        _row("c0", structure_score=0.1, missing=["capacity_constraint"], consensus=1.0),
        _row("c1", structure_score=1.0, missing=[], consensus=0.0),
    ]
    rows[0]["or_r1_like_voting_score"] = 0.9
    rows[1]["or_r1_like_voting_score"] = 0.4

    selected = select_for_method("OR-R1-like Voting", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c0"
    assert "critical_structure_penalty" not in selected[0]
