from replenishverifier.experiments.methods import MAIN_METHODS, select_for_method


FORBIDDEN_COMPONENT_KEYS = {
    "reference_objective",
    "objective_correct",
    "objective_accuracy",
    "relative_error",
    "oracle",
    "oracle_rank",
    "reference_lp",
    "reference_answer",
}


def _row(candidate_id, *, objective=10.0, structure=0.8, consensus=0.0, type_score=1.0, missing=None, executable=True, status="Optimal"):
    idx = int(candidate_id.replace("c", ""))
    missing = missing or []
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "candidate_index": idx,
        "problem_type": "multi_item_capacity",
        "execution": {"executable": executable, "status": status, "objective": objective, "lp_path": f"{candidate_id}.lp" if executable else None},
        "score": 0.5,
        "raw_inference_score": 0.5,
        "base_replenishverifier_score": 0.5,
        "structure_score": structure,
        "structure_only_score": structure,
        "objective_consensus_score": consensus,
        "objective_term_coverage": 1.0,
        "lp_stats": {"lp_exported": executable, "objective_present": objective is not None, "constraints_count": 4, "variables_count": 4},
        "code_output_format_valid": executable,
        "static_validation_score": 1.0 if executable else 0.0,
        "type_aware_static_validation": {
            "score": type_score,
            "hard_gate_score": type_score,
            "hard_gate_failures": [] if type_score >= 1.0 else ["weak"],
            "missing_items": [] if type_score >= 1.0 else ["weak"],
        },
        "type_aware_static_validation_errors": [] if type_score >= 1.0 else ["weak"],
        "feedback": "",
        "structure_verification": {
            "structure_score": structure,
            "required_structures": ["inventory_balance", "capacity_constraint"],
            "missing": missing,
            "certificates": [
                {"rule_name": "inventory_balance", "score": 0.0 if "inventory_balance" in missing else 1.0},
                {"rule_name": "capacity_constraint", "score": 0.0 if "capacity_constraint" in missing else 1.0},
            ],
        },
        "reference_objective": 12345.0,
        "objective_correct": 0.0,
        "relative_error": 999.0,
    }


def _benchmark():
    return {"p0": {"id": "p0", "problem_type": "multi_item_capacity"}}


def _select(method, rows):
    return select_for_method(method, {"p0": rows}, _benchmark())[0]


def test_hybrid_safe_is_registered_as_main_method():
    assert "ReplenishVerifier-HybridSafe" in MAIN_METHODS


def test_hybrid_safe_components_are_no_reference_and_explain_votes():
    rows = [
        _row("c0", objective=10.0, structure=0.9, consensus=0.2),
        _row("c1", objective=20.0, structure=0.8, consensus=0.6),
    ]

    selected = _select("ReplenishVerifier-HybridSafe", rows)
    components = selected["selection_components"]

    assert components["selector_family"] == "hybrid_safe"
    assert components["method_vote_count"] >= 0.0
    assert "selected_by_bestofk_feature" in components
    assert set(components).isdisjoint(FORBIDDEN_COMPONENT_KEYS)
    assert selected["uses_reference_objective_for_selection"] is False


def test_hybrid_safe_is_not_best_of_k_alias_when_votes_disagree():
    rows = [
        _row("c0", objective=10.0, structure=1.0, consensus=0.1, type_score=1.0),
        _row("c1", objective=20.0, structure=0.9, consensus=0.8, type_score=1.0),
    ]

    best = _select("Best-of-K", rows)
    hybrid = _select("ReplenishVerifier-HybridSafe", rows)

    assert best["candidate_id"] == "c0"
    assert hybrid["candidate_id"] == "c1"


def test_hybrid_safe_is_not_type_aware_consensus_alias_when_safety_breaks_tie():
    rows = [
        _row("c0", objective=10.0, structure=0.95, consensus=0.7, type_score=1.0, missing=[]),
        _row("c1", objective=10.000001, structure=0.90, consensus=0.7, type_score=1.0, missing=["capacity_constraint"]),
    ]
    rows[1]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 1, "variables_count": 4}

    type_consensus = _select("ReplenishVerifier-TypeAware-Consensus", rows)
    hybrid = _select("ReplenishVerifier-HybridSafe", rows)

    assert type_consensus["candidate_id"] in {"c0", "c1"}
    assert hybrid["candidate_id"] == "c0"
    assert hybrid["selection_components"]["critical_missing_count"] == 0.0


def test_hybrid_safe_all_failed_fallback_does_not_crash():
    rows = [
        _row("c0", executable=False, status="Error", objective=None, structure=0.0, consensus=0.0),
        _row("c1", executable=False, status="Error", objective=None, structure=0.0, consensus=0.0),
    ]

    selected = _select("ReplenishVerifier-HybridSafe", rows)

    assert selected["candidate_id"] in {"c0", "c1"}
    assert selected["score"] == 0.0
    assert selected["selection_components"]["selector_family"] == "hybrid_safe"
