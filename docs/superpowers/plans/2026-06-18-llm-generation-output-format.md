# LLM Generation Output Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make real LLM generation save runner-compatible PuLP Python code instead of explanatory text whenever the model output contains recoverable code.

**Architecture:** Keep the existing generation flow and strengthen three seams: prompt contract, output extraction, and lightweight format validity metadata. `run_generation.py` continues to call the extractor before writing JSONL; `code_output_format_valid` remains a generic candidate-observable signal and gains stricter syntax checks.

**Tech Stack:** Python 3.10+, PuLP, pytest, transformers tokenizer chat templates when installed.

## Global Constraints

- Do not delete or modify existing experiment results.
- Do not change benchmark generation logic.
- Do not change evaluation metric definitions.
- Do not run real LLM generation or large experiments.
- Do not introduce new large dependencies.
- Do not execute untrusted generated code during generation-time validation.
- Communicate with the user in Chinese by default.

---

## File Structure

- Modify `replenishverifier/llm/prompt_builder.py`: strengthen the prompt contract and include the runner-compatible `build_model()` template.
- Modify `replenishverifier/llm/code_extractor.py`: add `extract_python_code(text: str) -> str` and keep `extract_code(text)` as the compatibility wrapper.
- Modify `replenishverifier/experiments/baselines.py`: strengthen `code_output_format_valid(generated_code)` using syntax parsing and Markdown-fence rejection.
- Modify `replenishverifier/llm/run_generation.py`: save `code_output_format_valid` and try `enable_thinking=False` in chat templates when supported.
- Create `tests/test_code_extractor.py`: focused extractor and syntax tests.
- Modify `tests/test_prompt_modes.py`: prompt contract and chat-template thinking tests.
- Modify `tests/test_strong_baselines.py`: adjust/add tests for stricter format validity.

---

### Task 1: Strengthen Code Extraction

**Files:**
- Modify: `replenishverifier/llm/code_extractor.py`
- Create: `tests/test_code_extractor.py`

**Interfaces:**
- Consumes: raw LLM response text as `str | None`.
- Produces: `extract_python_code(text: str) -> str` and existing `extract_code(text) -> str` returning cleaned Python-like source with one trailing newline.

- [ ] **Step 1: Write failing extractor tests**

Create `tests/test_code_extractor.py` with:

```python
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
```

- [ ] **Step 2: Run extractor tests to verify they fail**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_code_extractor.py -q
```

Expected: FAIL because `extract_python_code` does not exist yet.

- [ ] **Step 3: Implement extractor**

Replace `replenishverifier/llm/code_extractor.py` with:

```python
import re


CODE_START_MARKERS = [
    "import pulp",
    "from pulp import",
    "def build_model",
    "model = pulp.LpProblem",
    "model= pulp.LpProblem",
]

TRAILING_TEXT_MARKERS = [
    "\n# Explanation",
    "\nExplanation:",
    "\nNotes:",
    "\n```",
]


def _normalize_code(code):
    cleaned = code.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:python|py)?\s*\n?", "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned + "\n" if cleaned else ""


def _strip_trailing_explanation(code):
    stop_positions = [code.find(marker) for marker in TRAILING_TEXT_MARKERS if code.find(marker) > 0]
    if stop_positions:
        return code[: min(stop_positions)]
    return code


