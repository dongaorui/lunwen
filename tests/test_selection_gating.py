from replenishverifier.experiments.methods import APPENDIX_METHODS, MAIN_METHODS, METHODS, select_for_method


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
        "ReplenishVerifier-ConsensusSafe",
        "ReplenishVerifier-HybridSafe",
        "ReplenishVerifier-TypeAware",
        "ReplenishVerifier-TypeAware-Consensus",
    ]
    assert "Solver-Filter" in APPENDIX_METHODS
    assert "OR-R1-like Voting" in APPENDIX_METHODS
    assert "OptArgus-like Audit" in APPENDIX_METHODS
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
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["consensus_score"] == 0.9
    assert selected[0]["uses_reference_objective_for_selection"] is False


def test_type_aware_consensus_uses_critical_missing_only_when_consensus_is_close():
    rows = [
        _row("c0", structure_score=0.95, missing=["capacity_constraint"], consensus=0.83),
        _row("c1", structure_score=0.70, missing=[], consensus=0.82),
    ]
    for row in rows:
        row["objective_term_coverage"] = 1.0
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    selected = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert selected[0]["candidate_id"] == "c1"
    assert selected[0]["selection_components"]["critical_missing_count"] == 0.0


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
        row["type_aware_static_validation"] = {"hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
        row["type_aware_static_validation_errors"] = []

    type_aware = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())
    consensus = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert type_aware[0]["candidate_id"] == "c0"
    assert consensus[0]["candidate_id"] == "c1"
    assert "type_aware_pool_filter_applied" not in consensus[0]
    assert consensus[0]["selection_components"]["consensus_score"] == 0.99


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
