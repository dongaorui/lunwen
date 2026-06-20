from replenishverifier.experiments.methods import fullv2_selection_components


def _row(problem_type, missing):
    return {
        "problem_id": "p0",
        "candidate_id": "c0",
        "candidate_index": 0,
        "problem_type": problem_type,
        "execution": {"executable": True, "status": "Optimal", "objective": 1.0},
        "objective_consensus_score": 0.5,
        "objective_cluster_size": 1,
        "objective_density_score": 1.0,
        "distance_to_cluster_median": 0.0,
        "objective_term_coverage": 1.0,
        "objective_term_lp_coefficient_coverage": 1.0,
        "structure_score": 0.8,
        "static_validation_score": 1.0,
        "code_output_format_valid": True,
        "type_aware_static_validation": {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []},
        "structure_verification": {
            "structure_score": 0.8,
            "required_structures": list(missing),
            "missing": list(missing),
            "certificates": [{"rule_name": name, "score": 0.0} for name in missing],
        },
    }


def test_critical_structure_penalty_depends_on_problem_type():
    capacity = fullv2_selection_components(_row("multi_item_capacity", ["capacity_constraint"]))
    newsvendor = fullv2_selection_components(_row("single_period_newsvendor", ["capacity_constraint"]))
    fixed = fullv2_selection_components(_row("fixed_order_cost_big_m", ["big_m_constraint", "binary_order_variable"]))

    assert capacity["type_aware_missing_critical_count"] == 1
    assert "capacity_constraint" in capacity["missing_critical_structures"]
    assert newsvendor["type_aware_missing_critical_count"] == 0
    assert fixed["type_aware_missing_critical_count"] == 2
    assert fixed["critical_structure_penalty"] > capacity["critical_structure_penalty"]
