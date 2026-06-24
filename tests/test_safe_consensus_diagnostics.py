from replenishverifier.experiments.diagnose_selection_metrics import (
    compute_full_typeaware_consensus_difference_diagnostics,
    compute_wrong_consensus_risk_diagnostics,
    diagnose_selection_metrics,
)
from replenishverifier.utils.io import write_jsonl


def _selected(method, pid, cid, objective_correct=1.0, missing=None, consensus=0.0, safe_consensus=0.0):
    missing = list(missing or [])
    return {
        "method_name": method,
        "problem_id": pid,
        "candidate_id": cid,
        "selected": True,
        "problem_type": "multi_item_capacity",
        "execution": {"executable": True, "status": "Optimal", "objective": 10.0},
        "objective_correct": objective_correct,
        "structure_score": 0.5 if missing else 1.0,
        "constraint_coverage": 0.5 if missing else 1.0,
        "objective_term_coverage": 1.0,
        "objective_consensus_score": consensus,
        "structure_verification": {
            "required_structures": ["inventory_balance", "capacity_constraint"],
            "missing": missing,
            "structure_score": 0.5 if missing else 1.0,
        },
        "selection_components": {
            "consensus_cluster_support": consensus,
            "safe_consensus_score": safe_consensus,
            "wrong_consensus_risk": max(0.0, consensus - safe_consensus),
            "critical_missing_count": float(len(missing)),
            "constraint_coverage": 0.5 if missing else 1.0,
            "objective_term_coverage": 1.0,
            "structure_completeness": 0.5 if missing else 1.0,
        },
    }


def test_compute_wrong_consensus_risk_diagnostics_flags_risky_majority_cluster():
    rows = [
        _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"], consensus=0.90, safe_consensus=0.30),
        _selected("Consensus only", "p0", "m_k0", objective_correct=0.0, missing=["capacity_constraint"], consensus=0.90, safe_consensus=0.30),
        _selected("Best-of-K", "p0", "m_k1", objective_correct=1.0, missing=[], consensus=0.10, safe_consensus=0.10),
    ]

    diagnostics = compute_wrong_consensus_risk_diagnostics(rows)

    assert diagnostics[0]["problem_id"] == "p0"
    assert diagnostics[0]["method"] == "ReplenishVerifier-TypeAware-Consensus"
    assert diagnostics[0]["wrong_consensus_risk"] == 0.60
    assert diagnostics[0]["posthoc_objective_correct"] == 0.0
    assert diagnostics[0]["posthoc_note"] == "posthoc objective correctness is diagnostic-only"


def test_compute_full_typeaware_consensus_difference_diagnostics_explains_different_choices():
    rows = [
        _selected("ReplenishVerifier-Full", "p0", "m_k0", objective_correct=0.0, missing=[], consensus=0.30, safe_consensus=0.30),
        _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0, missing=[], consensus=0.90, safe_consensus=0.90),
    ]

    diagnostics = compute_full_typeaware_consensus_difference_diagnostics(rows)

    assert diagnostics == [{
        "problem_id": "p0",
        "problem_type": "multi_item_capacity",
        "same_candidate": False,
        "full_candidate_id": "m_k0",
        "typeaware_consensus_candidate_id": "m_k1",
        "full_objective_correct_posthoc": 0.0,
        "typeaware_consensus_objective_correct_posthoc": 1.0,
        "full_safe_consensus_score": 0.30,
        "typeaware_consensus_safe_consensus_score": 0.90,
        "full_wrong_consensus_risk": 0.0,
        "typeaware_consensus_wrong_consensus_risk": 0.0,
        "full_constraint_coverage": 1.0,
        "typeaware_consensus_constraint_coverage": 1.0,
        "full_objective_term_coverage": 1.0,
        "typeaware_consensus_objective_term_coverage": 1.0,
        "diagnostic_note": "post-hoc diagnostics only; differences explain selected candidates and are not formal selection inputs",
    }]


def test_diagnose_selection_metrics_writes_safe_consensus_diagnostics(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    rows = [
        _selected("ReplenishVerifier-Full", "p0", "m_k0", objective_correct=0.0, missing=[], consensus=0.30, safe_consensus=0.30),
        _selected("ReplenishVerifier-TypeAware-Consensus", "p0", "m_k1", objective_correct=1.0, missing=[], consensus=0.90, safe_consensus=0.90),
        _selected("Consensus only", "p1", "m_k0", objective_correct=0.0, missing=["capacity_constraint"], consensus=0.90, safe_consensus=0.20),
    ]
    write_jsonl(exp_dir / "main_results.jsonl", rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", rows)

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "wrong_consensus_risk.csv").exists()
    assert (exp_dir / "diag" / "full_vs_typeaware_consensus_diff.csv").exists()
    assert result["wrong_consensus_risk"]
    assert result["full_vs_typeaware_consensus_diff"]
    assert "post-hoc diagnostics only" in (exp_dir / "diag" / "wrong_consensus_risk.md").read_text(encoding="utf-8")
    assert "post-hoc diagnostics only" in (exp_dir / "diag" / "full_vs_typeaware_consensus_diff.md").read_text(encoding="utf-8")
