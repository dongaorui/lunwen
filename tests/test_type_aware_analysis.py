from replenishverifier.experiments.baselines import classify_error_type
from replenishverifier.experiments.compare_repair_results import summarize_repair_rows


def test_error_type_ignores_non_required_big_m_absence():
    row = {
        "problem_type": "single_period_newsvendor",
        "execution": {"executable": True, "status": "Optimal"},
        "optargus_audit": {},
        "structure_verification": {
            "missing": ["big_m_constraint"],
            "required_structures": ["order_variable", "inventory_variable", "shortage_variable", "holding_cost", "shortage_cost"],
            "expected": {"big_m_constraint": False},
        },
        "objective_correct": 1.0,
    }

    assert classify_error_type(row) == "no_error_detected"


def test_error_type_counts_explicit_required_big_m():
    row = {
        "problem_type": "single_period_newsvendor",
        "execution": {"executable": True, "status": "Optimal"},
        "optargus_audit": {},
        "structure_verification": {
            "missing": ["big_m_constraint"],
            "required_structures": ["big_m_constraint"],
            "expected": {"big_m_constraint": True},
        },
        "objective_correct": 1.0,
    }

    assert classify_error_type(row) == "missing_big_m_constraint"


def test_missing_big_m_rate_ignores_non_required_absence():
    rows = [
        {
            "objective_correct": 1.0,
            "feedback": "",
            "structure_verification": {
                "structure_score": 1.0,
                "missing": ["big_m_constraint"],
                "required_structures": ["order_variable", "inventory_variable"],
                "expected": {"big_m_constraint": False},
                "detected": {"inventory_balance": False},
            },
        }
    ]

    summary = summarize_repair_rows(rows)

    assert summary["missing_big_m_constraint_rate"] == 0.0
