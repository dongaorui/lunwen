import pytest

from replenishverifier.verifier.feedback import generate_feedback
from replenishverifier.verifier.lp_parser import parse_lp_text
from replenishverifier.verifier.structure_rules import (
    check_big_m_magnitude,
    check_inventory_balance_index_consistency,
    check_structures,
)


def _cert(result, rule):
    return {item["rule_name"]: item for item in result.certificates}[rule]


def test_structure_detection():
    text = """
Minimize
OBJ: 2 Q_0 + 3 I_0 + 10 Y_0
Subject To
inventory_balance_0: I_0 - Q_0 + demand_0 = 0
big_m_0: Q_0 - 100 Y_0 <= 0
Binaries
Y_0
End
"""
    parsed = parse_lp_text(text)
    expected = {
        "inventory_balance": True,
        "order_variable": True,
        "inventory_variable": True,
        "shortage_variable": False,
        "capacity_constraint": False,
        "binary_order_variable": True,
        "big_m_constraint": True,
        "lead_time": False,
        "holding_cost": True,
        "shortage_cost": False,
        "fixed_order_cost": True,
    }
    result = check_structures(parsed, expected)
    assert result.structure_score >= 0.75
    assert not result.missing
    assert result.certificates
    assert _cert(result, "inventory_balance")["evidence_strength"] in {"expression_supported", "strong"}
    assert _cert(result, "big_m_constraint")["passed"] is True
    assert _cert(result, "big_m_constraint")["magnitude_check"]["candidate_M"] == 100.0
    assert _cert(result, "fixed_order_cost")["evidence"]
    assert result.weak_evidence["big_m_like_constraints"]["found"] is True
    assert result.weak_evidence["fixed_cost_binary_terms"]["found"] is True


def test_structure_detection_with_descriptive_variable_names():
    text = """
Minimize
OBJ: 2 order_qty_0 + 3 ending_inventory_0 + 10 setup_0
Subject To
stock_flow_0: ending_inventory_0 - order_qty_0 + demand_0 = 0
setup_link_0: order_qty_0 - 100 setup_0 <= 0
Binaries
setup_0
End
"""
    parsed = parse_lp_text(text)
    expected = {
        "inventory_balance": True,
        "order_variable": True,
        "inventory_variable": True,
        "shortage_variable": False,
        "capacity_constraint": False,
        "binary_order_variable": True,
        "big_m_constraint": True,
        "lead_time": False,
        "holding_cost": True,
        "shortage_cost": False,
        "fixed_order_cost": True,
    }
    result = check_structures(parsed, expected)
    assert result.structure_score >= 0.75
    assert not result.missing
    assert _cert(result, "order_variable")["passed"] is True
    assert _cert(result, "fixed_order_cost")["evidence"]
    assert result.weak_evidence["inventory_recurrence_candidates"]["found"] is True


def test_name_only_inventory_balance_is_weak_evidence():
    text = """
Minimize
OBJ: Q_0 + I_0
Subject To
inventory_balance_0: Q_0 >= 0
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, {"inventory_balance": True})
    cert = _cert(result, "inventory_balance")
    assert cert["evidence_strength"] == "name_only"
    assert cert["score"] <= 0.4
    assert cert["passed"] is False
    assert "inventory_balance" in result.missing


def test_inventory_balance_index_consistency_detects_adjacent_and_repeated():
    good = check_inventory_balance_index_consistency("I_1 - I_0 - Q_1 + D_1 = 0", ["I_0", "I_1"])
    assert good["passed"] is True
    assert "adjacent_inventory_periods_detected" in good["evidence"]

    bad = check_inventory_balance_index_consistency("I_1 - I_1 - Q_1 + D_1 = 0", ["I_1"])
    assert bad["passed"] is False
    assert any("same_inventory_variable_repeated" in warning for warning in bad["warnings"])


def test_big_m_name_only_is_weak_but_linking_expression_is_strong():
    name_only = parse_lp_text(
        """
