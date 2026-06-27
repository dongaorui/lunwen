from replenishverifier.experiments.methods import (
    capacity_evidence_strength,
    formulation_awareness_score,
    select_for_method,
    select_typeaware_consensus,
    should_recover_tac_selection,
    solver_execution_feedback_score,
    variable_domain_correctness_score,
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


def test_select_for_method_preserves_tac_recovery_metadata_after_annotation():
    required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost"]
    rows = [
        _row("minority_k3", problem_type="fixed_order_cost_big_m", rank=3, required=required, missing=[], consensus=0.125),
        _row("majority_k4", problem_type="fixed_order_cost_big_m", rank=4, required=required, missing=[], consensus=0.875),
    ]
    benchmark = {"p0": {"problem_type": "fixed_order_cost_big_m"}}

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, benchmark)[0]

    assert selected["candidate_id"] == "majority_k4"
    assert selected["tac_recovery_decision"]["triggered"] is True
    assert selected["selection_components"]["tac_recovery_triggered"] is True
    assert selected["selection_components"]["tac_recovery_reason"] == "fixed_order_overwhelming_safe_consensus"


def test_tac_components_include_llmopt_no_reference_signals():
    row = _row(
        "c0",
        problem_type="fixed_order_cost_big_m",
        required=["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost", "nonnegative_bounds"],
        missing=[],
        generated_code="""
import pulp
periods = range(2)
demand = [3, 4]
model = pulp.LpProblem('fixed', pulp.LpMinimize)
Q = pulp.LpVariable.dicts('Q', periods, lowBound=0)
I = pulp.LpVariable.dicts('I', periods, lowBound=0)
Y = pulp.LpVariable.dicts('Y', periods, lowBound=0, upBound=1, cat='Binary')
model += pulp.lpSum(2 * Q[t] + I[t] + 5 * Y[t] for t in periods)
for t in periods:
    model += I[t] >= 0
    model += Q[t] <= 99 * Y[t]
""",
        text="Sets: periods. Parameters include demand and costs. Variables are order, inventory, binary trigger. Objective and constraints are required.",
    )

    selected = select_typeaware_consensus([row], {"problem_type": "fixed_order_cost_big_m"})
    components = selected["selection_components"]

    assert components["formulation_awareness_score"] == 1.0
    assert components["variable_domain_correctness_score"] == 1.0
    assert components["solver_execution_feedback_score"] == 1.0
    assert set(components["formulation_elements_present"]) == {"sets", "parameters", "variables", "objective", "constraints"}
    assert components["variable_domain_failures"] == []
    assert set(components).isdisjoint(FORBIDDEN_SELECTION_KEYS)


def test_variable_domain_correctness_penalizes_continuous_trigger_in_fixed_order_tac():
    required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost", "nonnegative_bounds"]
    bad = _row(
        "continuous_trigger_k0",
        problem_type="fixed_order_cost_big_m",
        rank=0,
        required=required,
        missing=[],
        consensus=0.90,
        generated_code="Y = pulp.LpVariable.dicts('Y', range(T), lowBound=0, upBound=1)\nQ = pulp.LpVariable.dicts('Q', range(T), lowBound=0)",
    )
    bad["lp_stats"]["binary_variables_count"] = 0
    good = _row(
        "binary_trigger_k1",
        problem_type="fixed_order_cost_big_m",
        rank=1,
        required=required,
        missing=[],
        consensus=0.50,
        generated_code="Y = pulp.LpVariable.dicts('Y', range(T), lowBound=0, upBound=1, cat='Binary')\nQ = pulp.LpVariable.dicts('Q', range(T), lowBound=0)",
    )
    good["lp_stats"]["binary_variables_count"] = 2

    assert variable_domain_correctness_score(bad) < variable_domain_correctness_score(good)
    selected = select_typeaware_consensus([bad, good], {"problem_type": "fixed_order_cost_big_m"})

    assert selected["candidate_id"] == "binary_trigger_k1"
    assert "binary_order_domain" in selected["selection_components"]["variable_domain_checks"]


