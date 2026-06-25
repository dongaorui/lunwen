from replenishverifier.experiments.methods import (
    capacity_evidence_strength,
    select_typeaware_consensus,
    should_recover_tac_selection,
)


FORBIDDEN_SELECTION_KEYS = {
    "reference_objective",
    "objective_correct",
    "objective_accuracy",
    "relative_error",
    "oracle",
    "oracle_rank",
    "reference_lp",
    "reference_answer",
}


def _row(
    candidate_id,
    *,
    problem_type="multi_item_capacity",
    rank=0,
    objective=10.0,
    executable=True,
    status="Optimal",
    structure_score=0.8,
    required=None,
    missing=None,
    consensus=0.5,
    objective_terms=1.0,
    generated_code="",
    text="",
):
    required = required or ["inventory_balance", "order_variable", "inventory_variable", "capacity_constraint"]
    missing = missing or []
    certificates = [
        {"rule_name": rule, "score": 0.0 if rule in missing else 1.0}
        for rule in required
    ]
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "candidate_index": rank,
        "problem_type": problem_type,
        "natural_language": text,
        "generated_code": generated_code,
        "execution": {
            "executable": executable,
            "status": status,
            "objective": objective,
            "lp_path": f"{candidate_id}.lp" if executable else None,
        },
        "structure_score": structure_score,
        "structure_verification": {
            "structure_score": structure_score,
            "required_structures": required,
            "missing": missing,
            "certificates": certificates,
        },
        "objective_consensus_score": consensus,
        "objective_term_coverage": objective_terms,
        "objective_term_lp_coefficient_coverage": objective_terms,
        "lp_stats": {"lp_exported": executable, "objective_present": objective is not None, "constraints_count": 4, "variables_count": 4},
        "code_output_format_valid": True,
        "static_validation_score": 1.0,
        "type_aware_static_validation": {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []},
        "type_aware_static_validation_errors": [],
    }


def test_tac_selection_components_exclude_reference_and_oracle_keys():
    row = _row("model_k0", missing=[], consensus=1.0)
    row.update({
        "reference_objective": 10.0,
        "objective_correct": 0.0,
        "relative_error": 99.0,
        "oracle_rank": 0,
        "reference_lp": "do-not-use",
        "reference_answer": "do-not-use",
    })

    selected = select_typeaware_consensus([row], {"problem_type": "multi_item_capacity"})

    assert set(selected["selection_components"]).isdisjoint(FORBIDDEN_SELECTION_KEYS)
    assert selected["selection_components"]["tac_recovery_triggered"] is False


def test_tac_selects_schema_complete_candidate_in_two_synthetic_pools():
    capacity_rows = [
        _row("bad_k0", rank=0, missing=["capacity_constraint"], consensus=0.95, text="warehouse capacity limits all products"),
        _row("good_k7", rank=7, missing=[], consensus=0.40, text="warehouse capacity limits all products"),
    ]
    fixed_required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost"]
    fixed_rows = [
        _row("bad_fixed_k0", problem_type="fixed_order_cost_big_m", rank=0, required=fixed_required, missing=["big_m_constraint"], consensus=0.95),
        _row("good_fixed_k6", problem_type="fixed_order_cost_big_m", rank=6, required=fixed_required, missing=[], consensus=0.40),
    ]

    capacity_selected = select_typeaware_consensus(capacity_rows, {"problem_type": "multi_item_capacity"})
    fixed_selected = select_typeaware_consensus(fixed_rows, {"problem_type": "fixed_order_cost_big_m"})

    assert capacity_selected["candidate_id"] == "good_k7"
    assert fixed_selected["candidate_id"] == "good_fixed_k6"


def test_tac_does_not_choose_by_early_candidate_rank_when_schema_differs():
    fixed_required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost"]
    rows = [
        _row("early_bad_k0", problem_type="fixed_order_cost_big_m", rank=0, required=fixed_required, missing=["fixed_order_cost"], consensus=0.99),
        _row("late_good_k7", problem_type="fixed_order_cost_big_m", rank=7, required=fixed_required, missing=[], consensus=0.50),
    ]

    selected = select_typeaware_consensus(rows, {"problem_type": "fixed_order_cost_big_m"})

    assert selected["candidate_id"] == "late_good_k7"
    assert selected["candidate_index"] == 7


