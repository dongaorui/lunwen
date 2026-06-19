import csv

from replenishverifier.experiments.build_paper_metrics import build_paper_metrics
from replenishverifier.experiments.paper_metrics import (
    compute_metrics_by_problem_type,
    compute_selected_method_metrics,
    compute_error_type_summary,
    compute_pass_at_k,
    compute_selection_collapse_summary,
    compute_selection_diagnostics,
    format_metric_value,
)
from replenishverifier.utils.io import write_jsonl


def _row(method, pid, cid, selected=True, executable=True, status="Optimal", objective_correct=1.0, structure_score=1.0, problem_type="multi_item_capacity"):
    return {
        "method_name": method,
        "problem_id": pid,
        "candidate_id": cid,
        "selected": selected,
        "problem_type": problem_type,
        "execution": {"executable": executable, "status": status, "objective": 10.0},
        "objective_correct": objective_correct,
        "relative_error": 0.0 if objective_correct else 0.5,
        "structure_score": structure_score,
        "structure_verification": {
            "expected": {"inventory_balance": True, "capacity_constraint": False},
            "detected": {"inventory_balance": structure_score >= 1.0, "capacity_constraint": False},
            "required_structures": ["inventory_balance"],
            "missing": [] if structure_score >= 1.0 else ["inventory_balance"],
            "structure_score": structure_score,
        },
        "objective_term_coverage": 1.0,
        "objective_term_surface_coverage": 1.0,
        "objective_term_lp_coefficient_coverage": 0.75,
        "runtime_sec": 0.25,
        "feedback": "",
        "code_output_format_valid": True,
        "selection_score": 0.8,
        "objective_consensus_score": 0.5,
    }


def test_compute_selected_method_metrics_uses_only_selected_rows():
    rows = [
        _row("Direct", "p0", "k0", selected=True, objective_correct=1.0, structure_score=1.0),
        _row("Direct", "p1", "k0", selected=True, objective_correct=0.0, structure_score=0.0),
        _row("Direct", "p2", "k1", selected=False, objective_correct=1.0, structure_score=1.0),
    ]

    metrics = compute_selected_method_metrics(rows)

    assert metrics == [{
        "method": "Direct",
        "n": 2,
        "objective_accuracy_count": 1,
        "objective_accuracy_total": 2,
        "structure_complete_count": 1,
        "structure_complete_total": 2,
        "code_validity_rate": 1.0,
        "executable_rate": 1.0,
        "optimal_rate": 1.0,
        "solver_status_optimal_rate": 1.0,
        "solver_status_infeasible_rate": 0.0,
        "solver_status_timeout_rate": 0.0,
        "solver_status_error_rate": 0.0,
        "objective_accuracy": 0.5,
        "mean_relative_error": 0.25,
        "median_relative_error": 0.25,
        "mean_objective_gap": 0.25,
        "median_objective_gap": 0.25,
        "structure_completeness": 0.5,
        "inventory_balance_accuracy": 0.5,
        "constraint_coverage": 0.5,
        "objective_term_surface_coverage": 1.0,
        "objective_term_lp_coefficient_coverage": 0.75,
        "objective_term_coverage": 1.0,
        "average_runtime_sec": 0.25,
        "median_runtime_sec": 0.25,
        "average_repair_feedback_count": 0.5,
    }]


def test_format_metric_value_outputs_na_and_four_decimals():
    assert format_metric_value(None) == "N/A"
    assert format_metric_value(0.123456) == "0.1235"
    assert format_metric_value("Direct") == "Direct"


def test_error_type_summary_counts_selected_rows_by_method():
    rows = [
        _row("Direct", "p0", "k0", executable=False, status="Error"),
        _row("Direct", "p1", "k0"),
    ]

    summary = compute_error_type_summary(rows)

    assert {item["error_type"]: item["count"] for item in summary if item["method"] == "Direct"} == {
        "execution_error": 1,
        "no_error_detected": 1,
    }
    assert all("rate" in item for item in summary)


def test_compute_pass_at_k_reports_oracle_upper_bounds():
    candidate_rows = [
        _row("candidate", "p0", "m_k0", objective_correct=0.0, structure_score=0.0),
        _row("candidate", "p0", "m_k1", objective_correct=1.0, structure_score=1.0),
        _row("candidate", "p1", "m_k0", objective_correct=0.0, structure_score=1.0),
        _row("candidate", "p1", "m_k1", objective_correct=0.0, structure_score=1.0),
    ]

    rows = compute_pass_at_k(candidate_rows, [1, 2])

    by_k = {row["k"]: row for row in rows}
    assert by_k[1]["pass_at_k_objective"] == 0.0
    assert by_k[2]["pass_at_k_objective"] == 0.5
    assert by_k[2]["oracle_structure_completeness_at_k"] == 1.0
    assert by_k[2]["uses_reference_for_oracle_metrics"] is True
    assert by_k[2]["formal_selection_metric"] is False


