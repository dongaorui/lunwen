from replenishverifier.experiments.diagnose_selection_metrics import diagnose_selection_metrics
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
    candidate_rows = [dict(main_rows[0], method_name=None), dict(main_rows[1], method_name=None)]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "metric_comparison.csv").exists()
    assert (exp_dir / "diag" / "metric_comparison.md").exists()
    assert (exp_dir / "diag" / "selection_score_debug.csv").exists()
    assert (exp_dir / "diag" / "same_selection_rate.csv").exists()
    assert result["metric_comparison"]
    assert any(row["status"] in {"OK", "MISSING"} for row in result["metric_comparison"])
    debug_text = (exp_dir / "diag" / "selection_score_debug.csv").read_text(encoding="utf-8")
    assert "objective_correct_posthoc" in debug_text


def test_diagnose_detects_reported_mismatch(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "main_results.jsonl", [_selected("Direct", "p0", "m_k0")])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [_selected("candidate", "p0", "m_k0")])
    write_jsonl(exp_dir / "reported_main_summary.jsonl", [{"method": "Direct", "executable_rate": 0.0}])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    mismatches = [row for row in result["metric_comparison"] if row["status"] == "MISMATCH"]
    assert any(row["method"] == "Direct" and row["metric"] == "executable_rate" for row in mismatches)


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
    assert result["missed_oracle_summary"]
    assert result["paired_method_comparison"]


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
