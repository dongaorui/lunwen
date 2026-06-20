import pytest

from replenishverifier.experiments import methods
from replenishverifier.experiments.methods import select_for_method


FORBIDDEN_SELECTION_FIELDS = {
    "reference_objective",
    "objective_correct",
    "objective_accuracy",
    "relative_error",
    "oracle",
    "oracle_rank",
    "reference_lp",
    "reference_answer",
}


def _candidate(candidate_id, *, objective, structure=0.5, consensus=0.0, type_score=1.0, missing=None):
    missing = missing or []
    idx = int(candidate_id.replace("k", ""))
    return {
        "problem_id": "p0",
        "candidate_id": f"Qwen3-8B_{candidate_id}",
        "candidate_index": idx,
        "problem_type": "multi_item_capacity",
        "execution": {"executable": True, "status": "Optimal", "objective": objective, "lp_path": f"{candidate_id}.lp"},
        "score": 0.5,
        "raw_inference_score": 0.5,
        "structure_score": structure,
        "structure_only_score": structure,
        "objective_consensus_score": consensus,
        "objective_term_coverage": 1.0,
        "lp_stats": {"lp_exported": True, "objective_present": True, "constraints_count": 3 + idx, "variables_count": 3 + idx},
        "code_output_format_valid": True,
        "static_validation_score": 1.0,
        "type_aware_static_validation": {
            "score": type_score,
            "hard_gate_score": type_score,
            "hard_gate_failures": [] if type_score >= 1.0 else ["weak"],
            "missing_items": [] if type_score >= 1.0 else ["weak"],
        },
        "type_aware_static_validation_errors": [] if type_score >= 1.0 else ["weak"],
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
        "relative_error": 10.0,
        "oracle_rank": 7,
        "reference_lp": "FORBIDDEN",
        "reference_answer": "FORBIDDEN",
    }


def _rows():
    return [
        _candidate("k0", objective=100.0, structure=1.0, consensus=0.125, type_score=1.0),
        _candidate("k1", objective=42.0, structure=0.92, consensus=0.375, type_score=0.92),
        _candidate("k2", objective=42.000001, structure=0.90, consensus=0.375, type_score=0.90),
        _candidate("k3", objective=42.000002, structure=0.88, consensus=0.375, type_score=0.88),
        _candidate("k4", objective=77.0, structure=0.86, consensus=0.125, type_score=1.0),
        _candidate("k5", objective=88.0, structure=0.80, consensus=0.125, type_score=1.0, missing=["capacity_constraint"]),
        _candidate("k6", objective=99.0, structure=0.75, consensus=0.125, type_score=0.75),
        _candidate("k7", objective=None, structure=0.70, consensus=0.0, type_score=1.0),
    ]


def _benchmark():
    return {"p0": {"id": "p0", "problem_type": "multi_item_capacity"}}


def _selected(method_name):
    return select_for_method(method_name, {"p0": _rows()}, _benchmark())[0]


def _component_keys(row):
    return set((row.get("selection_components") or {}).keys())


def test_core_methods_have_independent_dispatch_and_no_reference_components():
    methods_to_check = [
        "Direct",
        "Best-of-K",
        "ReplenishVerifier-Full",
        "ReplenishVerifier-TypeAware",
        "ReplenishVerifier-TypeAware-Consensus",
        "ReplenishVerifier-ConsensusSafe",
        "ReplenishVerifier-HybridSafe",
    ]

    selected = {method_name: _selected(method_name) for method_name in methods_to_check}

    assert selected["Direct"]["candidate_id"] == "Qwen3-8B_k0"
    assert selected["ReplenishVerifier-HybridSafe"]["selection_components"]["selector_family"] == "hybrid_safe"
    assert selected["ReplenishVerifier-ConsensusSafe"]["selection_components"]["selector_family"] == "consensus_safe_v2"
    assert selected["ReplenishVerifier-TypeAware-Consensus"]["selection_components"]["selector_family"] == "type_aware_consensus"
    assert selected["ReplenishVerifier-TypeAware"]["selection_components"].get("selector_family", "type_aware") == "type_aware"
    assert selected["ReplenishVerifier-Full"]["selection_components"]["selector_family"] == "full_legacy"

    for method_name, row in selected.items():
        assert row.get("uses_reference_objective_for_selection") is False
        assert _component_keys(row).isdisjoint(FORBIDDEN_SELECTION_FIELDS), method_name


def test_dispatch_does_not_call_other_selector_component_builders(monkeypatch):
    def fail_consensus_safe(_row):
        raise AssertionError("Full must not call ConsensusSafe components")

    def fail_type_aware_consensus(_row):
        raise AssertionError("ConsensusSafe must not call TypeAware-Consensus components")

    def fail_type_aware(_row):
        raise AssertionError("TypeAware-Consensus must not call TypeAware score")

    original_consensus_safe = methods.consensus_safe_selection_components
    monkeypatch.setattr(methods, "consensus_safe_selection_components", fail_consensus_safe)
    _selected("ReplenishVerifier-Full")
    monkeypatch.setattr(methods, "consensus_safe_selection_components", original_consensus_safe)

    original_type_aware_consensus = methods.type_aware_consensus_selection_components
    monkeypatch.setattr(methods, "type_aware_consensus_selection_components", fail_type_aware_consensus)
    _selected("ReplenishVerifier-ConsensusSafe")
    monkeypatch.setattr(methods, "type_aware_consensus_selection_components", original_type_aware_consensus)

    monkeypatch.setattr(methods, "type_aware_selection_score", fail_type_aware)
    _selected("ReplenishVerifier-TypeAware-Consensus")


@pytest.mark.parametrize("method_name", [
    "ReplenishVerifier-Full",
    "ReplenishVerifier-TypeAware",
    "ReplenishVerifier-TypeAware-Consensus",
    "ReplenishVerifier-ConsensusSafe",
    "ReplenishVerifier-HybridSafe",
])
def test_reference_fields_do_not_change_formal_selection(method_name):
    rows_a = _rows()
    rows_b = _rows()
    for idx, row in enumerate(rows_b):
        row["reference_objective"] = -1000000.0 + idx
        row["objective_correct"] = 1.0 if idx == 7 else 0.0
        row["relative_error"] = 0.0 if idx == 7 else 999.0
        row["oracle_rank"] = 0 if idx == 7 else 99
        row["reference_lp"] = f"reference_lp_{idx}"
        row["reference_answer"] = f"reference_answer_{idx}"

    selected_a = select_for_method(method_name, {"p0": rows_a}, _benchmark())[0]
    selected_b = select_for_method(method_name, {"p0": rows_b}, _benchmark())[0]

    assert selected_a["candidate_id"] == selected_b["candidate_id"]