def extract_python_code(text):
    """Extract Python code from an LLM response without executing it."""
    if text is None:
        return ""

    python_blocks = re.findall(r"```(?:python|py)\s*\n(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if python_blocks:
        return _normalize_code(python_blocks[0])

    any_blocks = re.findall(r"```\s*\n(.*?)```", text, flags=re.DOTALL)
    if any_blocks:
        return _normalize_code(any_blocks[0])

    starts = [text.find(marker) for marker in CODE_START_MARKERS if text.find(marker) >= 0]
    if starts:
        candidate = text[min(starts):]
        return _normalize_code(_strip_trailing_explanation(candidate))

    return _normalize_code(text)


def extract_code(text):
    return extract_python_code(text)
```

- [ ] **Step 4: Run extractor tests to verify they pass**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_code_extractor.py -q
```

Expected: PASS.

---

### Task 2: Strengthen Prompt Contract and Chat Template Thinking Control

**Files:**
- Modify: `replenishverifier/llm/prompt_builder.py`
- Modify: `replenishverifier/llm/run_generation.py`
- Modify: `tests/test_prompt_modes.py`

**Interfaces:**
- Consumes: existing `build_prompt(sample, prompt_type="hidden_verifier")` and `render_prompt(tokenizer, sample, use_chat_template=True, prompt_type="hidden_verifier")`.
- Produces: prompts containing explicit runner contract and `render_prompt` that attempts `enable_thinking=False` before fallback.

- [ ] **Step 1: Add failing prompt and chat-template tests**

Append to `tests/test_prompt_modes.py`:

```python

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


def test_prompt_explicitly_forbids_markdown_and_requires_lp_problem_return():
    prompt = build_prompt(_sample(), prompt_type="hidden_verifier")
    assert "build_model()" in prompt
    assert "return a pulp.LpProblem" in prompt
    assert "Do not output Markdown" in prompt
    assert "must be importable as a Python module" in prompt


def test_render_prompt_disables_thinking_when_supported():
    tokenizer = ThinkingAwareTokenizer()

    render_prompt(tokenizer, _sample(), use_chat_template=True, prompt_type="hidden_verifier")

    assert tokenizer.enable_thinking_seen is False


def test_render_prompt_falls_back_when_enable_thinking_is_unsupported():
    rendered = render_prompt(ThinkingUnsupportedTokenizer(), _sample(), use_chat_template=True, prompt_type="hidden_verifier")

    assert rendered == "fallback-ok"
```

- [ ] **Step 2: Run prompt tests to verify they fail**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_prompt_modes.py -q
```

Expected: FAIL because the exact prompt strings and `enable_thinking=False` behavior are not implemented yet.

- [ ] **Step 3: Strengthen prompt requirements**

In `replenishverifier/llm/prompt_builder.py`, replace `PULP_INTERFACE_REQUIREMENTS` with:

```python
PULP_INTERFACE_REQUIREMENTS = """Hard output and runner-interface requirements:
1. Output only plain Python source code. Do not output Markdown fences, explanations, natural-language reasoning, or multiple alternatives.
2. The generated file must be importable as a Python module.
3. Define build_model() with no arguments. build_model() must return a pulp.LpProblem object.
4. A global model = pulp.LpProblem(...) object is acceptable only as a secondary runner-compatible interface; build_model() is preferred.
5. Use PuLP for modeling and include import pulp.
6. Build a complete objective and all required constraints inside build_model().
7. If you include a main block, it may call build_model(), write OUTPUT_LP_PATH when present, solve with pulp.PULP_CBC_CMD(msg=False), and print STATUS and OBJECTIVE.
8. Do not output Markdown. Do not wrap the answer in ```python or ``` fences.

Required format template:
import pulp

def build_model():
    prob = pulp.LpProblem("replenishment_model", pulp.LpMinimize)

    # Define decision variables here

    # Define objective here
    prob += ...

    # Define constraints here

    return prob

Replace the template placeholders with complete executable PuLP code for the given problem.
"""
```

- [ ] **Step 4: Add chat-template thinking fallback**

In `replenishverifier/llm/run_generation.py`, replace the `apply_chat_template` block in `render_prompt()` with:

```python
    if use_chat_template and hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            try:
                return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            except Exception:
                LOGGER.warning("Tokenizer chat template failed; falling back to plain prompt.")
        except Exception:
            LOGGER.warning("Tokenizer chat template failed; falling back to plain prompt.")
```

Keep the final fallback line:

```python
    return build_prompt(sample, prompt_type=prompt_type)
```

- [ ] **Step 5: Run prompt tests to verify they pass**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_prompt_modes.py -q
```

Expected: PASS.

---

### Task 3: Add Format Validity Metadata

**Files:**
- Modify: `replenishverifier/experiments/baselines.py`
- Modify: `replenishverifier/llm/run_generation.py`
- Modify: `tests/test_strong_baselines.py`

**Interfaces:**
- Consumes: `generated_code: str`.
- Produces: stricter `code_output_format_valid(generated_code) -> bool`; generated candidate rows include boolean `code_output_format_valid`.

- [ ] **Step 1: Add failing format validity tests**

Append to `tests/test_strong_baselines.py`:

```python

def test_code_output_format_rejects_markdown_fences():
    code = """```python
import pulp

def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    return prob
```"""

    assert code_output_format_valid(code) is False


def test_code_output_format_rejects_syntax_errors():
    code = """import pulp

def build_model(:
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    return prob
"""

    assert code_output_format_valid(code) is False


def test_code_output_format_accepts_runner_compatible_build_model():
    code = """import pulp

def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x
    return prob
"""

    assert code_output_format_valid(code) is True
```

- [ ] **Step 2: Run baseline tests to verify at least one fails**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_strong_baselines.py -q
```

Expected: FAIL because Markdown-fenced code currently passes the surface check.

- [ ] **Step 3: Strengthen `code_output_format_valid`**

In `replenishverifier/experiments/baselines.py`, add `import ast` at the top and replace `code_output_format_valid` with:

```python
def code_output_format_valid(generated_code):
    """Generic code-format validity signal used by OR-R1-like voting.

    This intentionally checks only solver-code surface format. It does not inspect
    replenishment-specific structures such as inventory balance or Big-M links.
    """
    code = generated_code or ""
    if not code.strip():
        return False
    if "```" in code:
        return False

    has_runner_entry = "def build_model" in code or "model =" in code or "model=" in code
    has_pulp_import = "import pulp" in code or "from pulp import" in code
    has_lp_problem = "pulp.LpProblem" in code or ("LpProblem" in code and has_pulp_import)
    if not (has_runner_entry and has_pulp_import and has_lp_problem):
        return False

    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True
```

- [ ] **Step 4: Save validity field in generation rows**

In `replenishverifier/llm/run_generation.py`:

Add import:

```python
from replenishverifier.experiments.baselines import code_output_format_valid
```

Initialize each row with:

```python
                "code_output_format_valid": False,
```

After extracting code, add:

```python
                row["code_output_format_valid"] = code_output_format_valid(row["generated_code"])
```

- [ ] **Step 5: Run baseline and prompt/extractor tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_strong_baselines.py tests/test_prompt_modes.py tests/test_code_extractor.py -q
```

Expected: PASS.

---

### Task 4: Full Verification and Planning-File Update

**Files:**
- Modify: `progress.md`
- Optionally modify: `findings.md` only if a durable project fact is discovered during implementation.

**Interfaces:**
- Consumes: all implementation from Tasks 1-3.
- Produces: verified working tree with tests passing and planning log updated.

- [ ] **Step 1: Run full requested test command**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Update `progress.md`**

Append this entry to `progress.md` with the actual test result filled in from Step 1:

```markdown

## 2026-06-18 — LLM generation output format repair

### User request

The user asked to fix real LLM generation output formatting after a Qwen3-8B K=4 run produced mostly explanatory text instead of runner-compatible PuLP code.

### Actions completed

1. Strengthened generation prompts so candidates must be plain importable Python modules and must define `build_model()` returning a `pulp.LpProblem` or a global PuLP `model`.
2. Added robust LLM output extraction for Python fences, generic fences, and explanatory prefixes before code markers such as `import pulp` and `def build_model`.
3. Added generation-time `code_output_format_valid` metadata and strengthened the existing generic format check with Markdown-fence rejection and `ast.parse`.
4. Added a best-effort `enable_thinking=False` chat-template call for tokenizers that support it, with fallback for tokenizers that do not.
5. Added focused tests for extraction, prompt contract, chat-template fallback, and stricter format validation.

### Verification

- Full suite command: `PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
- Result: `<replace with exact pytest result>`

### Notes

No existing experiment results were deleted or modified. No benchmark generation logic, evaluation metric definitions, large dependencies, or real LLM experiment runs were introduced.
```

- [ ] **Step 3: Inspect changed files**

Run:

```bash
git diff -- replenishverifier/llm/prompt_builder.py replenishverifier/llm/code_extractor.py replenishverifier/llm/run_generation.py replenishverifier/experiments/baselines.py tests/test_code_extractor.py tests/test_prompt_modes.py tests/test_strong_baselines.py progress.md docs/superpowers/specs/2026-06-18-llm-generation-output-format-design.md docs/superpowers/plans/2026-06-18-llm-generation-output-format.md
```

Expected: diff only contains the planned prompt, extraction, validation, tests, and planning-document changes.

- [ ] **Step 4: Do not commit unless the user explicitly asks**

No command is run in this step. The repository instruction from the harness says commits require explicit user request.

---

## Self-Review

### Spec coverage

- Prompt contract: Task 2.
- Code extraction: Task 1.
- Format validity metadata: Task 3.
- Qwen thinking control: Task 2.
- Tests: Tasks 1-3.
- Full requested verification: Task 4.
- No large experiment / no result deletion / no benchmark or metric changes: Global Constraints and Task 4.

### Placeholder scan

The plan contains no TBD/TODO placeholders. The only replacement text is the explicit instruction to fill in the actual pytest result in `progress.md` after running the command.

### Type consistency

- `extract_python_code(text)` and `extract_code(text)` both return strings.
- `code_output_format_valid(generated_code)` returns bool and is imported by `run_generation.py`.
- `render_prompt(...)` signature remains unchanged.
