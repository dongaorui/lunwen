from replenishverifier.experiments.audit_leakage import FORMAL_METHODS, _audit_rows
from replenishverifier.experiments.baselines import (
    code_output_format_valid,
    compute_lp_stats,
    compute_objective_consensus_scores,
    compute_optargus_audit,
    optargus_like_audit_score,
    optirepair_like_score,
    or_r1_like_voting_score,
    sirl_like_lp_stats_score,
)
from replenishverifier.experiments.methods import reward_components, select_for_method
from replenishverifier.experiments.extract_case_studies import extract_case_studies
from replenishverifier.utils.io import write_jsonl
from replenishverifier.verifier.lp_parser import parse_lp_text


def test_strong_baselines_use_generic_lp_signals():
    parsed = parse_lp_text(
        """
Minimize
OBJ: 2 production + 3 shipment
Subject To
resource_limit: production + shipment >= 5
Bounds
production >= 0
shipment >= 0
End
"""
    )
    execution = {"executable": True, "status": "Optimal", "objective": 10.0}

    stats = compute_lp_stats(parsed)
    audit = compute_optargus_audit(parsed, execution)

    assert stats["lp_exported"] is True
    assert stats["objective_terms_count"] == 2
    assert stats["constraints_to_variables_ratio"] > 0
    assert audit["objective_has_variable"] is True
    assert audit["generic_issue_count"] == 0
    assert sirl_like_lp_stats_score(execution, stats) > 0.8
    assert optargus_like_audit_score(execution, audit) > 0.7
    assert optirepair_like_score(execution, audit) > 0.7


def test_or_r1_like_voting_uses_candidate_consensus_without_reference_objective():
    rows = [
        {"execution": {"executable": True, "status": "Optimal", "objective": 10.0, "lp_path": "a.lp"}},
        {"execution": {"executable": True, "status": "Optimal", "objective": 10.0000001, "lp_path": "b.lp"}},
        {"execution": {"executable": True, "status": "Optimal", "objective": 99.0, "lp_path": "c.lp"}},
        {"execution": {"executable": False, "status": "Error", "objective": None, "lp_path": None}},
    ]

    consensus = compute_objective_consensus_scores(rows)

    assert consensus[0] > consensus[2]
    assert consensus[1] > consensus[2]
    assert consensus[2] > 0.0
    assert consensus[3] == 0.0
    assert code_output_format_valid("import pulp\nmodel = pulp.LpProblem('x', pulp.LpMinimize)\n") is False
    assert or_r1_like_voting_score(rows[0]["execution"], consensus[0], code_format_valid=True) > 0.8


def test_code_output_format_rejects_markdown_fences():
    fence = chr(96) * 3
    code = f'''{fence}python
import pulp

def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    return prob
{fence}'''

    assert code_output_format_valid(code) is False


def test_code_output_format_rejects_syntax_errors():
    code = '''import pulp

def build_model(:
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    return prob
'''

    assert code_output_format_valid(code) is False


def test_code_output_format_accepts_runner_compatible_build_model():
    code = '''import pulp

def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x
    return prob
'''

    assert code_output_format_valid(code) is True


def _row(candidate_id, objective, structure_score=0.0, executable=True, status="Optimal", reference_objective=999.0):
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "execution": {"executable": executable, "status": status, "objective": objective, "lp_path": f"{candidate_id}.lp" if executable else None},
        "structure_score": structure_score,
        "structure_verification": {"structure_score": structure_score, "missing": [] if structure_score >= 1.0 else ["inventory_balance"]},
        "objective_consensus_score": 0.0,
        "reference_objective": reference_objective,
        "raw_solver_only_score": 1.0 if executable and status == "Optimal" else 0.0,
        "solver_only_score": 1.0 if executable and status == "Optimal" else 0.0,
        "score": structure_score,
    }


