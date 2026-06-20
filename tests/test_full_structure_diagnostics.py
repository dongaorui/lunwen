from replenishverifier.experiments.diagnose_selection_metrics import diagnose_selection_metrics
from replenishverifier.utils.io import write_jsonl


def _selected(method, pid, cid, correct=1.0, structure=1.0, consensus=0.5):
    return {
        "method_name": method,
        "problem_id": pid,
        "problem_type": "multi_item_capacity",
        "candidate_id": cid,
        "selected": True,
        "execution": {"executable": True, "status": "Optimal", "objective": 42.0},
        "objective_correct": correct,
        "structure_score": structure,
        "objective_consensus_score": consensus,
        "objective_cluster_size": 2,
        "objective_density_score": 0.8,
        "distance_to_cluster_median": 0.0,
        "objective_term_coverage": 1.0,
        "objective_term_lp_coefficient_coverage": 1.0,
        "static_validation_score": 1.0,
        "code_output_format_valid": True,
        "runtime_sec": 0.1,
        "selection_components": {
            "selector_family": method,
            "score_tuple_debug": [("solver_ok", 1.0), ("neg_candidate_rank", 0)],
            "missing_critical_structures": [],
            "critical_structure_penalty": 0.0,
            "type_aware_hard_gate_score": 1.0,
            "type_aware_missing_critical_count": 0.0,
        },
        "structure_verification": {
            "structure_score": structure,
            "required_structures": ["inventory_balance", "capacity_constraint"],
            "missing": [],
            "certificates": [],
        },
    }


def test_full_structure_diagnostics_files_are_generated(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    main_rows = [
        _selected("Best-of-K", "p0", "m_k1", correct=1.0, structure=0.8, consensus=0.9),
        _selected("Structure only", "p0", "m_k0", correct=0.0, structure=1.0, consensus=0.1),
        _selected("ReplenishVerifier-Full", "p0", "m_k0", correct=0.0, structure=1.0, consensus=0.1),
        _selected("ReplenishVerifier-FullV2", "p0", "m_k1", correct=1.0, structure=0.8, consensus=0.9),
    ]
    candidate_rows = [
        dict(main_rows[1], method_name=None),
        dict(main_rows[0], method_name=None),
    ]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diagnostics")

    assert (exp_dir / "diagnostics" / "full_vs_structure_diagnosis.csv").exists()
    assert (exp_dir / "diagnostics" / "full_structure_overlap_summary.md").exists()
    assert (exp_dir / "diagnostics" / "objective_consensus_clusters.csv").exists()
    assert (exp_dir / "diagnostics" / "fullv2_critical_structure_debug.csv").exists()
    assert (exp_dir / "diagnostics" / "fullv2_score_debug.csv").exists()
    assert (exp_dir / "diagnostics" / "fullv2_vs_structure_summary.md").exists()
    assert result["full_vs_structure_diagnosis"][0]["diagnostic_reason"] in {
        "same_candidate_due_to_structure_dominance",
        "same_candidate_due_to_identical_score_tuple",
        "bestofk_selected_different_correct_candidate",
    }
    text = (exp_dir / "diagnostics" / "fullv2_vs_structure_summary.md").read_text(encoding="utf-8")
    assert "FullV2 vs Structure same_selection_rate" in text
    score_debug = (exp_dir / "diagnostics" / "fullv2_score_debug.csv").read_text(encoding="utf-8")
    assert "posthoc_objective_correct" in score_debug
