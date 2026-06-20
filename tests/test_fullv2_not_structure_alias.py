from replenishverifier.experiments.methods import MAIN_METHODS, select_for_method


def _row(cid, *, objective, structure, consensus=0.0, objective_terms=1.0, lp_terms=1.0, missing=None, type_score=1.0):
    idx = int(cid.replace("c", ""))
    missing = missing or []
    return {
        "problem_id": "p0",
        "candidate_id": cid,
        "candidate_index": idx,
        "problem_type": "multi_item_capacity",
        "execution": {"executable": True, "status": "Optimal", "objective": objective, "lp_path": f"{cid}.lp"},
        "score": 0.5,
        "raw_inference_score": 0.5,
        "base_replenishverifier_score": 0.5,
        "structure_score": structure,
        "structure_only_score": structure,
        "objective_consensus_score": consensus,
        "objective_cluster_size": int(round(consensus * 8)) if consensus else 1,
        "objective_density_score": consensus or 0.125,
        "distance_to_cluster_median": 0.0,
        "objective_term_coverage": objective_terms,
        "objective_term_lp_coefficient_coverage": lp_terms,
        "static_validation_score": 1.0,
        "code_output_format_valid": True,
        "type_aware_static_validation": {"score": type_score, "hard_gate_score": type_score, "hard_gate_failures": [], "missing_items": []},
        "type_aware_static_validation_errors": [],
        "runtime_sec": 0.1 + idx * 0.01,
        "structure_verification": {
            "structure_score": structure,
            "required_structures": ["inventory_balance", "capacity_constraint"],
            "missing": missing,
            "certificates": [
                {"rule_name": "inventory_balance", "score": 0.0 if "inventory_balance" in missing else 1.0},
                {"rule_name": "capacity_constraint", "score": 0.0 if "capacity_constraint" in missing else 1.0},
            ],
        },
        "reference_objective": 999.0,
        "objective_correct": 0.0,
        "relative_error": 99.0,
    }


def _benchmark():
    return {"p0": {"id": "p0", "problem_type": "multi_item_capacity"}}


def _select(method, rows):
    return select_for_method(method, {"p0": rows}, _benchmark())[0]


def test_fullv2_is_registered_and_not_structure_alias_when_consensus_disagrees():
    assert "ReplenishVerifier-FullV2" in MAIN_METHODS
    rows = [
        _row("c0", objective=100.0, structure=1.0, consensus=0.125, objective_terms=0.5, lp_terms=0.5),
        _row("c1", objective=42.0, structure=0.85, consensus=0.5, objective_terms=1.0, lp_terms=1.0),
        _row("c2", objective=42.000001, structure=0.84, consensus=0.5, objective_terms=1.0, lp_terms=1.0),
    ]

    structure = _select("Structure only", rows)
    fullv2 = _select("ReplenishVerifier-FullV2", rows)

    assert structure["candidate_id"] == "c0"
    assert fullv2["candidate_id"] in {"c1", "c2"}
    assert fullv2["selection_components"]["selector_family"] == "fullv2"
    assert "score_tuple_debug" in fullv2["selection_components"]


def test_candidate_rank_is_final_tie_breaker_only():
    rows = [
        _row("c0", objective=42.0, structure=0.9, consensus=0.5, objective_terms=1.0, lp_terms=1.0),
        _row("c1", objective=42.0, structure=0.9, consensus=0.5, objective_terms=1.0, lp_terms=1.0),
    ]

    selected = _select("ReplenishVerifier-FullV2", rows)

    assert selected["candidate_id"] == "c0"
    debug = selected["selection_components"]["score_tuple_debug"]
    assert debug[-1][0] == "neg_candidate_rank"
