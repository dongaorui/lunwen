from replenishverifier.experiments.diagnose_selection_metrics import (
    build_method_redundancy_report,
    build_metric_saturation_report,
    compute_avoidable_error_summary,
    compute_best_of_k_audit,
    compute_full_typeaware_consensus_difference_diagnostics,
    compute_method_selection_clusters,
    compute_problem_type_pool_limit_diagnostics,
    compute_tac_comparison_diagnostics,
    compute_tac_override_summary,
    compute_wrong_consensus_risk_diagnostics,
    diagnose_selection_metrics,
)
from replenishverifier.experiments.paper_metrics import compute_missed_oracle_summary, compute_paired_method_comparison
from replenishverifier.utils.io import write_jsonl


def _selected(method, pid, cid, objective_correct=1.0, missing=None, problem_type="multi_item_capacity"):
    return {
        "method_name": method,
        "problem_id": pid,
        "candidate_id": cid,
        "selected": True,
        "execution": {"executable": True, "status": "Optimal", "objective": 1.0},
        "objective_correct": objective_correct,
        "relative_error": 0.0 if objective_correct else 0.5,
        "structure_score": 0.5 if missing else 1.0,
        "problem_type": problem_type,
        "structure_verification": {
            "expected": {"inventory_balance": True, "capacity_constraint": problem_type == "multi_item_capacity"},
            "detected": {"inventory_balance": "inventory_balance" not in (missing or []), "capacity_constraint": "capacity_constraint" not in (missing or [])},
            "required_structures": ["inventory_balance", "capacity_constraint"] if problem_type == "multi_item_capacity" else ["inventory_balance"],
            "missing": list(missing or []),
            "structure_score": 0.5 if missing else 1.0,
        },
        "runtime_sec": 0.1,
        "code_output_format_valid": True,
        "objective_term_coverage": 1.0,
    }


def test_diagnose_selection_metrics_writes_comparisons_and_debug(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    main_rows = [_selected("Direct", "p0", "m_k0"), _selected("Best-of-K", "p0", "m_k1", objective_correct=0.0)]
    main_rows[1]["uses_reference_objective_for_selection"] = False
    main_rows[1]["selection_policy"] = "best executable/optimal candidate by no-reference tie-breaker, with Hard Selection Gate for formal score; no reference objective"
    main_rows[1]["selection_components"] = {"selector_family": "best_of_k", "structure_score": 1.0}
    candidate_rows = [dict(main_rows[0], method_name=None), dict(main_rows[1], method_name=None)]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "metric_comparison.csv").exists()
    assert (exp_dir / "diag" / "metric_comparison.md").exists()
    assert (exp_dir / "diag" / "selection_score_debug.csv").exists()
    assert (exp_dir / "diag" / "same_selection_rate.csv").exists()
    assert (exp_dir / "diag" / "best_of_k_audit.md").exists()
    assert (exp_dir / "diag" / "best_of_k_audit.json").exists()
    assert result["metric_comparison"]
    assert result["best_of_k_audit"]["formal_best_of_k_is_no_reference"] is True
    assert any(row["status"] in {"OK", "MISSING"} for row in result["metric_comparison"])
    debug_text = (exp_dir / "diag" / "selection_score_debug.csv").read_text(encoding="utf-8")
    assert "objective_correct_posthoc" in debug_text


def test_compute_best_of_k_audit_reports_no_reference_signals():
    best = _selected("Best-of-K", "p0", "m_k1", objective_correct=1.0)
    best["selection_policy"] = "best executable/optimal candidate by no-reference tie-breaker, with Hard Selection Gate for formal score; no reference objective"
    best["uses_reference_objective_for_selection"] = False
    best["selection_components"] = {"selector_family": "best_of_k", "structure_score": 1.0}

    audit = compute_best_of_k_audit([best])

    assert audit["method"] == "Best-of-K"
    assert audit["formal_best_of_k_is_no_reference"] is True
    assert audit["uses_reference_objective_for_selection"] is False
    assert audit["uses_objective_correct_for_selection"] is False
    assert audit["uses_oracle_for_selection"] is False
    assert audit["uses_reference_lp_for_selection"] is False
    assert audit["uses_reference_answer_for_selection"] is False
    assert audit["forbidden_component_keys"] == []


