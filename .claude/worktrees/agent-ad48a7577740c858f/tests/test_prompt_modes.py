from replenishverifier.llm.prompt_builder import build_chat_messages, build_prompt
from replenishverifier.llm.run_generation import render_prompt


class DummyTokenizer:
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert tokenize is False
        assert add_generation_prompt is True
        return "\n".join(message["content"] for message in messages)


def _sample():
    return {
        "id": "p0",
        "problem_type": "fixed_order_cost_big_m",
        "difficulty": "hard",
        "natural_language": "Plan replenishment with setup decisions.",
        "parameters": {"periods": 2, "demand": [3, 4]},
        "expected_structures": {"inventory_balance": True, "big_m_constraint": True, "fixed_order_cost": True},
    }


def test_structured_prompt_exposes_expected_structures_for_guided_ablation():
    prompt = build_prompt(_sample(), prompt_type="structured")
    assert "Expected high-level modeling structures as JSON" in prompt
    assert "inventory_balance" in prompt
    assert "big_m_constraint" in prompt
    assert "fixed_order_cost" in prompt


def test_plain_prompt_hides_expected_structures_and_specific_structure_labels():
    prompt = build_prompt(_sample(), prompt_type="plain")
    assert "Expected high-level modeling structures" not in prompt
    assert "inventory_balance" not in prompt
    assert "big_m_constraint" not in prompt
    assert "fixed_order_cost" not in prompt
    assert "Parameters as JSON" in prompt
    assert "Plan replenishment with setup decisions." in prompt


def test_hidden_verifier_prompt_hides_expected_structures_but_keeps_io_contract():
    prompt = build_prompt(_sample(), prompt_type="hidden_verifier")
    assert "Expected high-level modeling structures" not in prompt
    assert "inventory_balance" not in prompt
    assert "big_m_constraint" not in prompt
    assert "fixed_order_cost" not in prompt
    assert "OUTPUT_LP_PATH" in prompt
    assert "build_model()" in prompt
    assert "explicitly name every PuLP constraint" in prompt


def test_build_chat_messages_passes_prompt_type():
    messages = build_chat_messages(_sample(), prompt_type="plain")
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Expected high-level modeling structures" not in messages[1]["content"]


def test_render_prompt_uses_prompt_type_with_chat_template():
    rendered = render_prompt(DummyTokenizer(), _sample(), use_chat_template=True, prompt_type="hidden_verifier")
    assert "OUTPUT_LP_PATH" in rendered
    assert "Expected high-level modeling structures" not in rendered
    assert "big_m_constraint" not in rendered


def test_unknown_prompt_type_raises_value_error():
    try:
        build_prompt(_sample(), prompt_type="unknown")
    except ValueError as exc:
        assert "prompt_type" in str(exc)
    else:
        raise AssertionError("build_prompt should reject unknown prompt_type")


class ThinkingAwareTokenizer:
    def __init__(self):
        self.enable_thinking_seen = None

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=True):
        self.enable_thinking_seen = enable_thinking
        assert tokenize is False
        assert add_generation_prompt is True
        return "\n".join(message["content"] for message in messages)


class ThinkingUnsupportedTokenizer:
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert tokenize is False
        assert add_generation_prompt is True
        return "fallback-ok"


def test_prompt_explicitly_forbids_think_markdown_and_requires_import_pulp_first():
    prompt = build_prompt(_sample(), prompt_type="hidden_verifier")
    assert "build_model()" in prompt
    assert "return a pulp.LpProblem" in prompt
    assert "Do not output Markdown" in prompt
    assert "must be importable as a Python module" in prompt
    assert "Do not output <think>" in prompt
    assert "The first line of your answer must be exactly: import pulp" in prompt


def test_render_prompt_disables_thinking_when_supported():
    tokenizer = ThinkingAwareTokenizer()

    render_prompt(tokenizer, _sample(), use_chat_template=True, prompt_type="hidden_verifier")

    assert tokenizer.enable_thinking_seen is False


def test_render_prompt_falls_back_when_enable_thinking_is_unsupported():
    rendered = render_prompt(ThinkingUnsupportedTokenizer(), _sample(), use_chat_template=True, prompt_type="hidden_verifier")

    assert rendered == "fallback-ok"
