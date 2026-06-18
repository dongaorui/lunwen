from replenishverifier.experiments.audit_leakage import _audit_rows


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
