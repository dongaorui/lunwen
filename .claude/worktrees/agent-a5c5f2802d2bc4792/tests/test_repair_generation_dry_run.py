from replenishverifier.llm.prompt_builder import build_prompt, build_repair_prompt
from replenishverifier.llm.run_repair_generation import render_repair_prompt, run_repair_generation
from replenishverifier.utils.io import write_jsonl, read_jsonl


def test_prompt_builder_requires_explicit_constraint_names():
    sample = {"id": "p0", "parameters": {}, "expected_structures": {}, "natural_language": "test"}
    prompt = build_prompt(sample)
    assert "explicitly name every PuLP constraint" in prompt
    assert "_C1/_C2" in prompt
    structured = build_prompt(sample, prompt_type="structured")
    assert "CRITICAL REGULATION" in structured
    assert "MUST explicitly provide string names for ALL constraints" in structured
    repair = build_repair_prompt(sample, {"feedback": "fix"})
    assert "Do NOT write anonymous constraints" in repair


class RepairThinkingAwareTokenizer:
    def __init__(self):
        self.enable_thinking_seen = None

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=True):
        self.enable_thinking_seen = enable_thinking
        assert tokenize is False
        assert add_generation_prompt is True
        return "repair-prompt"


class RepairThinkingUnsupportedTokenizer:
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert tokenize is False
        assert add_generation_prompt is True
        return "repair-fallback-ok"


def test_render_repair_prompt_disables_thinking_when_supported():
    tokenizer = RepairThinkingAwareTokenizer()

    rendered = render_repair_prompt(tokenizer, {"id": "p0", "parameters": {}, "natural_language": "test"}, {"feedback": "fix"})

    assert rendered == "repair-prompt"
    assert tokenizer.enable_thinking_seen is False


def test_render_repair_prompt_falls_back_when_enable_thinking_is_unsupported():
    rendered = render_repair_prompt(
        RepairThinkingUnsupportedTokenizer(),
        {"id": "p0", "parameters": {}, "natural_language": "test"},
        {"feedback": "fix"},
    )

    assert rendered == "repair-fallback-ok"


def test_repair_generation_dry_run_outputs_uniform_placeholder(tmp_path):
    benchmark = tmp_path / "benchmark.jsonl"
    repairs = tmp_path / "repair_prompts.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    out = tmp_path / "out.jsonl"
    write_jsonl(benchmark, [{"id": "p0", "problem_type": "single", "difficulty": "easy", "natural_language": "minimize", "parameters": {}}])
    write_jsonl(repairs, [{"problem_id": "p0", "candidate_id": "c0", "feedback": "Add inventory balance."}])
    write_jsonl(candidates, [{"problem_id": "p0", "candidate_id": "c0", "generated_code": "import pulp\n"}])

    rows = run_repair_generation(
        benchmark_path=benchmark,
        repair_prompts_path=repairs,
        candidates_path=candidates,
        out_path=out,
        model_name_or_path="dummy",
        dry_run=True,
    )

    assert len(rows) == 1
    assert rows[0]["dry_run"] is True
    assert rows[0]["generated_code"]
    assert "dry_run_placeholder_constraint" in rows[0]["generated_code"]
    saved = read_jsonl(out)
    assert saved[0]["candidate_id"] == "repair_c0"


def test_generic_repair_dry_run_uses_generic_method(tmp_path):
    benchmark = tmp_path / "benchmark.jsonl"
    repairs = tmp_path / "repair_prompts.jsonl"
    candidates = tmp_path / "candidates.jsonl"
    out = tmp_path / "out.jsonl"
    write_jsonl(benchmark, [{"id": "p0", "natural_language": "minimize", "parameters": {}}])
    write_jsonl(repairs, [{"problem_id": "p0", "candidate_id": "c0", "generic_repair_feedback": "Add objective."}])
    write_jsonl(candidates, [{"problem_id": "p0", "candidate_id": "c0", "generated_code": ""}])

    rows = run_repair_generation(
        benchmark_path=benchmark,
        repair_prompts_path=repairs,
        candidates_path=candidates,
        out_path=out,
        model_name_or_path="dummy",
        repair_type="generic",
        dry_run=True,
    )
    assert rows[0]["method"] == "generic_llm_repair"
    assert rows[0]["candidate_id"] == "generic_repair_c0"
    assert "Generic feedback" in rows[0]["prompt"]
