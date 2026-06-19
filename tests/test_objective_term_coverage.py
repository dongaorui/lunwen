from types import SimpleNamespace

from replenishverifier.experiments.objective_terms import expected_objective_terms, evaluate_objective_terms


def test_expected_terms_by_problem_type():
    assert expected_objective_terms("single_period_newsvendor") == ["ordering_cost", "holding_cost", "shortage_cost"]
    assert expected_objective_terms("single_item_multi_period") == ["ordering_cost", "holding_cost"]
    assert expected_objective_terms("single_item_multi_period_shortage") == ["ordering_cost", "holding_cost", "shortage_cost"]
    assert expected_objective_terms("multi_item_capacity") == ["ordering_cost", "holding_cost"]
    assert expected_objective_terms("fixed_order_cost_big_m") == ["ordering_cost", "holding_cost", "fixed_order_cost"]


def test_detects_terms_from_generated_code_names():
    row = {"problem_type": "fixed_order_cost_big_m"}
    code = "model += unit_order_cost * Q[t] + holding_cost * I[t] + fixed_order_cost * Y[t]"

    result = evaluate_objective_terms(row, generated_code=code)

    assert result["expected_objective_terms"] == ["ordering_cost", "holding_cost", "fixed_order_cost"]
    assert result["detected_objective_terms"] == ["ordering_cost", "holding_cost", "fixed_order_cost"]
    assert result["missing_objective_terms"] == []
    assert result["objective_term_coverage"] == 1.0
    assert result["uses_reference_objective_for_objective_term_coverage"] is False


def test_missing_shortage_term_lowers_coverage():
    row = {"problem_type": "single_item_multi_period_shortage"}
    code = "model += order_cost * Q[t] + holding_cost * I[t]"

    result = evaluate_objective_terms(row, generated_code=code)

    assert result["detected_objective_terms"] == ["ordering_cost", "holding_cost"]
    assert result["missing_objective_terms"] == ["shortage_cost"]
    assert result["objective_term_coverage"] == 2 / 3


def test_surface_terms_do_not_prove_missing_lp_inventory_coefficients():
    row = {"problem_type": "single_item_multi_period"}
    code = "model += order_cost * Q[t] + holding_cost * I[t]"
    parsed = SimpleNamespace(objective={"Q_0": 2.0}, variable_names=["Q_0", "I_0"])

    result = evaluate_objective_terms(row, parsed=parsed, generated_code=code)

    assert result["objective_term_surface_coverage"] == 1.0
    assert result["objective_term_lp_coefficient_coverage"] == 0.5
    assert result["objective_term_coverage"] == 0.5
    assert result["lp_detected_objective_terms"] == ["ordering_cost"]
    assert result["lp_missing_objective_terms"] == ["holding_cost"]


def test_fixed_order_big_m_missing_binary_objective_coefficient_is_detected():
    row = {"problem_type": "fixed_order_cost_big_m"}
    code = "model += order_cost * Q[t] + holding_cost * I[t] + fixed_order_cost * Y[t]"
    parsed = SimpleNamespace(objective={"Q_0": 2.0, "I_0": 1.0}, variable_names=["Q_0", "I_0", "Y_0"])

    result = evaluate_objective_terms(row, parsed=parsed, generated_code=code)

    assert result["objective_term_surface_coverage"] == 1.0
    assert result["objective_term_lp_coefficient_coverage"] == 2 / 3
    assert result["objective_term_coverage"] == 2 / 3
    assert result["lp_missing_objective_terms"] == ["fixed_order_cost"]


def test_unknown_problem_type_returns_na_shape():
    result = evaluate_objective_terms({"problem_type": "unknown"}, generated_code="model += x")

    assert result["expected_objective_terms"] == []
    assert result["detected_objective_terms"] == []
    assert result["missing_objective_terms"] == []
    assert result["objective_term_coverage"] is None