def test_compute_selection_diagnostics_outputs_same_rate_and_rank_distribution():
    main_rows = [
        _row("Direct", "p0", "model_k0"),
        _row("Best-of-K", "p0", "model_k1"),
        _row("Direct", "p1", "model_k0"),
        _row("Best-of-K", "p1", "model_k0"),
    ]
    candidate_rows = [
        _row("candidate", "p0", "model_k0"),
        _row("candidate", "p0", "model_k1"),
        _row("candidate", "p1", "model_k0"),
        _row("candidate", "p1", "model_k1"),
    ]

    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows)

    same = diagnostics["same_selection_rate"]
    direct_vs_best = [row for row in same if row["method_a"] == "Best-of-K" and row["method_b"] == "Direct"][0]
    assert direct_vs_best["same_selection_rate"] == 0.5
    distribution = diagnostics["candidate_rank_distribution"]
    assert {row["method"]: row["k0"] for row in distribution} == {"Best-of-K": 1, "Direct": 2}
    debug = diagnostics["selection_score_debug"]
    assert {"method", "problem_id", "candidate_id", "objective_correct_posthoc", "selected"} <= set(debug[0])


def test_compute_metrics_by_problem_type_groups_selected_methods_and_problem_types():
    rows = [
        _row("Consensus only", "p0", "model_k0", objective_correct=0.0, structure_score=0.5, problem_type="multi_item_capacity"),
        _row("ReplenishVerifier-TypeAware-Consensus", "p1", "model_k1", objective_correct=1.0, structure_score=1.0, problem_type="multi_item_capacity"),
        _row("ReplenishVerifier-TypeAware-Consensus", "p2", "model_k1", objective_correct=1.0, structure_score=1.0, problem_type="fixed_order_cost_big_m"),
    ]

    table = compute_metrics_by_problem_type(rows, methods=["Consensus only", "ReplenishVerifier-TypeAware-Consensus"])
    keyed = {(row["method"], row["problem_type"]): row for row in table}

    assert keyed[("Consensus only", "multi_item_capacity")]["objective_accuracy"] == 0.0
    assert keyed[("ReplenishVerifier-TypeAware-Consensus", "multi_item_capacity")]["objective_accuracy"] == 1.0
    assert keyed[("ReplenishVerifier-TypeAware-Consensus", "fixed_order_cost_big_m")]["constraint_coverage"] == 1.0


def test_compute_selection_collapse_summary_reports_high_overlap_and_duplicate_metrics():
    rows = [
        _row("A", "p0", "model_k0", objective_correct=1.0, structure_score=1.0),
        _row("B", "p0", "model_k0", objective_correct=1.0, structure_score=1.0),
        _row("A", "p1", "model_k1", objective_correct=0.0, structure_score=0.5),
        _row("B", "p1", "model_k1", objective_correct=0.0, structure_score=0.5),
    ]

    summary = compute_selection_collapse_summary(rows, threshold=0.95)

    assert any(row["diagnostic_type"] == "high_same_selection_pair" and row["method_a"] == "A" and row["method_b"] == "B" for row in summary)
    assert any(row["diagnostic_type"] == "metric_duplicate_group" and "A" in row["methods"] and "B" in row["methods"] for row in summary)


def test_build_paper_metrics_writes_expected_tables(tmp_path):
    exp_dir = tmp_path / "exp"
    out_dir = tmp_path / "paper"
    exp_dir.mkdir()
    main_rows = [
        _row("Direct", "p0", "model_k0"),
        _row("ReplenishVerifier-TypeAware-Consensus", "p0", "model_k0"),
    ]
    candidate_rows = [_row("candidate", "p0", "model_k0")]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = build_paper_metrics(exp_dir, out_dir, k_values=[1], bootstrap_samples=20, seed=1)

    expected = [
        "table_main_metrics",
        "table_solver_status",
        "table_objective_gap",
        "table_structure_metrics",
        "table_objective_terms",
        "table_pass_at_k_oracle",
        "table_selection_diagnostics",
        "table_missed_oracle_summary",
        "table_paired_method_comparison",
        "table_error_taxonomy",
        "table_runtime_cost",
        "table_bootstrap_ci",
        "table_by_problem_type",
        "table_selection_collapse",
    ]
    assert set(result["tables"]) == set(expected)
    for name in expected:
        assert (out_dir / f"{name}.csv").exists()
        assert (out_dir / f"{name}.md").exists()

    with (out_dir / "table_objective_terms.csv").open(encoding="utf-8") as f:
        objective_terms_rows = list(csv.DictReader(f))
    assert {
        "objective_term_surface_coverage",
        "objective_term_lp_coefficient_coverage",
        "objective_term_coverage",
    } <= set(objective_terms_rows[0])

    with (out_dir / "table_main_metrics.csv").open(encoding="utf-8") as f:
        main_metric_rows = list(csv.DictReader(f))
    assert main_metric_rows[0]["objective_accuracy_count"] == "1"
    assert main_metric_rows[0]["objective_accuracy_total"] == "1"

    with (out_dir / "table_by_problem_type.csv").open(encoding="utf-8") as f:
        by_type_rows = list(csv.DictReader(f))
    assert any(row["method"] == "ReplenishVerifier-TypeAware-Consensus" for row in by_type_rows)

    with (out_dir / "table_selection_collapse.csv").open(encoding="utf-8") as f:
        collapse_rows = list(csv.DictReader(f))
    assert collapse_rows
