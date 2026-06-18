from replenishverifier.experiments.methods import select_for_method
from replenishverifier.pipeline.scoring import compute_score, hard_selection_gate, normalize_solver_status


def test_hard_selection_gate_default_requires_optimal():
    assert normalize_solver_status("Optimal") == "optimal"
    assert hard_selection_gate({"executable": True, "status": "Optimal"}, 0.8) == 0.8
    assert hard_selection_gate({"executable": True, "status": "Feasible"}, 0.8) == 0.0
    assert hard_selection_gate({"executable": False, "status": "Optimal"}, 0.8) == 0.0
    assert hard_selection_gate({"executable": True, "status": "Feasible"}, 0.8, allow_feasible_selection=True) == 0.8


def test_compute_score_preserves_structure_score_but_gates_selection():
    execution = {"executable": True, "status": "Infeasible", "objective": 1.0}
    structure = {"structure_score": 1.0, "missing": []}
    result = compute_score(execution, structure)
    assert result["structure_score"] == 1.0
    assert result["raw_inference_score"] > 0.0
    assert result["selection_score"] == 0.0
    assert result["score"] == 0.0


def test_select_for_method_ranks_by_gated_score():
    benchmark = {"p0": {"problem_type": "x", "reference_objective": 0}}
    rows = {
        "p0": [
            {
                "problem_id": "p0",
                "candidate_id": "infeasible_structural",
                "execution": {"executable": True, "status": "Infeasible", "objective": 1.0},
                "structure_score": 1.0,
                "structure_only_score": 0.0,
                "raw_structure_only_score": 1.0,
                "score": 0.0,
                "raw_inference_score": 1.0,
            },
            {
                "problem_id": "p0",
                "candidate_id": "optimal_weaker",
                "execution": {"executable": True, "status": "Optimal", "objective": 2.0},
                "structure_score": 0.5,
                "structure_only_score": 0.5,
                "raw_structure_only_score": 0.5,
                "score": 0.5,
                "raw_inference_score": 0.5,
            },
        ]
    }
    selected = select_for_method("Structure-Only", rows, benchmark)
    assert selected[0]["candidate_id"] == "optimal_weaker"
    assert selected[0]["selection_score"] == 0.5
