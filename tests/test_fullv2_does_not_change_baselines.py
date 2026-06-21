"""Isolation test: ReplenishVerifier-FullV2 must not change baseline selectors.

This test documents the project invariant that the FullV2 feature extractor
and guarded selector live in their own module and do not alter the outputs of
Best-of-K, Full, Structure only, or any other existing method.
"""

import copy

from replenishverifier.experiments.fullv2_features import should_override_full_selection
from replenishverifier.experiments.methods import select_for_method


def _row(cid, *, objective, structure, consensus=0.0, objective_terms=1.0, lp_terms=1.0, missing=None, type_score=1.0, executable=True, status="Optimal", static_validation_score=1.0, code_valid=True):
    idx = int(cid.replace("c", ""))
    missing = missing or []
    return {
        "problem_id": "p0",
        "candidate_id": cid,
        "candidate_index": idx,
        "problem_type": "multi_item_capacity",
        "execution": {"executable": executable, "status": status, "objective": objective, "lp_path": f"{cid}.lp"},
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
        "static_validation_score": static_validation_score,
        "code_output_format_valid": code_valid,
        "type_aware_static_validation": {"score": type_score, "hard_gate_score": type_score, "hard_gate_failures": [], "missing_items": []},
        "type_aware_static_validation_errors": [],
        "runtime_sec": 0.1 + idx * 0.01,
        "lp_stats": {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4},
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


def _snapshot(rows):
    """Deep-ish snapshot for detecting in-place mutation."""
    return copy.deepcopy(rows)


def _selected_id(method, rows, benchmark):
    return select_for_method(method, {"p0": rows}, benchmark)[0]["candidate_id"]


def test_fullv2_does_not_change_existing_method_selections_or_rows():
    rows = [
        _row("c0", objective=100.0, structure=1.0, consensus=0.125, missing=["capacity_constraint"]),
        _row("c1", objective=42.0, structure=0.85, consensus=0.5, missing=[]),
        _row("c2", objective=42.000001, structure=0.84, consensus=0.5, missing=[]),
    ]
    benchmark = _benchmark()

    before = _snapshot(rows)

    best_of_k_id = _selected_id("Best-of-K", rows, benchmark)
    full_id = _selected_id("ReplenishVerifier-Full", rows, benchmark)
    structure_id = _selected_id("Structure only", rows, benchmark)

    after_baselines = _snapshot(rows)

    fullv2_id = _selected_id("ReplenishVerifier-FullV2", rows, benchmark)

    after_fullv2 = _snapshot(rows)

    # The baseline selections must be unchanged by the presence of FullV2.
    assert best_of_k_id == "c0"
    assert full_id == "c1"
    assert structure_id == "c1"

    # FullV2 defaults to Full here because no challenger provides strong enough
    # no-reference evidence to override the stable Full base.
    assert fullv2_id == full_id

    # No method call may mutate the original candidate rows in place.
    assert after_baselines == before
    assert after_fullv2 == before

    # FullV2 must expose its guarded decision metadata without reference fields.
    selected = select_for_method("ReplenishVerifier-FullV2", {"p0": rows}, benchmark)[0]
    decision = selected.get("fullv2_guarded_decision")
    assert decision is not None
    assert decision["overridden"] is False
    assert decision["override_reason"] == "override_evidence_insufficient"
    assert decision["full_candidate_id"] == "c1"
    assert set(decision).isdisjoint({"reference_objective", "objective_correct", "relative_error", "reference_lp", "reference_answer", "oracle"})


def test_fullv2_override_logic_detects_critical_missing_fix():
    full_row = _row("c0", objective=100.0, structure=0.9, consensus=0.5, missing=["capacity_constraint"])
    chal_row = _row("c1", objective=42.0, structure=0.9, consensus=0.5, missing=[])

    overridden, reason = should_override_full_selection(full_row, chal_row)
    assert overridden is True
    assert "critical_missing" in reason


def test_fullv2_override_logic_detects_strictly_better_structure():
    full_row = _row("c0", objective=100.0, structure=0.80, consensus=0.5, missing=[])
    chal_row = _row("c1", objective=42.0, structure=0.95, consensus=0.5, missing=[])

    overridden, reason = should_override_full_selection(full_row, chal_row)
    assert overridden is True
    assert "strictly_better_structure" in reason


def test_fullv2_override_logic_requires_multiple_improvements_when_structure_equal():
    full_row = _row("c0", objective=100.0, structure=0.90, consensus=0.2, objective_terms=0.8, static_validation_score=0.5)
    chal_row = _row("c1", objective=42.0, structure=0.90, consensus=0.8, objective_terms=0.8, static_validation_score=0.5)

    # Only consensus improves; structure is equal.  This is not enough.
    overridden, reason = should_override_full_selection(full_row, chal_row)
    assert overridden is False
    assert reason == "override_evidence_insufficient"


def test_fullv2_override_logic_allows_override_with_multiple_equal_structure_improvements():
    full_row = _row("c0", objective=100.0, structure=0.90, consensus=0.2, objective_terms=0.8, static_validation_score=0.5, code_valid=False)
    chal_row = _row("c1", objective=42.0, structure=0.90, consensus=0.8, objective_terms=0.9, static_validation_score=1.0, code_valid=True)

    # Consensus, objective_terms, static_validation, and code_validity improve.
    overridden, reason = should_override_full_selection(full_row, chal_row)
    assert overridden is True
    assert "multiple_improvements" in reason


def test_fullv2_does_not_override_on_single_dimension_improvement():
    rows = [
        _row("c0", objective=100.0, structure=0.90, consensus=0.125, missing=[]),
        _row("c1", objective=42.0, structure=0.90, consensus=0.875, missing=[]),
    ]
    benchmark = _benchmark()

    full_id = _selected_id("ReplenishVerifier-Full", rows, benchmark)
    fullv2_id = _selected_id("ReplenishVerifier-FullV2", rows, benchmark)

    # Consensus alone is not strong enough to override the Full base.
    assert fullv2_id == full_id
