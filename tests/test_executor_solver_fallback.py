import textwrap

import pulp

from replenishverifier.experiments.methods import evaluate_candidate
from replenishverifier.solver.code_executor import execute_generated_code
from replenishverifier.solver.pulp_runner import solve_pulp_model


class FailingPulpCbcCmd:
    def __init__(self, *args, **kwargs):
        raise pulp.PulpSolverError("PULP_CBC_CMD unavailable in this environment")


class RecordingCoinCmd:
    calls = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        RecordingCoinCmd.calls.append((args, kwargs))

    def available(self):
        return "/tmp/fake-cbc"


class FakeLpProblem:
    objective = 3.0

    def __init__(self):
        self.solved_with = None
        self.written_lp_path = None

    def writeLP(self, path):
        self.written_lp_path = path

    def solve(self, solver):
        self.solved_with = solver
        return 1


def test_solve_pulp_model_uses_coin_cmd_when_pulp_cbc_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(pulp, "PULP_CBC_CMD", FailingPulpCbcCmd)
    monkeypatch.setattr(pulp, "COIN_CMD", RecordingCoinCmd)
    RecordingCoinCmd.calls = []
    model = FakeLpProblem()

    result = solve_pulp_model(model, lp_path=tmp_path / "model.lp", msg=False, time_limit=7)

    assert result["status"] == "Optimal"
    assert result["objective"] == 3.0
    assert result["lp_path"].endswith("model.lp")
    assert isinstance(model.solved_with, RecordingCoinCmd)
    assert RecordingCoinCmd.calls[0][1]["msg"] is False
    assert RecordingCoinCmd.calls[0][1]["timeLimit"] == 7


def test_execute_generated_code_ignores_main_block_solver_and_uses_project_solver(tmp_path):
    generated_code = textwrap.dedent(
        """
        import os
        import pulp


        def build_model():
            prob = pulp.LpProblem('unit_executor', pulp.LpMinimize)
            x = pulp.LpVariable('x', lowBound=0)
            prob += x, 'objective'
            prob += x >= 1, 'minimum_x'
            return prob


        if __name__ == '__main__':
            raise RuntimeError('executor must not run candidate __main__ block')
            prob = build_model()
            if os.environ.get('OUTPUT_LP_PATH'):
                prob.writeLP(os.environ['OUTPUT_LP_PATH'])
            prob.solve(pulp.PULP_CBC_CMD(msg=False))
        """
    )

    result = execute_generated_code(generated_code, tmp_path, candidate_id="c0", timeout=10)

    assert result["executable"] is True
    assert result["status"] == "Optimal"
    assert result["objective"] == 1.0
    assert result["lp_path"] is not None
    assert result["solver_lp_export_time"] is not None
    assert result["solver_time"] is not None
    assert result["error"] is None


def test_execute_generated_code_ignores_top_level_candidate_solver_and_uses_project_solver(tmp_path):
    generated_code = textwrap.dedent(
        """
        import pulp


        def build_model():
            prob = pulp.LpProblem('unit_executor_top_level', pulp.LpMinimize)
            x = pulp.LpVariable('x', lowBound=0)
            prob += x, 'objective'
            prob += x >= 2, 'minimum_x'
            return prob


        model = build_model()
        raise RuntimeError('executor must not run top-level candidate solver/export code')
        status_code = model.solve(pulp.PULP_CBC_CMD(msg=False))
        """
    )

    result = execute_generated_code(generated_code, tmp_path, candidate_id="c_top", timeout=10)

    assert result["executable"] is True
    assert result["status"] == "Optimal"
    assert result["objective"] == 2.0
    assert result["lp_path"] is not None
    assert result["error"] is None


def test_evaluate_candidate_runtime_fields_are_numeric_when_execution_or_parse_fails(tmp_path):
    candidate = {
        "problem_id": "p0",
        "candidate_id": "c0",
        "method": "unit",
        "generated_code": "def build_model():\n    raise RuntimeError('boom before LP')\n",
    }
    reference = {
        "problem_type": "single_period_newsvendor",
        "difficulty": "easy",
        "expected_structures": {},
        "reference_objective": 1.0,
        "reference_status": "Optimal",
    }

    row = evaluate_candidate(candidate, reference, work_dir=tmp_path, timeout=10)

    assert row["execution"]["executable"] is False
    assert row["runtime"]["code_execution_time"] is not None
    assert row["runtime"]["solver_lp_export_time"] is not None
    assert row["runtime"]["solver_time"] is not None
    assert row["runtime"]["lp_parse_time"] == 0.0
    assert row["runtime"]["structure_check_time"] == 0.0