Minimize
OBJ: Q_0 + Y_0
Subject To
big_m_0: Q_0 >= 0
Binaries
Y_0
End
"""
    )
    result = check_structures(name_only, {"big_m_constraint": True})
    assert _cert(result, "big_m_constraint")["score"] <= 0.4
    assert "big_m_constraint" in result.missing

    linked = parse_lp_text(
        """
Minimize
OBJ: Q_0 + Y_0
Subject To
link_0: Q_0 - 1000 Y_0 <= 0
Binaries
Y_0
End
"""
    )
    result = check_structures(linked, {"big_m_constraint": True})
    cert = _cert(result, "big_m_constraint")
    assert cert["passed"] is True
    assert cert["magnitude_check"]["has_large_coefficient"] is True


def test_fixed_order_cost_requires_binary_in_objective():
    text = """
Minimize
OBJ: Q_0
Subject To
link_0: Q_0 - 100 Y_0 <= 0
Binaries
Y_0
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, {"fixed_order_cost": True})
    cert = _cert(result, "fixed_order_cost")
    assert cert["passed"] is False
    assert cert["evidence_strength"] == "none"


def test_big_m_magnitude_small_m_warns_without_failing_parser():
    check = check_big_m_magnitude("Q_0 - 2 Y_0 <= 0")
    assert check["candidate_M"] == 2.0
    assert check["warning"]


def test_newsvendor_schema_does_not_require_big_m_or_capacity():
    text = """
Minimize
OBJ: 2 Q_0 + 3 I_0 + 10 B_0
Subject To
demand_satisfaction_0: Q_0 + B_0 - I_0 = 50
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, None, problem_type="single_period_newsvendor")

    assert "big_m_constraint" not in result.required_structures
    assert "capacity_constraint" not in result.required_structures
    assert "big_m_constraint" not in result.missing
    assert "capacity_constraint" not in result.missing
    certs = {item["rule_name"]: item for item in result.certificates}
    expected_score = sum(certs[key]["score"] for key in result.required_structures) / len(result.required_structures)
    assert result.structure_score == pytest.approx(expected_score)


def test_optional_structure_does_not_affect_missing_or_score_denominator():
    text = """
Minimize
OBJ: 2 Q_0 + 3 I_0
Subject To
inventory_balance_0: I_0 - Q_0 + demand_0 = 0
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, None, problem_type="single_item_multi_period")

    assert "capacity_constraint" in result.optional_structures
    assert "capacity_constraint" not in result.missing
    assert result.optional_detected["capacity_constraint"] is False
    certs = {item["rule_name"]: item for item in result.certificates}
    expected_score = sum(certs[key]["score"] for key in result.required_structures) / len(result.required_structures)
    assert result.structure_score == pytest.approx(expected_score)


def test_structure_score_denominator_is_required_only():
    text = """
Minimize
OBJ: Q_0
Subject To
nonneg_0: Q_0 >= 0
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, None, problem_type="single_item_multi_period")
    certs = {item["rule_name"]: item for item in result.certificates}
    expected_score = sum(certs[key]["score"] for key in result.required_structures) / len(result.required_structures)

    assert set(result.required_structures) == {"holding_cost", "inventory_balance", "inventory_variable", "order_variable"}
    assert result.structure_score == pytest.approx(expected_score)
    assert "capacity_constraint" not in result.missing


def test_feedback_only_reports_missing_required_structures():
    text = """
Minimize
OBJ: Q_0
Subject To
nonneg_0: Q_0 >= 0
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, None, problem_type="single_period_newsvendor")
    feedback = generate_feedback(result)

    assert "[shortage_variable]" in feedback
    assert "[big_m_constraint]" not in feedback
    assert "[capacity_constraint]" not in feedback


def test_explicit_expected_structures_take_precedence_in_check_structures():
    text = """
Minimize
OBJ: Q_0
Subject To
nonneg_0: Q_0 >= 0
End
"""
    parsed = parse_lp_text(text)
    result = check_structures(parsed, {"big_m_constraint": True}, problem_type="single_period_newsvendor")

    assert result.required_structures == ["big_m_constraint"]
    assert "big_m_constraint" in result.missing
    assert "order_variable" not in result.missing
