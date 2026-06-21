from replenishverifier.experiments.methods import select_for_method


def _row(cid, objective=10.0, consensus=0.5):
    idx = int(cid.replace("c", ""))
    return {
        "problem_id": "p0",
        "candidate_id": cid,
        "candidate_index": idx,
        "problem_type": "single_period_newsvendor",
        "execution": {"executable": True, "status": "Optimal", "objective": objective, "lp_path": f"{cid}.lp"},
        "score": 0.5,
        "raw_inference_score": 0.5,
        "structure_score": 0.8,
        "structure_only_score": 0.8,
        "objective_consensus_score": consensus,
        "objective_cluster_size": 2,
        "objective_density_score": 1.0,
        "distance_to_cluster_median": 0.0,
        "objective_term_coverage": 1.0,
        "objective_term_lp_coefficient_coverage": 1.0,
        "static_validation_score": 1.0,
        "code_output_format_valid": True,
        "type_aware_static_validation": {"checklist": [], "score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []},
        "type_aware_static_validation_errors": [],
        "structure_verification": {"structure_score": 0.8, "required_structures": [], "missing": [], "certificates": []},
    }


def _benchmark():
    return {"p0": {"id": "p0", "problem_type": "single_period_newsvendor"}}


def test_fullv2_does_not_read_reference_fields_and_empty_typeaware_is_neutral():
    rows_a = [_row("c0", objective=10.0, consensus=0.2), _row("c1", objective=20.0, consensus=0.8)]
    rows_b = [_row("c0", objective=10.0, consensus=0.2), _row("c1", objective=20.0, consensus=0.8)]
    rows_b[0].update({"reference_objective": 10.0, "objective_correct": 1.0, "relative_error": 0.0, "reference_lp": "x", "reference_answer": "x"})
    rows_b[1].update({"reference_objective": 10.0, "objective_correct": 0.0, "relative_error": 1.0, "reference_lp": "y", "reference_answer": "y"})

    selected_a = select_for_method("ReplenishVerifier-FullV2", {"p0": rows_a}, _benchmark())[0]
    selected_b = select_for_method("ReplenishVerifier-FullV2", {"p0": rows_b}, _benchmark())[0]

    # FullV2 defaults to Full here; the important invariant is that the
    # presence of reference fields does not change the selection.
    assert selected_a["candidate_id"] == selected_b["candidate_id"] == "c0"
    components = selected_a["selection_components"]
    assert components["type_aware_score"] == 1.0
    assert components["type_aware_hard_gate_score"] == 1.0
    assert set(components).isdisjoint({"reference_objective", "objective_correct", "relative_error", "reference_lp", "reference_answer", "oracle"})
