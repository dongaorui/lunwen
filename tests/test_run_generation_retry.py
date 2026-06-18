from replenishverifier.utils.io import read_jsonl, write_jsonl


def _valid_code():
    return '''import pulp


def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x, "total_cost"
    prob += x >= 1, "constraint_0"
    return prob
'''


class FakeTokenizer:
    pad_token = None
    eos_token = "</s>"
    eos_token_id = 1
    pad_token_id = 1

    def apply_chat_template(self, *args, **kwargs):
        return "prompt"


class FakeModel:
    pass


def test_generation_retries_until_static_valid(monkeypatch, tmp_path):
    from replenishverifier.llm import run_generation as module

    benchmark_path = tmp_path / "benchmark.jsonl"
    out_path = tmp_path / "candidates.jsonl"
    write_jsonl(benchmark_path, [{"id": "p0", "problem_type": "single_period_newsvendor", "prompt": "x"}])

    outputs = iter(["<think>reasoning</think> not code", _valid_code()])
    monkeypatch.setattr(module, "load_model_and_tokenizer", lambda *args, **kwargs: (FakeModel(), FakeTokenizer()))
    monkeypatch.setattr(module, "generate_one", lambda *args, **kwargs: next(outputs))

    rows = module.run_generation(
        benchmark_path=benchmark_path,
        out_path=out_path,
        model_name_or_path="fake-model",
        k=1,
        retry_on_invalid_code=True,
        require_static_valid_code=True,
        max_generation_attempts_per_candidate=3,
    )

    row = rows[0]
    assert row["attempt_count"] == 2
    assert row["attempts"][0]["raw_contains_think"] is True
    assert row["attempts"][0]["accepted"] is False
    assert row["attempts"][1]["accepted"] is True
    assert row["code_output_format_valid"] is True
    assert row["generated_code"].startswith("import pulp")
    assert read_jsonl(out_path)[0]["attempt_count"] == 2


def test_generation_saves_final_candidate_when_all_attempts_invalid(monkeypatch, tmp_path):
    from replenishverifier.llm import run_generation as module

    benchmark_path = tmp_path / "benchmark.jsonl"
    out_path = tmp_path / "candidates.jsonl"
    write_jsonl(benchmark_path, [{"id": "p0", "problem_type": "single_period_newsvendor", "prompt": "x"}])

    monkeypatch.setattr(module, "load_model_and_tokenizer", lambda *args, **kwargs: (FakeModel(), FakeTokenizer()))
    monkeypatch.setattr(module, "generate_one", lambda *args, **kwargs: "<think>still not code</think>")

    rows = module.run_generation(
        benchmark_path=benchmark_path,
        out_path=out_path,
        model_name_or_path="fake-model",
        k=1,
        retry_on_invalid_code=True,
        require_static_valid_code=True,
        max_generation_attempts_per_candidate=2,
    )

    row = rows[0]
    assert row["attempt_count"] == 2
    assert len(row["attempts"]) == 2
    assert row["attempts"][-1]["accepted"] is False
    assert row["code_output_format_valid"] is False
    assert row["generated_code"] == ""
