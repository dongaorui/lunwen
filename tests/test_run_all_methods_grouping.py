import inspect

from replenishverifier.experiments import run_all_methods
from replenishverifier.experiments.methods import APPENDIX_METHODS, MAIN_METHODS, METHODS
from replenishverifier.utils.io import write_jsonl


def _minimal_experiment_files(tmp_path):
    benchmark = tmp_path / "benchmark.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    write_jsonl(benchmark, [{"id": "p0", "problem_type": "single_period_newsvendor", "expected_structures": {}}])
    write_jsonl(candidates, [{"problem_id": "p0", "candidate_id": "c0", "generated_code": "import pulp\n"}])
    return benchmark, candidates


def test_run_experiments_accepts_appendix_methods_in_main_flag():
    signature = inspect.signature(run_all_methods.run_experiments)

    assert "appendix_methods_in_main" in signature.parameters
    assert signature.parameters["appendix_methods_in_main"].default is False


def test_run_experiments_uses_main_methods_by_default(monkeypatch, tmp_path):
    benchmark, candidates = _minimal_experiment_files(tmp_path)
    selected_methods = []

    monkeypatch.setattr(run_all_methods, "evaluate_all_candidates", lambda *args, **kwargs: {"p0": []})
    monkeypatch.setattr(run_all_methods, "select_for_method", lambda method, *args, **kwargs: selected_methods.append(method) or [])
    monkeypatch.setattr(run_all_methods, "build_repair_prompts", lambda rows: [])
    monkeypatch.setattr(run_all_methods, "build_generic_repair_prompts", lambda rows: [])

    manifest = run_all_methods.run_experiments(benchmark, candidates, tmp_path / "out", k_values=[], demo_if_empty=False)

    assert selected_methods[: len(MAIN_METHODS)] == MAIN_METHODS
    assert not any(method in selected_methods[: len(MAIN_METHODS)] for method in APPENDIX_METHODS)
    assert manifest["main_methods"] == MAIN_METHODS
    assert manifest["appendix_methods_in_main"] is False


def test_run_experiments_can_include_appendix_methods_in_main(monkeypatch, tmp_path):
    benchmark, candidates = _minimal_experiment_files(tmp_path)
    selected_methods = []

    monkeypatch.setattr(run_all_methods, "evaluate_all_candidates", lambda *args, **kwargs: {"p0": []})
    monkeypatch.setattr(run_all_methods, "select_for_method", lambda method, *args, **kwargs: selected_methods.append(method) or [])
    monkeypatch.setattr(run_all_methods, "build_repair_prompts", lambda rows: [])
    monkeypatch.setattr(run_all_methods, "build_generic_repair_prompts", lambda rows: [])

    manifest = run_all_methods.run_experiments(
        benchmark,
        candidates,
        tmp_path / "out",
        k_values=[],
        demo_if_empty=False,
        appendix_methods_in_main=True,
    )

    assert selected_methods[: len(METHODS)] == METHODS
    assert manifest["main_methods"] == METHODS
    assert manifest["appendix_methods_in_main"] is True
