from replenishverifier.experiments.methods import (
    APPENDIX_METHODS,
    MAIN_METHODS,
    METHODS,
    select_for_method,
    select_typeaware_consensus,
    type_aware_consensus_selection_components,
)


def _row(candidate_id, *, problem_type="multi_item_capacity", score=0.5, structure_score=0.5, missing=None, consensus=0.0, feedback=""):
    structure = {
        "structure_score": structure_score,
        "required_structures": ["inventory_balance", "capacity_constraint"],
        "missing": missing or [],
        "certificates": [
            {"rule_name": "inventory_balance", "score": 0.0 if "inventory_balance" in (missing or []) else 1.0},
            {"rule_name": "capacity_constraint", "score": 0.0 if "capacity_constraint" in (missing or []) else 1.0},
        ],
    }
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "candidate_index": int(str(candidate_id).replace("c", "")),
        "problem_type": problem_type,
        "execution": {"executable": True, "status": "Optimal", "objective": 10.0 + int(str(candidate_id).replace("c", ""))},
        "score": score,
        "raw_inference_score": score,
        "structure_score": structure_score,
        "structure_only_score": structure_score,
        "structure_verification": structure,
        "objective_consensus_score": consensus,
        "static_validation_score": 1.0,
        "feedback": feedback,
    }


def _benchmark(problem_type="multi_item_capacity"):
    return {"p0": {"id": "p0", "problem_type": problem_type}}


def test_main_methods_are_concise_and_appendix_keeps_legacy_methods():
    assert MAIN_METHODS == [
        "Direct",
        "Best-of-K",
        "Solver only",
        "Structure only",
        "Consensus only",
        "ReplenishVerifier-Full",
        "ReplenishVerifier-FullV2",
        "ReplenishVerifier-ConsensusSafe",
        "ReplenishVerifier-HybridSafe",
        "ReplenishVerifier-TypeAware",
        "ReplenishVerifier-TypeAware-Consensus",
    ]
    assert "Solver-Filter" in APPENDIX_METHODS
    assert "OR-R1-like Voting" in APPENDIX_METHODS
    assert "OptArgus-like Audit" in APPENDIX_METHODS
    assert "ReplenishVerifier-FullV2-CandidatePoolAware" in APPENDIX_METHODS
    assert "ReplenishVerifier-FullV2-CandidatePoolAware" not in MAIN_METHODS
    assert METHODS == MAIN_METHODS + APPENDIX_METHODS


