from replenishverifier.experiments.audit_leakage import FORMAL_METHODS, _audit_rows


def _formal_row(**updates):
    row = {
        "method_name": "Direct",
        "selected": True,
        "uses_reference_objective_for_selection": False,
        "selection_policy": "candidate order only; no reference objective",
        "score": 1.0,
        "selection_score": 1.0,
    }
    row.update(updates)
    return row


def test_formal_selection_rejects_reference_policy_marker():
    issues = _audit_rows([
        _formal_row(selection_policy="select closest to reference_objective")
    ], "main_results", require_selected=True)

    assert any("reference" in issue.lower() for issue in issues)


def test_formal_selection_rejects_reference_usage_flag():
    issues = _audit_rows([
        _formal_row(uses_reference_objective_for_selection=True)
    ], "main_results", require_selected=True)

    assert any("uses_reference_objective_for_selection" in issue for issue in issues)


def test_posthoc_oracle_metric_rows_are_allowed_when_marked_nonformal():
    issues = _audit_rows([
        {
            "k": 4,
            "formal_selection_metric": False,
            "uses_reference_for_oracle_metrics": True,
            "oracle_objective_accuracy_at_k": 1.0,
        }
    ], "paper_metrics", require_selected=False)

    assert issues == []


def test_consensus_safe_and_hybrid_safe_are_covered_by_formal_leakage_audit():
    assert "ReplenishVerifier-ConsensusSafe" in FORMAL_METHODS
    assert "ReplenishVerifier-HybridSafe" in FORMAL_METHODS


def test_type_aware_selection_components_reject_reference_fields():
    issues = _audit_rows([
        _formal_row(
            method_name="ReplenishVerifier-TypeAware",
            selection_policy="TypeAware score over candidate signals; no reference objective",
            selection_components={
                "executable": 1.0,
                "objective_term_coverage": 1.0,
                "reference_objective": 42.0,
            },
        )
    ], "main_results", require_selected=True)

    assert any("selection_components" in issue and "reference_objective" in issue for issue in issues)


def test_type_aware_allows_candidate_observable_components():
    issues = _audit_rows([
        _formal_row(
            method_name="ReplenishVerifier-TypeAware",
            selection_policy="TypeAware score over candidate static validation, LP structure, objective-term coverage, and consensus; no reference objective",
            selection_components={
                "executable": 1.0,
                "solver_optimal": 1.0,
                "structure_completeness": 1.0,
                "constraint_coverage": 1.0,
                "objective_term_coverage": 1.0,
                "hard_gate_score": 1.0,
                "consensus_score": 0.5,
                "repair_feedback_count": 0.0,
                "runtime_sec": 0.2,
            },
        )
    ], "main_results", require_selected=True)

    assert issues == []