def test_tac_fallback_is_stable_when_pool_has_no_valid_candidate():
    rows = [
        _row("failed_k0", rank=0, executable=False, status="Error", objective=None, missing=["capacity_constraint"], consensus=0.5),
        _row("failed_k1", rank=1, executable=False, status="Error", objective=None, missing=[], consensus=0.5),
    ]

    selected_once = select_typeaware_consensus(rows, {"problem_type": "multi_item_capacity"})
    selected_twice = select_typeaware_consensus(list(reversed(rows)), {"problem_type": "multi_item_capacity"})

    assert selected_once["candidate_id"] == selected_twice["candidate_id"] == "failed_k1"
    assert selected_once["selection_components"]["execution_success"] == 0.0


def test_tac_hard_profile_enabled_only_by_matching_type_or_unknown_text_trigger():
    ordinary = _row(
        "ordinary_k0",
        problem_type="single_item_multi_period",
        missing=[],
        text="This ordinary single-item problem mentions warehouse capacity only in prose.",
    )
    unknown_capacity = _row(
        "unknown_k0",
        problem_type=None,
        missing=["capacity_constraint"],
        text="Warehouse capacity limits shared product orders.",
    )
    ordinary_selected = select_typeaware_consensus([ordinary], {"problem_type": "single_item_multi_period"})
    unknown_selected = select_typeaware_consensus([unknown_capacity], {})

    assert ordinary_selected["selection_components"]["tac_priority_profile"] == "single_item_multi_period"
    assert unknown_selected["selection_components"]["tac_priority_profile"] == "multi_item_capacity"


def test_capacity_evidence_strength_distinguishes_keyword_from_shared_aggregation():
    no_evidence = _row("c0", generated_code="x = order[i]", text="plain replenishment")
    keyword_only = _row("c1", generated_code="# capacity is relevant\nx = order[i]", text="warehouse capacity matters", missing=["capacity_constraint"])
    shared_aggregation = _row(
        "c2",
        generated_code="model += pulp.lpSum(volume[i] * order[i] for i in items) <= warehouse_capacity",
        text="warehouse capacity matters",
    )

    assert capacity_evidence_strength(no_evidence) == 2  # schema certificate says capacity is present
    no_evidence["structure_verification"]["missing"] = ["capacity_constraint"]
    for cert in no_evidence["structure_verification"]["certificates"]:
        if cert["rule_name"] == "capacity_constraint":
            cert["score"] = 0.0
    assert capacity_evidence_strength(no_evidence) == 0
    assert capacity_evidence_strength(keyword_only) == 1
    assert capacity_evidence_strength(shared_aggregation) == 2


def test_conservative_recovery_requires_solver_and_schema_complete_challenger():
    initial = _row("initial", missing=["capacity_constraint"], consensus=0.90, objective_terms=1.0, text="warehouse capacity limits orders")
    challenger = _row("challenger", missing=[], consensus=0.40, objective_terms=0.9, text="warehouse capacity limits orders")
    failed_challenger = _row("failed", executable=False, status="Error", objective=None, missing=[], consensus=0.9, text="warehouse capacity limits orders")

    assert should_recover_tac_selection(initial, challenger, "multi_item_capacity") is True
    assert should_recover_tac_selection(initial, failed_challenger, "multi_item_capacity") is False
    assert should_recover_tac_selection(challenger, initial, "multi_item_capacity") is False


def test_fixed_order_tac_recovers_when_schema_safe_challenger_has_overwhelming_consensus():
    required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost"]
    rows = [
        _row("minority_k3", problem_type="fixed_order_cost_big_m", rank=3, required=required, missing=[], consensus=0.125),
        _row("majority_k4", problem_type="fixed_order_cost_big_m", rank=4, required=required, missing=[], consensus=0.875),
    ]

    selected = select_typeaware_consensus(rows, {"problem_type": "fixed_order_cost_big_m"})

    assert selected["candidate_id"] == "majority_k4"
    assert selected["selection_components"]["tac_recovery_triggered"] is True
    assert selected["selection_components"]["tac_recovery_reason"] == "fixed_order_overwhelming_safe_consensus"


def test_fixed_order_tac_keeps_stable_rank_when_consensus_gain_is_only_moderate():
    required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost"]
    rows = [
        _row("stable_k0", problem_type="fixed_order_cost_big_m", rank=0, required=required, missing=[], consensus=0.375),
        _row("moderate_consensus_k3", problem_type="fixed_order_cost_big_m", rank=3, required=required, missing=[], consensus=0.50),
    ]

    selected = select_typeaware_consensus(rows, {"problem_type": "fixed_order_cost_big_m"})

    assert selected["candidate_id"] == "stable_k0"
    assert selected["selection_components"]["tac_recovery_triggered"] is False
