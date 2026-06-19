from replenishverifier.pipeline.quality_signals import compute_static_validation


def test_static_validation_accepts_runner_compatible_pulp_model():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("inventory", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", range(2), lowBound=0)
    inventory = pulp.LpVariable.dicts("inventory", range(2), lowBound=0)
    prob += 2 * order[0] + 3 * inventory[0], "total_cost"
    prob += inventory[0] == order[0] - 5, "inventory_balance_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="single_item_multi_period")

    assert result["has_build_model"] is True
    assert result["has_pulp_problem"] is True
    assert result["has_objective"] is True
    assert result["has_constraints"] is True
    assert result["has_inventory_balance_pattern"] is True
    assert result["static_validation_errors"] == []
    assert result["static_validation_score"] == 1.0


def test_static_validation_detects_capacity_shortage_big_m_and_fixed_cost_patterns():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("capacity", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", range(2), lowBound=0)
    shortage = pulp.LpVariable.dicts("shortage", range(2), lowBound=0)
    y = pulp.LpVariable.dicts("order_binary", range(2), cat="Binary")
    fixed_order_cost = 10
    big_m = 100
    prob += fixed_order_cost * y[0] + 4 * shortage[0], "total_cost"
    prob += order[0] <= 50, "capacity_constraint_0"
    prob += order[0] <= big_m * y[0], "big_m_link_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="fixed_order_cost_big_m")

    assert result["has_capacity_pattern"] is True
    assert result["has_shortage_pattern"] is True
    assert result["has_binary_order_pattern"] is True
    assert result["has_big_m_pattern"] is True
    assert result["has_fixed_order_cost_pattern"] is True


def test_static_validation_reports_missing_runner_contract():
    result = compute_static_validation("print('not a model')", problem_type="multi_item_capacity")

    assert result["has_build_model"] is False
    assert result["has_pulp_problem"] is False
    assert result["has_objective"] is False
    assert result["has_constraints"] is False
    assert "missing_build_model" in result["static_validation_errors"]
    assert "missing_pulp_lp_problem" in result["static_validation_errors"]
    assert result["static_validation_score"] < 0.5


def test_static_validation_reports_syntax_error():
    result = compute_static_validation("import pulp\ndef build_model(:", problem_type="single_period_newsvendor")

    assert "syntax_error" in result["static_validation_errors"]
    assert result["has_build_model"] is False
    assert result["static_validation_score"] == 0.0


def test_type_aware_static_validation_empty_checklist_is_neutral_for_newsvendor():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("newsvendor", pulp.LpMinimize)
    q = pulp.LpVariable("Q", lowBound=0)
    prob += q, "total_cost"
    prob += q >= 5, "demand_satisfaction"
    return prob
'''

    result = compute_static_validation(code, problem_type="single_period_newsvendor")

    validation = result["type_aware_static_validation"]
    assert validation["checklist"] == []
    assert validation["score"] == 1.0
    assert result["type_aware_static_validation_score"] == 1.0
    assert validation["hard_gate_failures"] == []
    assert validation["hard_gate_score"] == 1.0
    assert result["type_aware_static_validation_errors"] == []


def test_type_aware_static_validation_flags_missing_capacity_for_capacity_problem():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("cap", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", ((i, t) for i in range(2) for t in range(2)), lowBound=0)
    inventory = pulp.LpVariable.dicts("inventory", ((i, t) for i in range(2) for t in range(2)), lowBound=0)
    prob += order[(0, 0)] + inventory[(0, 0)], "total_cost"
    prob += inventory[(0, 0)] == order[(0, 0)] - 3, "inventory_balance_0_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="multi_item_capacity")

    assert "missing_capacity_constraint" in result["type_aware_static_validation_errors"]
    assert result["type_aware_static_validation"]["hard_gate_failures"] == ["missing_capacity_constraint"]
    assert result["type_aware_static_validation_score"] < 1.0


def test_type_aware_static_validation_flags_missing_shortage_cost():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("shortage", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", range(2), lowBound=0)
    inventory = pulp.LpVariable.dicts("inventory", range(2), lowBound=0)
    shortage = pulp.LpVariable.dicts("shortage", range(2), lowBound=0)
    prob += order[0] + inventory[0], "total_cost"
    prob += inventory[0] + shortage[0] == order[0] - 4, "inventory_shortage_balance_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="single_item_multi_period_shortage")

    assert "missing_shortage_cost_term" in result["type_aware_static_validation_errors"]
    assert "missing_shortage_variable" not in result["type_aware_static_validation_errors"]


def test_type_aware_static_validation_flags_fixed_order_big_m_failures():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("fixed", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", range(2), lowBound=0)
    inventory = pulp.LpVariable.dicts("inventory", range(2), lowBound=0)
    prob += order[0] + inventory[0], "total_cost"
    prob += inventory[0] == order[0] - 4, "inventory_balance_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="fixed_order_cost_big_m")

    errors = result["type_aware_static_validation_errors"]
    assert "missing_fixed_order_binary" in errors
    assert "missing_big_m_linking" in errors
    assert "missing_fixed_order_cost_term" in errors
    assert result["type_aware_static_validation"]["hard_gate_score"] < 1.0
