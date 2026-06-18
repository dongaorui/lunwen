from replenishverifier.verifier.lp_parser import is_auto_constraint_name, parse_lp_text, tag_symbol_concepts
from replenishverifier.verifier.structure_rules import check_structures


def test_parse_simple_lp():
    text = """
Minimize
OBJ: 2 Q_0 + 3 I_0
Subject To
inventory_balance_0: I_0 - Q_0 = -5
Bounds
End
"""
    parsed = parse_lp_text(text)
    assert "inventory_balance_0" in parsed.constraint_names
    assert "Q_0" in parsed.variable_names
    assert "I_0" in parsed.variable_names
    assert "inventory" in parsed.variable_concept_tags["I_0"]


def test_auto_named_pulp_constraints_are_preserved_but_not_semantic_name_evidence():
    text = """
Minimize
OBJ: Q_0 + I_0
Subject To
_C1: I_0 - Q_0 + demand_0 = 0
Bounds
End
"""
    parsed = parse_lp_text(text)
    assert "_C1" in parsed.constraint_names
    assert parsed.auto_named_constraints == ["_C1"]
    assert is_auto_constraint_name("_C1") is True
    assert "auto_named_constraint" in parsed.constraint_concept_tags["_C1"]

    result = check_structures(parsed, {"inventory_balance": True})
    cert = {item["rule_name"]: item for item in result.certificates}["inventory_balance"]
    assert "_C1" not in cert["matched_names"]
    assert cert["evidence_strength"] in {"expression_supported", "expression_and_graph"}


def test_concept_tags_cover_descriptive_names():
    assert "inventory" in tag_symbol_concepts("ending-inventory[0]")
    assert "order" in tag_symbol_concepts("purchase_qty")
    assert "capacity" in tag_symbol_concepts("resource_limit_t")