def test_compute_tac_comparison_diagnostics_reports_alias_reason():
    tac = _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0)
    safe = _selected("ReplenishVerifier-ConsensusSafe", "p0", "m_k1", objective_correct=1.0)
    hybrid = _selected("ReplenishVerifier-HybridSafe", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"])
    tac["selection_components"] = {
        "tac_priority_profile": "multi_item_capacity",
        "safe_consensus_score": 0.7,
        "wrong_consensus_risk": 0.0,
        "objective_term_coverage": 1.0,
        "constraint_coverage": 1.0,
        "text_triggered_hard_gate_score": 1.0,
        "critical_missing_count": 0.0,
    }
    safe["selection_components"] = {"safe_consensus_score": 0.7, "wrong_consensus_risk": 0.0, "objective_term_coverage": 1.0, "constraint_coverage": 1.0}
    hybrid["selection_components"] = {"safe_consensus_score": 0.9, "wrong_consensus_risk": 0.4, "objective_term_coverage": 1.0, "constraint_coverage": 0.5}

    rows = compute_tac_comparison_diagnostics([tac, safe, hybrid])

    assert rows[0]["problem_id"] == "p0"
    assert rows[0]["tac_vs_consensussafe_same"] is True
    assert rows[0]["tac_vs_hybridsafe_same"] is False
    assert rows[0]["tac_profile"] == "multi_item_capacity"
    assert "objective_correct_posthoc_tac" in rows[0]
    assert rows[0]["posthoc_only"] is True


def test_diagnose_detects_reported_mismatch(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "main_results.jsonl", [_selected("Direct", "p0", "m_k0")])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [_selected("candidate", "p0", "m_k0")])
    write_jsonl(exp_dir / "reported_main_summary.jsonl", [{"method": "Direct", "executable_rate": 0.0}])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    mismatches = [row for row in result["metric_comparison"] if row["status"] == "MISMATCH"]
    assert any(row["method"] == "Direct" and row["metric"] == "executable_rate" for row in mismatches)


def test_compute_problem_type_pool_limit_diagnostics_marks_low_oracle_types_as_pool_limited():
    candidate_rows = [
        _selected("candidate", "cap0", "m_k0", objective_correct=0.0, problem_type="multi_item_capacity"),
        _selected("candidate", "cap0", "m_k1", objective_correct=1.0, problem_type="multi_item_capacity"),
        _selected("candidate", "cap1", "m_k0", objective_correct=0.0, problem_type="multi_item_capacity"),
        _selected("candidate", "cap1", "m_k1", objective_correct=0.0, problem_type="multi_item_capacity"),
        _selected("candidate", "fix0", "m_k0", objective_correct=1.0, problem_type="fixed_order_cost_big_m"),
        _selected("candidate", "fix1", "m_k0", objective_correct=1.0, problem_type="fixed_order_cost_big_m"),
    ]
    main_rows = [
        _selected("ReplenishVerifier-TypeAware-Consensus", "cap0", "m_k0", objective_correct=0.0, problem_type="multi_item_capacity"),
        _selected("ReplenishVerifier-TypeAware-Consensus", "cap1", "m_k0", objective_correct=0.0, problem_type="multi_item_capacity"),
        _selected("ReplenishVerifier-TypeAware-Consensus", "fix0", "m_k0", objective_correct=1.0, problem_type="fixed_order_cost_big_m"),
        _selected("ReplenishVerifier-TypeAware-Consensus", "fix1", "m_k0", objective_correct=1.0, problem_type="fixed_order_cost_big_m"),
    ]

    rows = compute_problem_type_pool_limit_diagnostics(main_rows, candidate_rows)
    by_type = {row["problem_type"]: row for row in rows}

    assert by_type["multi_item_capacity"]["oracle_at_k"] == 0.5
    assert by_type["multi_item_capacity"]["selector_accuracy"] == 0.0
    assert by_type["multi_item_capacity"]["candidate_pool_limited"] is True
    assert "candidate-pool limitation" in by_type["multi_item_capacity"]["diagnostic_note"]
    assert by_type["fixed_order_cost_big_m"]["oracle_at_k"] == 1.0
    assert by_type["fixed_order_cost_big_m"]["candidate_pool_limited"] is False



