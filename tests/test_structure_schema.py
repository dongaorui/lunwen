import pytest

from replenishverifier.data.structure_schema import (
    expected_from_schema,
    get_structure_schema,
    split_expected_structures,
)


def test_get_structure_schema_returns_sets_and_rejects_unknown_type():
    schema = get_structure_schema("single_period_newsvendor")

    assert isinstance(schema["required"], set)
    assert isinstance(schema["optional"], set)
    assert isinstance(schema["forbidden"], set)
    assert "order_variable" in schema["required"]
    assert "inventory_variable" in schema["required"]
    assert "shortage_variable" in schema["required"]
    assert "big_m_constraint" not in schema["required"]

    schema["required"].add("big_m_constraint")
    assert "big_m_constraint" not in get_structure_schema("single_period_newsvendor")["required"]

    with pytest.raises(ValueError, match="Unknown problem_type: unknown_type"):
        get_structure_schema("unknown_type")


def test_problem_type_schema_separates_required_optional_and_forbidden():
    expected = expected_from_schema("fixed_order_cost_big_m")
    required, optional, forbidden = split_expected_structures(expected, problem_type="fixed_order_cost_big_m")

    assert "big_m_constraint" in required
    assert "fixed_order_cost" in required
    assert "capacity_constraint" in optional
    assert forbidden == []
    assert expected["big_m_constraint"] is True
    assert expected["capacity_constraint"] is False


def test_explicit_expected_structures_override_default_schema():
    expected = {"big_m_constraint": True}
    required, optional, forbidden = split_expected_structures(expected, problem_type="single_period_newsvendor")

    assert required == ["big_m_constraint"]
    assert "inventory_balance" in optional
    assert "big_m_constraint" not in optional
    assert forbidden == []


def test_schema_fallback_used_when_instance_expected_missing():
    required, optional, forbidden = split_expected_structures(None, problem_type="single_item_multi_period")

    assert "inventory_balance" in required
    assert "order_variable" in required
    assert "capacity_constraint" in optional
    assert forbidden == []