def test_reward_style_selector_uses_consensus_structure_and_no_reference_objective():
    rows = [
        _row("minority_good_structure", 10.0, structure_score=1.0, reference_objective=10.0),
        _row("majority_mid_structure_a", 20.0, structure_score=0.5, reference_objective=999.0),
        _row("majority_mid_structure_b", 20.000001, structure_score=0.5, reference_objective=999.0),
    ]
    for row, score in zip(rows, compute_objective_consensus_scores(rows)):
        row["objective_consensus_score"] = score

    selected_consensus = select_for_method("Consensus only", {"p0": rows}, {"p0": {"problem_type": "single_item_multi_period", "difficulty": "medium"}})
    selected_structure = select_for_method("Structure only", {"p0": rows}, {"p0": {"problem_type": "single_item_multi_period", "difficulty": "medium"}})
    selected_full = select_for_method("Solver + Structure + Consensus", {"p0": rows}, {"p0": {"problem_type": "single_item_multi_period", "difficulty": "medium"}})
    selected_grounded = select_for_method("Structure-Grounded Consistency", {"p0": rows}, {"p0": {"problem_type": "single_item_multi_period", "difficulty": "medium"}})

    assert selected_consensus[0]["candidate_id"] == "majority_mid_structure_a"
    assert selected_structure[0]["candidate_id"] == "minority_good_structure"
    assert selected_full[0]["candidate_id"]
    assert selected_full[0]["uses_reference_objective_for_selection"] is False
    assert "reference_objective" not in selected_full[0]["reward_components"]
    assert "reference_objective" not in reward_components(rows[0])
    assert "Rlp_artifact_structure" in selected_grounded[0]["reward_components"]
    assert selected_grounded[0]["uses_reference_objective_for_selection"] is False
    assert "no reference objective" in selected_full[0]["selection_policy"]
    assert "structure-grounded" in selected_grounded[0]["selection_policy"]
    assert "no reference objective" in selected_grounded[0]["selection_policy"]


def test_reward_style_methods_are_in_no_leakage_audit():
    assert "Consensus only" in FORMAL_METHODS
    assert "Solver + Structure + Consensus" in FORMAL_METHODS
    assert "Structure-Grounded Consistency" in FORMAL_METHODS
    row = {
        "method_name": "Consensus only",
        "selected": True,
        "uses_reference_objective_for_selection": False,
        "selection_policy": "OR-R1-inspired objective consensus among candidates; no reference objective",
        "score": 1.0,
        "selection_score": 1.0,
        "objective_correct": 0.0,
    }

    assert _audit_rows([row], "unit", require_selected=True) == []


def test_optargus_like_audit_penalizes_placeholder_models():
    parsed = parse_lp_text(
        """
Minimize
OBJ: 0 dummy
Subject To
dummy_constraint: dummy >= 0
End
"""
    )
    execution = {"executable": True, "status": "Optimal", "objective": 0.0}

    audit = compute_optargus_audit(parsed, execution)

    assert audit["suspicious_variable_name_count"] == 1
    assert audit["suspicious_constraint_name_count"] == 1
    assert "placeholder_variable_names" in audit["generic_issues"]
    assert "placeholder_constraint_names" in audit["generic_issues"]


def test_case_studies_prioritize_strong_baselines(tmp_path):
    base = {
        "selected": True,
        "problem_id": "p0",
        "problem_type": "fixed_order_cost_big_m",
        "difficulty": "hard",
        "candidate_id": "cand_base",
        "execution": {"executable": True},
        "structure_score": 0.5,
        "objective_correct": 0.0,
        "structure_verification": {"missing": ["big_m_constraint"]},
        "selection_policy": "generic baseline; no reference objective",
        "feedback": "generic feedback",
    }
    full = {
        **base,
        "method_name": "ReplenishVerifier-Full",
        "candidate_id": "cand_full",
        "structure_score": 1.0,
        "objective_correct": 1.0,
        "structure_verification": {"missing": []},
    }
    solver = {**base, "method_name": "Solver-Filter"}
    strong = {**base, "method_name": "OptArgus-like Audit"}
    write_jsonl(tmp_path / "main_results.jsonl", [solver, strong, full])

    cases = extract_case_studies(tmp_path)

    assert len(cases) == 2
    assert cases[0]["baseline_method"] == "OptArgus-like Audit"
    assert cases[0]["baseline_selection_policy"] == "generic baseline; no reference objective"
    assert cases[1]["baseline_method"] == "Solver-Filter"
    assert (tmp_path / "case_studies.md").exists()
