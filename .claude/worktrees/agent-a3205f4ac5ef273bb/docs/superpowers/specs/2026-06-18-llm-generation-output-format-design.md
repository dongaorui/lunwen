# LLM Generation Output Format Fix Design

## Goal

Fix real LLM generation candidates so saved `generated_code` is much more likely to satisfy the existing runner contract: importable Python code that defines a no-argument `build_model()` returning a PuLP `LpProblem`, or a global `model` PuLP problem.

This addresses the observed Qwen3-8B failure mode where most outputs are explanatory text instead of executable PuLP code.

## Scope

In scope:

- Strengthen generation prompts in `replenishverifier/llm/prompt_builder.py`.
- Make LLM output cleaning more robust in `replenishverifier/llm/code_extractor.py`.
- Save a lightweight `code_output_format_valid` field during generation.
- Reuse and strengthen the existing generic `code_output_format_valid` helper.
- Try to disable Qwen-style thinking in `apply_chat_template` without requiring tokenizer-specific support.
- Add focused unit tests.

Out of scope:

- Deleting or modifying existing experiment results.
- Changing benchmark generation.
- Changing evaluation metric definitions.
- Running real LLM generation or large experiments.
- Adding large dependencies.
- Executing untrusted generated code during generation-time validation.

## Design

### Prompt contract

Update `PULP_INTERFACE_REQUIREMENTS` so every generation prompt explicitly states:

- Output only plain Python source code.
- Do not output Markdown fences, explanations, natural-language reasoning, or multiple alternatives.
- The file must be importable as a Python module.
- Prefer defining `build_model()` with no arguments.
- `build_model()` must return a `pulp.LpProblem`.
- A global `model = pulp.LpProblem(...)` is acceptable only as an alternative runner-compatible interface.

Include a compact template:

```python
import pulp

def build_model():
    prob = pulp.LpProblem("replenishment_model", pulp.LpMinimize)

    # Define decision variables here

    # Define objective here
    prob += ...

    # Define constraints here

    return prob
```

The template is guidance only; final outputs must be complete executable code.

### Code extraction

Add `extract_python_code(text: str) -> str` and keep `extract_code()` as a compatibility wrapper.

Extraction order:

1. First fenced `python` or `py` block.
2. First generic fenced code block.
3. Text from the earliest supported code marker:
   - `import pulp`
   - `from pulp import`
   - `def build_model`
   - `model = pulp.LpProblem`
   - `model= pulp.LpProblem`
4. Original text as a last resort.

The function strips leading/trailing Markdown fences and common trailing explanation markers, but should not modify already-valid Python code beyond trimming outer whitespace and appending one newline.

### Format validity metadata

Strengthen the existing `replenishverifier.experiments.baselines.code_output_format_valid` helper so it returns true only when:

- code is non-empty;
- code has no Markdown fence;
- code contains `def build_model` or `model =`/`model=`;
- code contains a PuLP problem construction signal such as `pulp.LpProblem` or `LpProblem` with a PuLP import;
- `ast.parse(code)` succeeds.

During generation, after extracting `generated_code`, save:

```python
row["code_output_format_valid"] = code_output_format_valid(row["generated_code"])
```

If generation fails before code exists, leave the field false.

This metadata is diagnostic and selection-signal-compatible; it does not change reference-objective usage or evaluation metric definitions.

### Qwen thinking control

In `render_prompt()`, try `tokenizer.apply_chat_template(..., enable_thinking=False)` first. If the tokenizer or transformers version does not accept the parameter, fall back to the existing call without `enable_thinking`.

This should reduce Qwen thinking/explanatory output when supported, without breaking other tokenizers.

### Tests

Add focused tests for:

- extracting from a ```python fenced code block;
- extracting from explanatory text followed by `import pulp` code;
- cleaned code containing no ``` fences;
- cleaned code passing `ast.parse`;
- prompt text explicitly containing `build_model()`, `return a pulp.LpProblem`, and a no-Markdown/no-explanation constraint;
- chat template receives `enable_thinking=False` when supported and still works when unsupported.

Run the full suite with:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

## Why this should fix the observed failure

The failed Qwen candidates did not reach verifier logic because they were not importable PuLP programs. The prompt change makes the runner interface explicit before generation. The extraction change recovers valid code when the model still wraps it in Markdown or prefixes it with explanation. The format-valid flag exposes remaining invalid outputs immediately in the candidate JSONL, before evaluation.

## Small rerun recommendation after implementation

After tests pass, use a small benchmark slice such as `test_small.jsonl` or `--max_samples 2` with `k=1` or `k=2`, then inspect `generated_code` and `code_output_format_valid` before running full evaluation. If the small run has importable code and LP export succeeds, then proceed to a larger rerun.