def test_compute_missed_oracle_summary_counts_oracle_cases_missed_by_selection():
    candidate_rows = [
        _selected("candidate", "p0", "m_k0", objective_correct=0.0),
        _selected("candidate", "p0", "m_k1", objective_correct=1.0),
        _selected("candidate", "p1", "m_k0", objective_correct=0.0),
        _selected("candidate", "p1", "m_k1", objective_correct=0.0),
    ]
    main_rows = [
        _selected("Direct", "p0", "m_k0", objective_correct=0.0),
        _selected("ReplenishVerifier-TypeAware", "p0", "m_k1", objective_correct=1.0),
        _selected("Direct", "p1", "m_k0", objective_correct=0.0),
        _selected("ReplenishVerifier-TypeAware", "p1", "m_k0", objective_correct=0.0),
    ]

    summary = compute_missed_oracle_summary(main_rows, candidate_rows)
    by_method = {row["method"]: row for row in summary}

    assert by_method["Direct"]["oracle_objective_available_count"] == 1
    assert by_method["Direct"]["missed_oracle_objective_count"] == 1
    assert by_method["ReplenishVerifier-TypeAware"]["missed_oracle_objective_count"] == 0


def test_compute_paired_method_comparison_reports_wins_losses_and_error_reduction():
    rows = [
        _selected("Direct", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("ReplenishVerifier-TypeAware", "p0", "m_k1", objective_correct=1.0, missing=[]),
        _selected("Direct", "p1", "m_k0", objective_correct=1.0, missing=[]),
        _selected("ReplenishVerifier-TypeAware", "p1", "m_k1", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("Direct", "p2", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("ReplenishVerifier-TypeAware", "p2", "m_k1", objective_correct=0.0, missing=[]),
    ]

    comparison = compute_paired_method_comparison(rows, target_method="ReplenishVerifier-TypeAware", baseline_methods=["Direct"])

    assert comparison == [{
        "target_method": "ReplenishVerifier-TypeAware",
        "baseline_method": "Direct",
        "n_common": 3,
        "objective_win_count": 1,
        "objective_loss_count": 1,
        "objective_tie_count": 1,
        "structure_win_count": 2,
        "structure_loss_count": 1,
        "structure_tie_count": 0,
        "missing_capacity_reduction_count": 2,
        "missing_capacity_increase_count": 1,
        "objective_mismatch_reduction_count": 1,
        "objective_mismatch_increase_count": 1,
    }]


def test_diagnose_selection_metrics_writes_oracle_and_paired_outputs(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    main_rows = [
        _selected("Direct", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("ReplenishVerifier-TypeAware", "p0", "m_k1", objective_correct=1.0, missing=[]),
    ]
    candidate_rows = [
        _selected("candidate", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("candidate", "p0", "m_k1", objective_correct=1.0, missing=[]),
    ]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "missed_oracle_summary.csv").exists()
    assert (exp_dir / "diag" / "paired_method_comparison.csv").exists()
    assert (exp_dir / "diag" / "problem_type_pool_limit_diagnostics.csv").exists()
    assert (exp_dir / "diag" / "problem_type_pool_limit_diagnostics.md").exists()
    assert result["missed_oracle_summary"]
    assert result["paired_method_comparison"]
    assert result["problem_type_pool_limit_diagnostics"]


def test_method_redundancy_report_lists_high_overlap_and_identical_metric_groups():
    metrics = [
        {"method": "Solver only", "objective_accuracy": 0.5, "structure_completeness": 1.0, "constraint_coverage": 1.0},
        {"method": "Solver-Filter", "objective_accuracy": 0.5, "structure_completeness": 1.0, "constraint_coverage": 1.0},
        {"method": "Consensus only", "objective_accuracy": 0.5, "structure_completeness": 0.5, "constraint_coverage": 0.5},
    ]
    same_selection = [{"method_a": "Solver only", "method_b": "Solver-Filter", "n_common": 20, "same_count": 19, "same_selection_rate": 0.95}]

    report = build_method_redundancy_report(metrics, same_selection, threshold=0.95)

    assert "This report is diagnostic only and does not affect formal selection." in report
    assert "Solver only" in report and "Solver-Filter" in report
    assert "same_selection_rate" in report
    assert "Metrics-identical method groups" in report


def test_metric_saturation_report_flags_low_unique_metrics_and_overlap_pairs():
    metrics = [
        {"method": "A", "objective_accuracy": 0.5, "optimal_rate": 1.0, "constraint_coverage": 1.0},
        {"method": "B", "objective_accuracy": 0.5, "optimal_rate": 1.0, "constraint_coverage": 0.5},
        {"method": "C", "objective_accuracy": 0.5, "optimal_rate": 0.0, "constraint_coverage": 1.0},
    ]
    same_selection = [{"method_a": "A", "method_b": "B", "n_common": 3, "same_count": 3, "same_selection_rate": 1.0}]

    report = build_metric_saturation_report(metrics, same_selection, low_unique_threshold=2)

    assert "This report is diagnostic only and does not affect formal selection." in report
    assert "objective_accuracy" in report
    assert "unique_values" in report
    assert "A" in report and "B" in report


def test_method_selection_clusters_labels_alias_like_pairs_and_recommendations():
    metrics = [
        {"method": "A", "objective_accuracy": 0.82},
        {"method": "B", "objective_accuracy": 0.82},
        {"method": "C", "objective_accuracy": 0.83},
    ]
    same_selection = [
        {"method_a": "A", "method_b": "B", "n_common": 100, "same_count": 100, "same_selection_rate": 1.0},
        {"method_a": "A", "method_b": "C", "n_common": 100, "same_count": 100, "same_selection_rate": 1.0},
    ]

    rows = compute_method_selection_clusters(metrics, same_selection)
    by_pair = {(row["method_a"], row["method_b"]): row for row in rows}

    assert by_pair[("A", "B")]["recommendation"] == "alias_like_same_selection"
    assert by_pair[("A", "B")]["objective_accuracy_a"] == 0.82
    assert by_pair[("A", "B")]["objective_accuracy_b"] == 0.82
    assert by_pair[("A", "C")]["recommendation"] == "same_selection_but_metric_difference_check_needed"


def test_diagnose_selection_metrics_writes_method_selection_clusters(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    main_rows = [
        _selected("A", "p0", "m_k0", objective_correct=1.0),
        _selected("B", "p0", "m_k0", objective_correct=1.0),
    ]
    candidate_rows = [dict(main_rows[0], method_name=None)]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "method_selection_clusters.csv").exists()
    assert result["method_selection_clusters"][0]["recommendation"] == "alias_like_same_selection"


def test_compute_avoidable_error_summary_counts_posthoc_opportunities():
    main_rows = [
        _selected("ReplenishVerifier-TypeAware", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0, missing=[]),
        _selected("Consensus only", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
    ]
    main_rows[0]["execution"] = {"executable": False, "status": "Error", "objective": None}
    main_rows[2]["execution"] = {"executable": True, "status": "Infeasible", "objective": 1.0}
    candidate_rows = [
        _selected("candidate", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("candidate", "p0", "m_k1", objective_correct=1.0, missing=[]),
    ]

    summary = compute_avoidable_error_summary(main_rows, candidate_rows)
    by_method = {row["method"]: row for row in summary}

    assert by_method["ReplenishVerifier-TypeAware"]["objective_mismatch_with_objective_correct_available"] == 1
    assert by_method["ReplenishVerifier-TypeAware"]["missing_capacity_with_capacity_available"] == 1
    assert by_method["ReplenishVerifier-TypeAware"]["execution_error_with_executable_available"] == 1
    assert by_method["Consensus only"]["solver_not_optimal_with_optimal_available"] == 1
    assert by_method["ReplenishVerifier-TypeAware-Consensus"]["objective_mismatch_with_objective_correct_available"] == 0


def test_diagnose_selection_metrics_writes_selector_counterfactuals_and_failure_summary(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    best = _selected("Best-of-K", "p0", "m_k1", objective_correct=1.0, missing=[])
    hybrid = _selected("ReplenishVerifier-HybridSafe", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"])
    hybrid["selection_components"] = {
        "selector_family": "hybrid_safe",
        "method_vote_count": 3.0,
        "consensus_score": 0.9,
        "critical_missing_count": 1.0,
        "constraint_coverage": 0.5,
        "structure_completeness": 0.5,
    }
    best["selection_components"] = {
        "selector_family": "best_of_k",
        "method_vote_count": 1.0,
        "consensus_score": 0.2,
        "critical_missing_count": 0.0,
        "constraint_coverage": 1.0,
        "structure_completeness": 1.0,
    }
    write_jsonl(exp_dir / "main_results.jsonl", [best, hybrid])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [dict(best, method_name=None), dict(hybrid, method_name=None)])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "selector_counterfactuals.csv").exists()
    assert (exp_dir / "diag" / "selector_counterfactuals.md").exists()
    assert (exp_dir / "diag" / "selector_failure_summary.md").exists()
    assert result["selector_counterfactuals"][0]["target_method"] == "ReplenishVerifier-HybridSafe"
    assert result["selector_counterfactuals"][0]["posthoc_only"] is True
    text = (exp_dir / "diag" / "selector_failure_summary.md").read_text(encoding="utf-8")
    assert "posthoc_only" in text
    assert "critical penalty" in text or "structure" in text



def test_diagnose_selection_metrics_writes_consensus_safe_counterfactual(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    best = _selected("Best-of-K", "p0", "m_k1", objective_correct=1.0, missing=[])
    safe = _selected("ReplenishVerifier-ConsensusSafe", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"])
    safe["selection_components"] = {
        "consensus_score": 0.9,
        "lp_health_score": 1.0,
        "critical_missing_count": 1.0,
        "constraint_coverage": 0.5,
        "objective_term_coverage": 1.0,
        "structure_completeness": 0.5,
    }
    best["selection_components"] = {
        "consensus_score": 0.2,
        "lp_health_score": 1.0,
        "critical_missing_count": 0.0,
        "constraint_coverage": 1.0,
        "objective_term_coverage": 1.0,
        "structure_completeness": 1.0,
    }
    write_jsonl(exp_dir / "main_results.jsonl", [best, safe])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [dict(best, method_name=None), dict(safe, method_name=None)])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "consensus_safe_counterfactual.csv").exists()
    assert (exp_dir / "diag" / "consensus_safe_counterfactual.md").exists()
    assert result["consensus_safe_counterfactual"][0]["problem_id"] == "p0"
    assert result["consensus_safe_counterfactual"][0]["objective_delta_vs_best_of_k"] == -1.0
    text = (exp_dir / "diag" / "consensus_safe_counterfactual.md").read_text(encoding="utf-8")
    assert "post-hoc diagnostics only" in text
    assert "critical_missing" in text


def test_diagnose_selection_metrics_writes_new_diagnostic_reports(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    main_rows = [
        _selected("ReplenishVerifier-TypeAware", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0, missing=[]),
        _selected("Consensus only", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
    ]
    candidate_rows = [
        _selected("candidate", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"]),
        _selected("candidate", "p0", "m_k1", objective_correct=1.0, missing=[]),
    ]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "method_redundancy_report.md").exists()
    assert (exp_dir / "diag" / "metric_saturation_report.md").exists()
    assert (exp_dir / "diag" / "avoidable_error_summary.md").exists()
    assert "avoidable_error_summary" in result
    assert "post-hoc diagnostics only" in (exp_dir / "diag" / "avoidable_error_summary.md").read_text(encoding="utf-8")


def test_compute_tac_override_summary_counts_posthoc_recovery_effects():
    improved = _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0, missing=[])
    worsened = _selected("ReplenishVerifier-TypeAware-Consensus", "p1", "m_k1", objective_correct=0.0, missing=[])
    unchanged = _selected("ReplenishVerifier-TypeAware-Consensus", "p2", "m_k0", objective_correct=1.0, missing=[])
    improved["tac_recovery_decision"] = {"triggered": True, "reason": "fixed_order_overwhelming_safe_consensus", "initial_candidate_id": "m_k0"}
    improved["selection_components"] = {"tac_recovery_triggered": True, "tac_recovery_reason": "fixed_order_overwhelming_safe_consensus"}
    improved["tac_initial_objective_correct_posthoc"] = 0.0
    worsened["tac_recovery_decision"] = {"triggered": True, "reason": "challenger_completes_hard_schema", "initial_candidate_id": "m_k0"}
    worsened["selection_components"] = {"tac_recovery_triggered": True, "tac_recovery_reason": "challenger_completes_hard_schema"}
    worsened["tac_initial_objective_correct_posthoc"] = 1.0
    unchanged["selection_components"] = {"tac_recovery_triggered": False}

    summary = compute_tac_override_summary([improved, worsened, unchanged])

    assert summary["total_triggered"] == 2
    assert summary["improved_count"] == 1
    assert summary["worsened_count"] == 1
    assert summary["unchanged_count"] == 0
    assert summary["posthoc_note"]


def test_diagnose_selection_metrics_writes_tac_override_summary(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    row = _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0, missing=[])
    row["selection_components"] = {"tac_recovery_triggered": True, "tac_recovery_reason": "fixed_order_overwhelming_safe_consensus"}
    row["tac_recovery_decision"] = {"triggered": True, "reason": "fixed_order_overwhelming_safe_consensus", "initial_candidate_id": "m_k0"}
    row["tac_initial_objective_correct_posthoc"] = 0.0
    write_jsonl(exp_dir / "main_results.jsonl", [row])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [dict(row, method_name=None)])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diagnostics")

    assert result["tac_override_summary"]["improved_count"] == 1
    text = (exp_dir / "diagnostics" / "tac_override_summary.md").read_text(encoding="utf-8")
    assert "improved_count" in text
    assert "post-hoc" in text


def test_diagnostics_join_matches_k4_to_k7_candidate_ids(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    candidate_rows = []
    main_rows = []
    selected_ranks = {
        "Direct": 4,
        "Best-of-K": 5,
        "ReplenishVerifier-TypeAware": 6,
        "ReplenishVerifier-TypeAware-Consensus": 7,
    }
    for k in range(8):
        candidate_rows.append(_selected("candidate", "p0", f"Qwen3-8B_k{k}"))
    for method, k in selected_ranks.items():
        main_rows.append(_selected(method, "p0", f"Qwen3-8B_k{k}"))
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diagnostics")

    assert result["diagnostic_join_unmatched"] == []
    unmatched_path = exp_dir / "diagnostics" / "diagnostic_join_unmatched.csv"
    assert unmatched_path.exists()
    distribution = {row["method"]: row for row in result["selection_diagnostics"]["candidate_rank_distribution"]}
    assert distribution["Direct"]["k4"] == 1
    assert distribution["Best-of-K"]["k5"] == 1
    assert distribution["ReplenishVerifier-TypeAware"]["k6"] == 1
    assert distribution["ReplenishVerifier-TypeAware-Consensus"]["k7"] == 1
    debug_text = (exp_dir / "diagnostics" / "selection_score_debug.csv").read_text(encoding="utf-8")
    assert "Qwen3-8B_k7" in debug_text
    summary_text = (exp_dir / "diagnostics" / "diagnostic_summary.md").read_text(encoding="utf-8")
    assert '"unmatched_selected_rows": 0' in summary_text


def test_diagnostics_join_can_match_by_unique_parsed_candidate_rank(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    candidate_rows = [_selected("candidate", "p0", f"Qwen3-8B_k{k}") for k in range(8)]
    main_rows = [_selected("Direct", "p0", "alternate_model_k7")]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diagnostics")

    assert result["diagnostic_join_unmatched"] == []
    debug_rows = result["selection_diagnostics"]["selection_score_debug"]
    selected_debug = [row for row in debug_rows if row["selected"]]
    assert selected_debug[0]["candidate_id"] == "Qwen3-8B_k7"
    assert selected_debug[0]["parsed_candidate_rank"] == 7


def test_diagnostics_join_reports_unmatched_selected_rows(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "main_results.jsonl", [_selected("Direct", "p0", "Qwen3-8B_k7")])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [_selected("candidate", "p0", "Qwen3-8B_k0")])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diagnostics")

    unmatched = result["diagnostic_join_unmatched"]
    assert unmatched == [{
        "method": "Direct",
        "problem_id": "p0",
        "candidate_id": "Qwen3-8B_k7",
        "parsed_candidate_rank": 7,
        "candidate_rank_parse_reason": "ok",
        "reason": "candidate_id_not_found_for_problem",
        "matched_candidate_id": "",
        "selected_file_or_source": "main_results",
    }]
    csv_text = (exp_dir / "diagnostics" / "diagnostic_join_unmatched.csv").read_text(encoding="utf-8")
    assert "parsed_candidate_rank" in csv_text
    assert "candidate_rank_parse_reason" in csv_text
    assert "selected_file_or_source" in csv_text
    assert "candidate_id_not_found_for_problem" in csv_text


def test_diagnostic_join_unmatched_records_source_and_rank_parse_reason(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    selected = _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "Qwen3-8B_candidate_without_rank")
    selected["selected_file_or_source"] = "custom_main_results.jsonl"
    write_jsonl(exp_dir / "main_results.jsonl", [selected])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [_selected("candidate", "p0", "Qwen3-8B_k7")])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diagnostics")

    unmatched = result["diagnostic_join_unmatched"]
    assert unmatched == [{
        "method": "ReplenishVerifier-TypeAware-Consensus",
        "problem_id": "p0",
        "candidate_id": "Qwen3-8B_candidate_without_rank",
        "parsed_candidate_rank": None,
        "candidate_rank_parse_reason": "no_k_rank_pattern",
        "reason": "candidate_id_not_found_for_problem",
        "matched_candidate_id": "",
        "selected_file_or_source": "custom_main_results.jsonl",
    }]
    csv_text = (exp_dir / "diagnostics" / "diagnostic_join_unmatched.csv").read_text(encoding="utf-8")
    assert "candidate_rank_parse_reason" in csv_text
    assert "selected_file_or_source" in csv_text
    assert "custom_main_results.jsonl" in csv_text


def test_diagnose_parses_reported_markdown_tables(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "main_results.jsonl", [_selected("Direct", "p0", "m_k0")])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [_selected("candidate", "p0", "m_k0")])
    (exp_dir / "summary.md").write_text(
        "# Experiment Summary\n\n"
        "| method | n | executable_rate | optimal_rate | objective_accuracy | structure_completeness | inventory_balance_accuracy | constraint_coverage | average_runtime_sec | average_repair_feedback_count |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| Direct | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.1000 | 0.0000 |\n",
        encoding="utf-8",
    )

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert all(row["status"] == "OK" for row in result["metric_comparison"])
