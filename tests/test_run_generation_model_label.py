from replenishverifier.llm import run_generation as rg
from replenishverifier.utils.io import write_jsonl


class DummyTokenizer:
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=False):
        return "PROMPT"


class DummyModel:
    pass


def _benchmark(tmp_path):
    path = tmp_path / "benchmark.jsonl"
    write_jsonl(path, [{"id": "p0", "problem_type": "single_item_multi_period", "prompt": "Build model"}])
    return path


def _patch_generation(monkeypatch):
    monkeypatch.setattr(rg, "load_model_and_tokenizer", lambda *args, **kwargs: (DummyModel(), DummyTokenizer()))
    monkeypatch.setattr(
        rg,
        "generate_one",
        lambda *args, **kwargs: (
            "import pulp\n\n"
            "def build_model():\n"
            "    model = pulp.LpProblem('x', pulp.LpMinimize)\n"
            "    q = pulp.LpVariable('Q_0', lowBound=0)\n"
            "    model += q, 'total_cost'\n"
            "    model += q >= 0, 'nonnegative_q'\n"
            "    return model\n"
        ),
    )


def test_model_label_controls_candidate_id_and_metadata(tmp_path, monkeypatch):
    _patch_generation(monkeypatch)
    out = tmp_path / "candidates.jsonl"

    rows = rg.run_generation(
        benchmark_path=_benchmark(tmp_path),
        out_path=out,
        model_name_or_path="Qwen/Qwen3-8B",
        model_label="qwen3_8b_k4_50_v3",
        k=2,
        use_chat_template=True,
    )

    assert [row["candidate_id"] for row in rows] == ["qwen3_8b_k4_50_v3_k0", "qwen3_8b_k4_50_v3_k1"]
    assert rows[0]["model"] == "Qwen/Qwen3-8B"
    assert rows[0]["model_name_or_path"] == "Qwen/Qwen3-8B"
    assert rows[0]["model_label"] == "qwen3_8b_k4_50_v3"
    assert rows[0]["attempt_count"] == 1
    assert rows[0]["generation_time_sec"] >= 0.0
    assert rows[0]["code_output_format_valid"] is True
    assert "static_validation" in rows[0]


def test_missing_model_label_keeps_legacy_candidate_id(tmp_path, monkeypatch):
    _patch_generation(monkeypatch)
    out = tmp_path / "candidates.jsonl"

    rows = rg.run_generation(
        benchmark_path=_benchmark(tmp_path),
        out_path=out,
        model_name_or_path="Qwen/Qwen3-8B",
        k=1,
        use_chat_template=True,
    )

    assert rows[0]["candidate_id"] == "Qwen3-8B_k0"
    assert rows[0].get("model_label") is None
    assert rows[0]["model"] == "Qwen/Qwen3-8B"
