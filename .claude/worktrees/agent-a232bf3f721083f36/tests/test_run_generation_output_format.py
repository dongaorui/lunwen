from replenishverifier.llm import run_generation as generation_module
from replenishverifier.utils.io import read_jsonl, write_jsonl


class DummyTokenizer:
    pad_token_id = 0
    eos_token_id = 0

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=False):
        assert enable_thinking is False
        return "prompt"


class DummyModel:
    pass


VALID_CODE = """import pulp


def build_model():
    prob = pulp.LpProblem("replenishment_model", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x
    return prob
"""


def test_run_generation_saves_clean_code_in_generated_text_and_keeps_raw_text(tmp_path, monkeypatch):
    benchmark = tmp_path / "benchmark.jsonl"
    out = tmp_path / "candidates.jsonl"
    write_jsonl(
        benchmark,
        [
            {
                "id": "p0",
                "problem_type": "single_period_newsvendor",
                "difficulty": "easy",
                "natural_language": "Build a tiny replenishment model.",
                "parameters": {},
            }
        ],
    )

    raw_output = "<think>reasoning...</think>\n" + VALID_CODE
    monkeypatch.setattr(generation_module, "load_model_and_tokenizer", lambda *args, **kwargs: (DummyModel(), DummyTokenizer()))
    monkeypatch.setattr(generation_module, "generate_one", lambda *args, **kwargs: raw_output)

    rows = generation_module.run_generation(
        benchmark_path=benchmark,
        out_path=out,
        model_name_or_path="dummy-model",
        k=1,
        seed=42,
    )

    assert rows[0]["raw_generated_text"] == raw_output
    assert rows[0]["generated_text"].startswith("import pulp")
    assert rows[0]["generated_code"] == rows[0]["generated_text"]
    assert "<think>" not in rows[0]["generated_text"]
    assert rows[0]["code_output_format_valid"] is True
    assert read_jsonl(out)[0]["generated_text"] == rows[0]["generated_text"]


def test_run_generation_adds_static_validation_fields(monkeypatch, tmp_path):
    benchmark_path = tmp_path / "benchmark.jsonl"
    out_path = tmp_path / "candidates.jsonl"
    write_jsonl(
        benchmark_path,
        [
            {
                "id": "p0",
                "problem_type": "single_item_multi_period",
                "prompt": "make model",
            }
        ],
    )

    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x, "total_cost"
    prob += x >= 1, "demand_constraint"
    return prob
'''

    monkeypatch.setattr(generation_module, "load_model_and_tokenizer", lambda *args, **kwargs: (DummyModel(), DummyTokenizer()))
    monkeypatch.setattr(generation_module, "generate_one", lambda *args, **kwargs: code)

    rows = generation_module.run_generation(
        benchmark_path=benchmark_path,
        out_path=out_path,
        model_name_or_path="fake-model",
        k=1,
    )

    assert rows[0]["has_build_model"] is True
    assert rows[0]["has_pulp_problem"] is True
    assert rows[0]["static_validation_score"] == 1.0
    assert rows[0]["static_validation_errors"] == []