def test_direct_still_selects_first_candidate():
    rows = [
        _row("c0", structure_score=0.1, missing=["capacity_constraint"]),
        _row("c1", structure_score=1.0, missing=[]),
    ]

    selected = select_for_method("Direct", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c0"


def test_best_of_k_uses_no_reference_tie_breaker_not_first_viable():
    rows = [
        _row("c0", structure_score=0.2, missing=["capacity_constraint"]),
        _row("c1", structure_score=0.9, missing=[]),
    ]

    selected = select_for_method("Best-of-K", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"


def test_structure_aware_selection_penalizes_critical_missing_structure_over_consensus():
    rows = [
        _row("c0", score=0.95, structure_score=0.8, missing=["capacity_constraint"], consensus=1.0),
        _row("c1", score=0.60, structure_score=0.7, missing=[], consensus=0.0),
    ]

    selected = select_for_method("ReplenishVerifier-Full", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["critical_structure_penalty"]["passed"] is True


def test_hybrid_safe_can_select_different_candidate_from_structure_only_when_structure_ties():
    rows = [
        _row("c0", score=0.80, structure_score=0.80, missing=[], consensus=0.10),
        _row("c1", score=0.80, structure_score=0.80, missing=[], consensus=0.90),
    ]
    rows[0]["execution"] = {"executable": True, "status": "Optimal", "objective": 100.0, "lp_path": "a.lp"}
    rows[1]["execution"] = {"executable": True, "status": "Optimal", "objective": 42.0, "lp_path": "b.lp"}
    rows[0]["objective_term_coverage"] = 0.6
    rows[1]["objective_term_coverage"] = 1.0
    rows[0]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 1, "variables_count": 2}
    rows[1]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
    rows[0]["type_aware_static_validation"] = {"score": 0.7, "hard_gate_score": 0.7, "hard_gate_failures": ["weak"], "missing_items": ["weak"]}
    rows[1]["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[0]["type_aware_static_validation_errors"] = ["weak"]
    rows[1]["type_aware_static_validation_errors"] = []
    rows[0]["code_output_format_valid"] = False
    rows[1]["code_output_format_valid"] = True
    rows[0]["static_validation_score"] = 0.5
    rows[1]["static_validation_score"] = 1.0

    structure_only = select_for_method("Structure only", {"p0": rows}, _benchmark())
    hybrid = select_for_method("ReplenishVerifier-HybridSafe", {"p0": rows}, _benchmark())

    assert structure_only[0]["candidate_id"] == "c0"
    assert hybrid[0]["candidate_id"] == "c1"
    assert hybrid[0]["selection_components"]["consensus_score"] == 0.90
    assert hybrid[0]["selection_components"].keys().isdisjoint({
        "reference_objective",
        "objective_correct",
        "relative_error",
        "oracle",
        "reference_lp",
        "reference_answer",
    })


def test_generic_or_r1_does_not_apply_replenishment_critical_penalty():
    rows = [
        _row("c0", structure_score=0.1, missing=["capacity_constraint"], consensus=1.0),
        _row("c1", structure_score=1.0, missing=[], consensus=0.0),
    ]
    rows[0]["or_r1_like_voting_score"] = 0.9
    rows[1]["or_r1_like_voting_score"] = 0.4

    selected = select_for_method("OR-R1-like Voting", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c0"
    assert "critical_structure_penalty" not in selected[0]


def test_solver_only_tie_break_ignores_structure_advantage():
    rows = [
        _row("c0", structure_score=1.0, missing=[]),
        _row("c1", structure_score=0.1, missing=["capacity_constraint"]),
    ]
    rows[0]["static_validation_score"] = 0.2
    rows[0]["runtime_sec"] = 5.0
    rows[1]["static_validation_score"] = 1.0
    rows[1]["runtime_sec"] = 1.0

    selected = select_for_method("Solver-Filter", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"


def test_structure_only_tie_break_ignores_consensus_advantage():
    rows = [
        _row("c0", structure_score=0.4, missing=["capacity_constraint"], consensus=1.0),
        _row("c1", structure_score=0.9, missing=[], consensus=0.0),
    ]
    rows[0]["structure_only_score"] = 0.9
    rows[1]["structure_only_score"] = 0.9

    selected = select_for_method("Structure-Only", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"


def test_type_aware_pool_filter_prefers_capacity_complete_candidate():
    rows = [
        _row("c0", structure_score=0.95, missing=["capacity_constraint"], consensus=1.0),
        _row("c1", structure_score=0.70, missing=[], consensus=0.0),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["type_aware_pool_filter_applied"] is True
    assert selected[0]["type_aware_pool_filter_fallback"] is False
    assert selected[0]["type_aware_pool_filter_candidate_count"] == 1


def test_type_aware_pool_filter_fallback_when_all_viable_miss_critical_structure():
    rows = [
        _row("c0", structure_score=0.9, missing=["capacity_constraint"], consensus=0.3),
        _row("c1", structure_score=0.8, missing=["capacity_constraint"], consensus=0.1),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())

    assert selected[0]["type_aware_pool_filter_applied"] is True
    assert selected[0]["type_aware_pool_filter_fallback"] is True
    assert selected[0]["type_aware_pool_filter_candidate_count"] == 2


def test_type_aware_selection_prefers_non_k0_with_better_objective_terms_and_gates():
    rows = [
        _row("c0", structure_score=1.0, missing=[], consensus=0.2, feedback="needs repair"),
        _row("c1", structure_score=0.9, missing=[], consensus=0.1, feedback=""),
    ]
    rows[0]["objective_term_coverage"] = 0.0
    rows[0]["runtime_sec"] = 1.0
    rows[0]["type_aware_static_validation"] = {
        "score": 0.5,
        "hard_gate_score": 0.5,
        "hard_gate_failures": ["missing_capacity_constraint"],
        "missing_items": ["missing_capacity_constraint", "missing_order_cost_term"],
        "repair_feedback": ["Add capacity constraints.", "Add order cost terms."],
    }
    rows[0]["type_aware_static_validation_errors"] = ["missing_capacity_constraint", "missing_order_cost_term"]
    rows[1]["objective_term_coverage"] = 1.0
    rows[1]["runtime_sec"] = 1.0
    rows[1]["type_aware_static_validation"] = {
        "score": 1.0,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
        "repair_feedback": [],
    }
    rows[1]["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["method_name"] == "ReplenishVerifier-TypeAware"
    assert selected[0]["uses_reference_objective_for_selection"] is False
    assert selected[0]["selection_components"]["objective_term_coverage"] == 1.0
    assert selected[0]["hard_gate_failures"] == []


def test_candidate_pool_aware_is_appendix_ablation_and_uses_no_reference_components():
    rows = [
        _row("c0", score=0.90, structure_score=0.90, missing=[], consensus=0.20),
        _row("c1", score=0.80, structure_score=0.88, missing=[], consensus=0.90),
    ]
    rows[0]["execution"] = {"executable": True, "status": "Optimal", "objective": 100.0, "lp_path": "a.lp"}
    rows[1]["execution"] = {"executable": True, "status": "Optimal", "objective": 42.0, "lp_path": "b.lp"}
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0
        row["candidate_index"] = int(row["candidate_id"].replace("c", ""))
        row["reference_objective"] = 999.0
        row["objective_correct"] = 0.0
        row["relative_error"] = 9.9

    selected = select_for_method("ReplenishVerifier-FullV2-CandidatePoolAware", {"p0": rows}, _benchmark())[0]

    assert selected["candidate_id"] == "c1"
    assert selected["selection_components"]["selector_family"] == "fullv2_candidate_pool_aware"
    assert selected["selection_components"]["objective_consensus_score"] == 0.90
    assert selected["uses_reference_objective_for_selection"] is False
    assert set(selected["selection_components"]).isdisjoint({
        "reference_objective",
        "objective_correct",
        "objective_accuracy",
        "relative_error",
        "reference_lp",
        "reference_answer",
        "oracle",
    })


def test_consensus_safe_is_main_method_before_type_aware_ablation():
    assert "ReplenishVerifier-ConsensusSafe" in MAIN_METHODS
    assert MAIN_METHODS.index("ReplenishVerifier-ConsensusSafe") < MAIN_METHODS.index("ReplenishVerifier-TypeAware")
    assert "ReplenishVerifier-ConsensusSafe" in METHODS


def test_consensus_safe_prefers_consensus_when_candidates_are_lp_safe():
    rows = [
        _row("c0", structure_score=0.9, missing=[], consensus=0.2),
        _row("c1", structure_score=0.75, missing=[], consensus=0.9),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-ConsensusSafe", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["consensus_score"] == 0.9
    assert selected[0]["selection_components"]["lp_health_score"] == 1.0


def test_consensus_safe_keeps_full_like_candidate_when_consensus_gain_is_small_and_safety_is_weaker():
    rows = [
        _row("c0", score=0.88, structure_score=0.9, missing=[], consensus=0.55),
        _row("c1", score=0.70, structure_score=0.6, missing=[], consensus=0.58),
    ]
    rows[0]["objective_term_coverage"] = 1.0
    rows[0]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
    rows[0]["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[0]["type_aware_static_validation_errors"] = []
    rows[1]["objective_term_coverage"] = 0.5
    rows[1]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 1, "variables_count": 3}
    rows[1]["type_aware_static_validation"] = {"score": 0.7, "hard_gate_score": 0.7, "hard_gate_failures": ["weak_safety"], "missing_items": ["weak_safety"]}
    rows[1]["type_aware_static_validation_errors"] = ["weak_safety"]

    selected = select_for_method("ReplenishVerifier-ConsensusSafe", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c0"
    assert selected[0]["selection_components"]["full_score"] == 0.88


def test_consensus_safe_demotes_close_consensus_candidate_with_critical_missing_structure():
    rows = [
        _row("c0", structure_score=0.95, missing=["capacity_constraint"], consensus=0.84),
        _row("c1", structure_score=0.70, missing=[], consensus=0.82),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-ConsensusSafe", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["critical_missing_count"] == 0.0


def test_consensus_safe_components_do_not_include_reference_or_oracle_fields():
    rows = [_row("c0", structure_score=1.0, missing=[], consensus=1.0)]
    rows[0]["reference_objective"] = 123.0
    rows[0]["objective_correct"] = 0.0
    rows[0]["relative_error"] = 0.9
    rows[0]["oracle_rank"] = 1
    rows[0]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
    rows[0]["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[0]["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-ConsensusSafe", {"p0": rows}, _benchmark())
    component_keys = set(selected[0]["selection_components"])

    assert component_keys.isdisjoint({"reference_objective", "objective_correct", "relative_error", "oracle", "oracle_rank", "reference_lp", "reference_answer"})
    assert selected[0]["uses_reference_objective_for_selection"] is False


def test_type_aware_consensus_prefers_consensus_before_structure_when_structure_is_safe():
    rows = [
        _row("c0", structure_score=1.0, missing=[], consensus=0.20),
        _row("c1", structure_score=0.8, missing=[], consensus=0.90),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["consensus_score"] == 0.9
    assert selected[0]["uses_reference_objective_for_selection"] is False


def test_type_aware_consensus_penalizes_wrong_consensus_with_structure_risk():
    rows = [
        _row("c0", structure_score=0.95, missing=["capacity_constraint"], consensus=0.83),
        _row("c1", structure_score=0.70, missing=[], consensus=0.82),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["critical_missing_count"] == 0.0
    assert selected[0]["selection_components"]["safe_consensus_score"] > rows[0].get("safe_consensus_score", 0.0)


def test_type_aware_consensus_demotes_large_cluster_missing_objective_terms():
    rows = [
        _row("c0", problem_type="fixed_order_cost_big_m", structure_score=0.88, missing=[], consensus=0.95),
        _row("c1", problem_type="fixed_order_cost_big_m", structure_score=0.82, missing=[], consensus=0.70),
    ]
    rows[0]["objective_term_coverage"] = 0.50
    rows[0]["objective_term_lp_coefficient_coverage"] = 0.50
    rows[0]["missing_objective_terms"] = ["fixed_order_cost"]
    rows[0]["lp_missing_objective_terms"] = ["fixed_order_cost"]
    rows[1]["objective_term_coverage"] = 1.0
    rows[1]["objective_term_lp_coefficient_coverage"] = 1.0
    rows[1]["missing_objective_terms"] = []
    rows[1]["lp_missing_objective_terms"] = []
    for row in rows:
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark("fixed_order_cost_big_m"))

    unsafe_components = type_aware_consensus_selection_components(rows[0])
    safe_components = selected[0]["selection_components"]
    assert selected[0]["candidate_id"] == "c1"
    assert safe_components["objective_term_coverage"] == 1.0
    assert safe_components["wrong_consensus_risk"] < unsafe_components["wrong_consensus_risk"]
    assert safe_components["text_triggered_hard_gate_failures"] == []


def test_type_aware_consensus_text_triggered_capacity_gate_only_when_text_mentions_capacity():
    rows = [
        _row("c0", problem_type="multi_item_capacity", structure_score=0.95, missing=["capacity_constraint"], consensus=0.99),
        _row("c1", problem_type="multi_item_capacity", structure_score=0.70, missing=[], consensus=0.50),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []
        row["natural_language"] = "Plan products with limited warehouse capacity and storage limits."

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark("multi_item_capacity"))

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["text_triggered_hard_gate_failures"] == []

    non_capacity_rows = [
        _row("c0", problem_type="single_item_multi_period", structure_score=0.95, missing=[], consensus=0.99),
        _row("c1", problem_type="single_item_multi_period", structure_score=0.70, missing=[], consensus=0.50),
    ]
    for row in non_capacity_rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []
        row["natural_language"] = "Plan one SKU over periods with inventory balance and holding costs."

    non_capacity_selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": non_capacity_rows}, _benchmark("single_item_multi_period"))

    assert non_capacity_selected[0]["candidate_id"] == "c0"
    assert non_capacity_selected[0]["selection_components"]["text_triggered_hard_gate_score"] == 1.0


def test_type_aware_consensus_does_not_let_non_executable_consensus_win():
    rows = [
        _row("c0", structure_score=1.0, missing=[], consensus=1.0),
        _row("c1", structure_score=0.2, missing=["capacity_constraint"], consensus=0.0),
    ]
    rows[0]["execution"] = {"executable": False, "status": "Error", "objective": 10.0}
    rows[1]["execution"] = {"executable": True, "status": "Optimal", "objective": 20.0}
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["execution"]["executable"] is True


def test_type_aware_consensus_does_not_use_type_aware_pool_filter_alias():
    rows = [
        _row("c0", structure_score=1.0, missing=[], consensus=0.10),
        _row("c1", structure_score=0.95, missing=["capacity_constraint"], consensus=0.99),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    type_aware = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())
    consensus = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert type_aware[0]["candidate_id"] == "c0"
    assert consensus[0]["candidate_id"] == "c0"
    assert "type_aware_pool_filter_applied" not in consensus[0]
    assert consensus[0]["selection_components"]["consensus_score"] == 0.10
    assert consensus[0]["selection_components"]["wrong_consensus_risk"] == 0.0


def test_type_aware_consensus_components_include_common_no_reference_features():
    rows = [_row("c2", problem_type="fixed_order_cost_big_m", structure_score=1.0, missing=[], consensus=0.70)]
    rows[0]["execution"] = {"executable": True, "status": "Optimal", "objective": 12.0, "lp_path": "c2.lp"}
    rows[0]["objective_term_coverage"] = 1.0
    rows[0]["objective_term_lp_coefficient_coverage"] = 1.0
    rows[0]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
    rows[0]["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[0]["type_aware_static_validation_errors"] = []
    rows[0]["reference_objective"] = 999.0
    rows[0]["objective_correct"] = 0.0
    rows[0]["relative_error"] = 9.9

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark("fixed_order_cost_big_m"))[0]
    components = selected["selection_components"]

    assert components["candidate_id"] == "c2"
    assert components["candidate_rank"] == 2
    assert components["problem_type"] == "fixed_order_cost_big_m"
    assert components["solver_ok"] == 1.0
    assert components["execution_success"] == 1.0
    assert components["finite_objective"] == 1.0
    assert components["objective"] == 12.0
    assert components.keys().isdisjoint({
        "reference_objective",
        "objective_correct",
        "objective_accuracy",
        "relative_error",
        "oracle",
        "reference_lp",
        "reference_answer",
    })


def test_fixed_order_tac_profile_uses_stable_structure_safe_tie_before_raw_consensus():
    rows = [
        _row("c0", problem_type="fixed_order_cost_big_m", structure_score=0.835, missing=[], consensus=0.375),
        _row("c1", problem_type="fixed_order_cost_big_m", structure_score=0.835, missing=[], consensus=0.500),
    ]
    rows[0]["execution"]["objective"] = 461.0
    rows[1]["execution"]["objective"] = 316.0
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []
        row["natural_language"] = "Plan replenishment with fixed order setup cost, binary order trigger, and Big-M linking."

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark("fixed_order_cost_big_m"))[0]

    assert selected["candidate_id"] == "c0"
    assert selected["selection_components"]["tac_priority_profile"] == "fixed_order_cost_big_m"
    assert selected["selection_components"]["profile_primary_signal"] == "fixed_order_schema_objective_big_m"


def test_full_uses_safe_consensus_when_structure_quality_is_tied():
    rows = [
        _row("c0", score=0.80, structure_score=0.88, missing=[], consensus=0.30),
        _row("c1", score=0.80, structure_score=0.88, missing=[], consensus=0.90),
    ]
    rows[0]["execution"]["objective"] = 100.0
    rows[1]["execution"]["objective"] = 42.0
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0

    selected = select_for_method("ReplenishVerifier-Full", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["safe_consensus_score"] > 0.88
    assert selected[0]["selection_components"].keys().isdisjoint({
        "reference_objective",
        "objective_correct",
        "relative_error",
        "oracle",
        "reference_lp",
        "reference_answer",
    })


def test_type_aware_consensus_prefers_majority_objective_cluster_over_isolated_typeaware_score():
    rows = [
        _row("c0", structure_score=1.0, missing=[], consensus=1 / 3),
        _row("c1", structure_score=0.92, missing=[], consensus=2 / 3),
        _row("c2", structure_score=0.90, missing=[], consensus=2 / 3),
    ]
    rows[0]["execution"]["objective"] = 100.0
    rows[1]["execution"]["objective"] = 42.0
    rows[2]["execution"]["objective"] = 42.000001
    rows[0]["objective_term_coverage"] = 1.0
    rows[1]["objective_term_coverage"] = 0.9
    rows[2]["objective_term_coverage"] = 0.88
    rows[0]["type_aware_static_validation"] = {
        "score": 1.0,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
    }
    rows[1]["type_aware_static_validation"] = {
        "score": 0.92,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
    }
    rows[2]["type_aware_static_validation"] = {
        "score": 0.90,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
    }
    for row in rows:
        row["type_aware_static_validation_errors"] = []
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0

    type_aware = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())
    consensus = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert type_aware[0]["candidate_id"] == "c0"
    assert consensus[0]["candidate_id"] in {"c1", "c2"}
    assert consensus[0]["selection_components"]["consensus_cluster_support"] == 2 / 3
    assert consensus[0]["selection_components"].keys().isdisjoint({
        "reference_objective",
        "objective_correct",
        "relative_error",
        "oracle",
        "reference_lp",
        "reference_answer",
    })


def test_selection_treats_empty_type_aware_checklist_as_neutral():
    rows = [
        _row("c0", problem_type="single_period_newsvendor", structure_score=1.0, missing=[], consensus=0.2),
        _row("c1", problem_type="single_period_newsvendor", structure_score=1.0, missing=[], consensus=0.8),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["type_aware_static_validation"] = {
            "checklist": [],
            "score": 1.0,
            "hard_gate_score": 1.0,
            "hard_gate_failures": [],
            "missing_items": [],
        }
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark("single_period_newsvendor"))

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["hard_gate_score"] == 1.0
    assert selected[0]["selection_components"]["type_aware_score"] == 1.0
    assert selected[0]["repair_feedback_count"] == 0.0


def test_type_aware_selection_components_do_not_include_reference_or_oracle_fields():
    rows = [_row("c0", structure_score=1.0, missing=[])]
    rows[0]["objective_term_coverage"] = 1.0
    rows[0]["reference_objective"] = 123.0
    rows[0]["objective_correct"] = 0.0
    rows[0]["relative_error"] = 0.9
    rows[0]["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[0]["type_aware_static_validation_errors"] = []

    for method in ["ReplenishVerifier-TypeAware", "ReplenishVerifier-TypeAware-Consensus"]:
        selected = select_for_method(method, {"p0": rows}, _benchmark())
        component_keys = set(selected[0]["selection_components"].keys())

        assert "reference_objective" not in component_keys
        assert "objective_correct" not in component_keys
        assert "relative_error" not in component_keys
        assert "reference_lp" not in component_keys


def test_select_typeaware_consensus_uses_fixed_order_profile_before_raw_consensus():
    rows = [
        _row("c0", problem_type="fixed_order_cost_big_m", structure_score=0.90, missing=["big_m_constraint"], consensus=0.95),
        _row("c1", problem_type="fixed_order_cost_big_m", structure_score=0.82, missing=[], consensus=0.60),
    ]
    rows[0]["objective_term_coverage"] = 0.67
    rows[0]["objective_term_lp_coefficient_coverage"] = 0.67
    rows[0]["type_aware_static_validation"] = {"score": 0.75, "hard_gate_score": 0.75, "hard_gate_failures": ["missing_big_m_linking"], "missing_items": ["missing_big_m_linking"]}
    rows[0]["type_aware_static_validation_errors"] = ["missing_big_m_linking"]
    rows[1]["objective_term_coverage"] = 1.0
    rows[1]["objective_term_lp_coefficient_coverage"] = 1.0
    rows[1]["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[1]["type_aware_static_validation_errors"] = []
    for row in rows:
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0
        row["natural_language"] = "A setup cost is paid whenever an order is placed; use binary triggers and Big-M links."

    selected = select_typeaware_consensus(rows, {"problem_type": "fixed_order_cost_big_m"})

    assert selected["candidate_id"] == "c1"
    assert selected["selection_components"]["tac_priority_profile"] == "fixed_order_cost_big_m"
    assert selected["selection_components"]["profile_primary_signal"] == "fixed_order_schema_objective_big_m"


def test_select_typeaware_consensus_uses_capacity_profile_for_capacity_text():
    rows = [
        _row("c0", problem_type="multi_item_capacity", structure_score=0.95, missing=["capacity_constraint"], consensus=0.99),
        _row("c1", problem_type="multi_item_capacity", structure_score=0.78, missing=[], consensus=0.55),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["objective_term_lp_coefficient_coverage"] = 1.0
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0
        row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []
        row["natural_language"] = "Warehouse capacity and item volume constrain storage each period."

    selected = select_typeaware_consensus(rows, {"problem_type": "multi_item_capacity"})

    assert selected["candidate_id"] == "c1"
    assert selected["selection_components"]["tac_priority_profile"] == "multi_item_capacity"
    assert selected["selection_components"]["text_triggered_hard_gate_failures"] == []


def test_select_typeaware_consensus_newsvendor_profile_prefers_structure_over_raw_consensus():
    rows = [
        _row("c0", problem_type="single_period_newsvendor", structure_score=0.83, missing=[], consensus=0.90),
        _row("c1", problem_type="single_period_newsvendor", structure_score=0.90, missing=[], consensus=0.20),
    ]
    rows[0]["objective_term_coverage"] = 0.67
    rows[1]["objective_term_coverage"] = 0.33
    for row in rows:
        row["objective_term_lp_coefficient_coverage"] = row["objective_term_coverage"]
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0
        row["type_aware_static_validation"] = {"checklist": [], "score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_typeaware_consensus(rows, {"problem_type": "single_period_newsvendor"})

    assert selected["candidate_id"] == "c1"
    assert selected["selection_components"]["tac_priority_profile"] == "single_period_newsvendor"
    assert selected["selection_components"]["profile_primary_signal"] == "newsvendor_structure_then_terms"


def test_typeaware_consensus_reference_fields_do_not_change_per_type_selection():
    rows_a = [
        _row("c0", problem_type="fixed_order_cost_big_m", structure_score=0.90, missing=["fixed_order_cost"], consensus=0.95),
        _row("c1", problem_type="fixed_order_cost_big_m", structure_score=0.80, missing=[], consensus=0.60),
    ]
    rows_b = [dict(row) for row in rows_a]
    for rows in [rows_a, rows_b]:
        rows[0]["objective_term_coverage"] = 0.67
        rows[0]["objective_term_lp_coefficient_coverage"] = 0.67
        rows[1]["objective_term_coverage"] = 1.0
        rows[1]["objective_term_lp_coefficient_coverage"] = 1.0
        for row in rows:
            row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
            row["code_output_format_valid"] = True
            row["static_validation_score"] = 1.0
            row["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
            row["type_aware_static_validation_errors"] = []
    rows_b[0].update({"reference_objective": 10.0, "objective_correct": 1.0, "relative_error": 0.0, "reference_lp": "x", "reference_answer": "x"})
    rows_b[1].update({"reference_objective": 10.0, "objective_correct": 0.0, "relative_error": 99.0, "reference_lp": "y", "reference_answer": "y"})

    selected_a = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows_a}, _benchmark("fixed_order_cost_big_m"))[0]
    selected_b = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows_b}, _benchmark("fixed_order_cost_big_m"))[0]

    assert selected_a["candidate_id"] == selected_b["candidate_id"] == "c1"
    assert set(selected_a["selection_components"]).isdisjoint({"reference_objective", "objective_correct", "relative_error", "reference_lp", "reference_answer", "oracle"})