def test_solver_feedback_penalizes_timeout_and_parse_error_even_with_high_consensus():
    bad = _row("timeout_k0", rank=0, consensus=0.99, text="warehouse capacity limits orders")
    bad["execution"] = {"executable": False, "status": "Timeout", "objective": None, "error": "solver timeout while optimizing"}
    bad["lp_stats"] = {"lp_exported": False, "objective_present": False, "constraints_count": 0, "variables_count": 0, "error": "LP parse failed"}
    good = _row("healthy_k1", rank=1, consensus=0.25, text="warehouse capacity limits orders")

    assert solver_execution_feedback_score(bad) < solver_execution_feedback_score(good)
    selected = select_typeaware_consensus([bad, good], {"problem_type": "multi_item_capacity"})

    assert selected["candidate_id"] == "healthy_k1"
    assert selected["selection_components"]["solver_execution_feedback_score"] == 1.0


def test_formulation_awareness_detects_missing_constraints_element():
    row = _row(
        "missing_constraints_k0",
        missing=["capacity_constraint"],
        generated_code="Q = pulp.LpVariable.dicts('Q', items, lowBound=0)\nmodel += pulp.lpSum(cost[i] * Q[i] for i in items)",
        text="Sets are items; parameters are costs; variables and objective are described.",
    )
    row["lp_stats"]["constraints_count"] = 0

    assert formulation_awareness_score(row) < 1.0
    selected = select_typeaware_consensus([row], {"problem_type": "multi_item_capacity"})

    assert selected["selection_components"]["formulation_awareness_score"] < 1.0
    assert "constraints" in selected["selection_components"]["formulation_elements_missing"]


def test_formulation_awareness_does_not_use_problem_prompt_as_candidate_evidence():
    row = _row(
        "prompt_only_k0",
        generated_code="",
        text="Sets, Parameters, Variables, Objective, and Constraints are all described in the user problem.",
    )
    row["generated_text"] = ""
    row["lp_stats"] = {"lp_exported": False, "objective_present": False, "constraints_count": 0, "variables_count": 0}

    selected = select_typeaware_consensus([row], {"problem_type": "multi_item_capacity"})

    assert selected["selection_components"]["formulation_awareness_score"] == 0.0
    assert set(selected["selection_components"]["formulation_elements_missing"]) == {"sets", "parameters", "variables", "objective", "constraints"}


def test_variable_domain_correctness_requires_positive_nonnegative_evidence():
    row = _row(
        "no_bounds_k0",
        problem_type="multi_item_capacity",
        required=["inventory_balance", "order_variable", "inventory_variable", "capacity_constraint"],
        missing=[],
        generated_code="Q = pulp.LpVariable.dicts('Q', items)",
    )
    row["lp_stats"]["bounds_present"] = False

    assert variable_domain_correctness_score(row) < 1.0


def test_fixed_order_tac_rank_stability_when_only_formulation_awareness_differs():
    required = ["inventory_balance", "order_variable", "binary_order_variable", "big_m_constraint", "fixed_order_cost", "nonnegative_bounds"]
    stable = _row(
        "stable_k0",
        problem_type="fixed_order_cost_big_m",
        rank=0,
        required=required,
        missing=[],
        consensus=0.40,
        generated_code="Y = pulp.LpVariable.dicts('Y', range(T), lowBound=0, upBound=1, cat='Binary')\nQ = pulp.LpVariable.dicts('Q', range(T), lowBound=0)",
    )
    stable["lp_stats"]["binary_variables_count"] = 2
    richer_description = _row(
        "richer_formulation_k3",
        problem_type="fixed_order_cost_big_m",
        rank=3,
        required=required,
        missing=[],
        consensus=0.40,
        generated_code="""
periods = range(T)
demand = [1, 2]
Y = pulp.LpVariable.dicts('Y', periods, lowBound=0, upBound=1, cat='Binary')
Q = pulp.LpVariable.dicts('Q', periods, lowBound=0)
model += pulp.lpSum(Q[t] + Y[t] for t in periods)
for t in periods:
    model += Q[t] <= M * Y[t]
""",
    )
    richer_description["lp_stats"]["binary_variables_count"] = 2

    selected = select_typeaware_consensus([stable, richer_description], {"problem_type": "fixed_order_cost_big_m"})

    assert selected["candidate_id"] == "stable_k0"
    assert selected["selection_components"]["tac_recovery_triggered"] is False
