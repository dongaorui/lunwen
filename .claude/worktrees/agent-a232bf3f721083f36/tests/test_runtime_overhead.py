from replenishverifier.experiments.analyze_runtime_overhead import analyze_runtime_overhead
from replenishverifier.experiments.methods import evaluate_candidate
from replenishverifier.utils.io import write_jsonl


def test_runtime_overhead_analyzer_outputs_jsonl_csv_md_with_missing_fields(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [
        {
            "problem_id": "p0",
            "candidate_id": "c0",
            "total_candidate_evaluation_time": 1.2,
            "lp_parse_time": 0.2,
            "structure_check_time": 0.3,
        },
        {
            "problem_id": "p0",
            "candidate_id": "c1",
        },
    ])

    report = analyze_runtime_overhead(exp_dir)

    assert report["candidate_count"] == 2
    assert report["metrics"]["total_candidate_evaluation_time"]["mean"] == 1.2
    assert report["metrics"]["solver_time"]["mean"] is None
    assert (exp_dir / "runtime_overhead.jsonl").exists()
    assert (exp_dir / "runtime_overhead.csv").exists()
    assert (exp_dir / "runtime_overhead.md").exists()
    md = (exp_dir / "runtime_overhead.md").read_text(encoding="utf-8")
    assert "Candidate count" in md
    assert "NA" in md


def test_evaluate_candidate_records_runtime_fields(tmp_path):
    candidate = {
        "problem_id": "p0",
        "candidate_id": "c0",
        "method": "unit",
        "generated_code": """
import os
import pulp


def build_model():
    prob = pulp.LpProblem('unit', pulp.LpMinimize)
    x = pulp.LpVariable('x', lowBound=0)
    prob += x, 'objective'
    prob += x >= 1, 'minimum_x'
    return prob


if __name__ == '__main__':
    prob = build_model()
    if os.environ.get('OUTPUT_LP_PATH'):
        prob.writeLP(os.environ['OUTPUT_LP_PATH'])
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    print('STATUS:', pulp.LpStatus[prob.status])
    print('OBJECTIVE:', pulp.value(prob.objective))
""",
    }
    reference = {
        "problem_type": "single_period_newsvendor",
        "difficulty": "easy",
        "expected_structures": {},
        "reference_objective": 1.0,
        "reference_status": "Optimal",
    }

    row = evaluate_candidate(candidate, reference, work_dir=tmp_path, timeout=10)

    assert "runtime" in row
    assert row["code_execution_time"] is not None
    assert row["lp_parse_time"] is not None
    assert row["structure_check_time"] is not None
    assert row["total_candidate_evaluation_time"] is not None
    assert row["runtime_sec"] == row["total_candidate_evaluation_time"]


def test_evaluate_candidate_attaches_static_validation_fields(tmp_path):
    candidate = {
        "problem_id": "p0",
        "candidate_id": "c0",
        "method": "unit",
        "generated_code": """import pulp


def build_model():
    prob = pulp.LpProblem('unit', pulp.LpMinimize)
    x = pulp.LpVariable('x', lowBound=0)
    prob += x, 'objective'
    prob += x >= 1, 'minimum_x'
    return prob
""",
    }
    reference = {
        "problem_type": "single_period_newsvendor",
        "difficulty": "easy",
        "expected_structures": {},
        "reference_objective": 1.0,
        "reference_status": "Optimal",
    }

    row = evaluate_candidate(candidate, reference, work_dir=tmp_path, timeout=10, force_skip_execution=True)

    assert row["static_validation"]["has_build_model"] is True
    assert row["has_pulp_problem"] is True
    assert row["has_constraints"] is True
    assert row["static_validation_score"] == 1.0
