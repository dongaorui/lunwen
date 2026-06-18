import ast

from replenishverifier.llm.code_extractor import extract_code, extract_python_code


VALID_CODE = """import pulp


def build_model():
    prob = pulp.LpProblem("replenishment_model", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x
    return prob
"""


def test_extract_python_code_from_python_fence():
    text = f"Here is the model:\n```python\n{VALID_CODE}```\n"

    code = extract_python_code(text)

    assert code.startswith("import pulp")
    assert "```" not in code
    ast.parse(code)


def test_extract_python_code_from_explanation_then_import_pulp():
    text = "So, in the code, we need variables first.\n" + VALID_CODE

    code = extract_python_code(text)

    assert code.startswith("import pulp")
    assert "So, in the code" not in code
    assert "```" not in code
    ast.parse(code)


def test_extract_code_keeps_backward_compatible_wrapper():
    assert extract_code(VALID_CODE) == extract_python_code(VALID_CODE)


def test_extract_python_code_from_build_model_marker_without_import_prefix():
    text = "Explanation first.\n\ndef build_model():\n    return None\n"

    code = extract_python_code(text)

    assert code.startswith("def build_model")
    assert "Explanation first" not in code
    ast.parse(code)


def test_extract_python_code_strips_closed_qwen_thinking_before_import_pulp():
    text = "<think>reasoning...</think>\n" + VALID_CODE

    code = extract_python_code(text)

    assert code.startswith("import pulp")
    assert "<think>" not in code
    assert "reasoning" not in code
    ast.parse(code)


def test_extract_python_code_strips_unclosed_qwen_thinking_before_import_pulp():
    text = "<think>reasoning without closing tag...\nMore thoughts.\n" + VALID_CODE

    code = extract_python_code(text)

    assert code.startswith("import pulp")
    assert "<think>" not in code
    assert "reasoning" not in code
    ast.parse(code)


def test_extract_python_code_returns_empty_for_reasoning_without_code_start():
    text = "<think>reasoning only</think>\nI would create variables and constraints."

    code = extract_python_code(text)

    assert code == ""
