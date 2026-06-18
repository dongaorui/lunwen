# ReplenishVerifier Experiment Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Qwen3-8B experiment diagnosis, candidate quality signals, retry generation, no-reference selection, and optional repair while preserving the ReplenishVerifier leakage boundary.

**Architecture:** Add a shared candidate-observable quality-signal module and reuse it from generation, evaluation, diagnostics, and selection tie-breakers. Keep diagnostics/oracle analysis separate from formal selection, keep Direct unchanged, and keep true LLM repair off by default through the existing repair-generation path.

**Tech Stack:** Python 3.10+, pytest, PuLP LP artifacts, JSONL/CSV/Markdown experiment artifacts, existing `replenishverifier` modules, no large new dependencies.

## Global Constraints

- 与用户沟通默认使用中文。
- Formal candidate selection must not use `reference_objective`.
- Formal candidate selection must not use reference answer, reference LP, or reference status.
- `reference_objective` is allowed only for final evaluation metrics and oracle upper-bound diagnostics.
- Do not delete or overwrite existing experiment results.
- Do not upload, download, or bundle model weights.
- Do not introduce large new dependencies.
- Direct baseline must remain candidate-index-0 selection.
- Generic baselines must remain generic and must not use replenishment-specific structure penalties.
- Synthetic/demo smoke results are sanity checks only and must not be written as formal paper results.
- Repair may be called second-round LLM repair only after repaired candidates are generated and re-evaluated.
- Do not create git commits unless the user explicitly asks for commits; use the checkpoint steps to inspect status only.

---

## File Structure

- Create `replenishverifier/pipeline/quality_signals.py`
  - Owns static code validation and candidate-observable pattern signals.
  - Exposes `compute_static_validation(generated_code: str, problem_type: str | None = None) -> dict`.
  - Exposes helpers used by selection, such as `static_validation_score(row)` and `candidate_index(row)` if needed.

- Modify `replenishverifier/experiments/baselines.py`
  - Reuse `compute_static_validation()` in `code_output_format_valid()` so generation and baseline format checks stay consistent.
  - Keep the baseline docstring explicit that this is a generic code-format signal.

- Modify `replenishverifier/experiments/methods.py`
  - Attach `static_validation` fields to every evaluated candidate row.
  - Add critical-structure penalty and tie-breaker logic for structure-aware methods.
  - Preserve Direct behavior.
  - Keep generic baselines free of replenishment-specific penalties.

- Modify `replenishverifier/pipeline/scoring.py`
  - Add small pure helpers for critical missing-structure penalties if cleaner than keeping all selector logic in `methods.py`.
  - Do not introduce reference-objective selection logic.

- Modify `replenishverifier/llm/run_generation.py`
  - Add bounded retry CLI and attempt metadata.
  - Use `compute_static_validation()` on extracted code.

- Create `replenishverifier/experiments/diagnose_run.py`
  - Reads benchmark, candidate evaluations, and main results.
  - Writes diagnostic JSONL/CSV/Markdown artifacts.
  - Uses reference objective only for post-selection evaluation/oracle diagnostics.

- Modify `replenishverifier/llm/run_repair_generation.py`
  - Include static validation errors in rendered repair context when present.
  - Keep dry-run behavior and existing CLI compatibility.

- Optionally modify `replenishverifier/experiments/run_all_methods.py`
  - Add off-by-default flags for LLM repair orchestration only if doing so stays small.
  - If this becomes broad, keep repair as a documented separate command using `run_repair_generation.py`.

- Add tests:
  - `tests/test_static_validation.py`
  - `tests/test_run_generation_retry.py`
  - `tests/test_diagnose_run.py`
  - extend `tests/test_hard_selection_gate.py` or create `tests/test_selection_gating.py`
  - extend `tests/test_repair_generation_dry_run.py` if repair prompt context changes.

- Modify `progress.md`
  - Record completed implementation, tests, and no-large-experiment/no-result-deletion notes.

---

### Task 1: Add shared static validation quality signals

**Files:**
- Create: `replenishverifier/pipeline/quality_signals.py`
- Modify: `replenishverifier/experiments/baselines.py`
- Test: `tests/test_static_validation.py`

**Interfaces:**
- Produces: `compute_static_validation(generated_code: str, problem_type: str | None = None) -> dict`
- Produces fields: `has_build_model`, `has_pulp_problem`, `has_objective`, `has_constraints`, `has_inventory_balance_pattern`, `has_capacity_pattern`, `has_shortage_pattern`, `has_binary_order_pattern`, `has_big_m_pattern`, `has_fixed_order_cost_pattern`, `static_validation_errors`, `static_validation_score`
- Consumes: generated candidate code only; no reference artifacts.

- [ ] **Step 1: Write failing tests for valid code and pattern features**

Create `tests/test_static_validation.py` with this content:

```python
from replenishverifier.pipeline.quality_signals import compute_static_validation


def test_static_validation_accepts_runner_compatible_pulp_model():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("inventory", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", range(2), lowBound=0)
    inventory = pulp.LpVariable.dicts("inventory", range(2), lowBound=0)
    prob += 2 * order[0] + 3 * inventory[0], "total_cost"
    prob += inventory[0] == order[0] - 5, "inventory_balance_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="single_item_multi_period")

    assert result["has_build_model"] is True
    assert result["has_pulp_problem"] is True
    assert result["has_objective"] is True
    assert result["has_constraints"] is True
    assert result["has_inventory_balance_pattern"] is True
    assert result["static_validation_errors"] == []
    assert result["static_validation_score"] == 1.0


def test_static_validation_detects_capacity_shortage_big_m_and_fixed_cost_patterns():
    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("capacity", pulp.LpMinimize)
    order = pulp.LpVariable.dicts("order", range(2), lowBound=0)
    shortage = pulp.LpVariable.dicts("shortage", range(2), lowBound=0)
    y = pulp.LpVariable.dicts("order_binary", range(2), cat="Binary")
    fixed_order_cost = 10
    big_m = 100
    prob += fixed_order_cost * y[0] + 4 * shortage[0], "total_cost"
    prob += order[0] <= 50, "capacity_constraint_0"
    prob += order[0] <= big_m * y[0], "big_m_link_0"
    return prob
'''

    result = compute_static_validation(code, problem_type="fixed_order_cost_big_m")

    assert result["has_capacity_pattern"] is True
    assert result["has_shortage_pattern"] is True
    assert result["has_binary_order_pattern"] is True
    assert result["has_big_m_pattern"] is True
    assert result["has_fixed_order_cost_pattern"] is True
```

- [ ] **Step 2: Write failing tests for invalid code and errors**

Append to `tests/test_static_validation.py`:

```python

def test_static_validation_reports_missing_runner_contract():
    result = compute_static_validation("print('not a model')", problem_type="multi_item_capacity")

    assert result["has_build_model"] is False
    assert result["has_pulp_problem"] is False
    assert result["has_objective"] is False
    assert result["has_constraints"] is False
    assert "missing_build_model" in result["static_validation_errors"]
    assert "missing_pulp_lp_problem" in result["static_validation_errors"]
    assert result["static_validation_score"] < 0.5


def test_static_validation_reports_syntax_error():
    result = compute_static_validation("import pulp\ndef build_model(:", problem_type="single_period_newsvendor")

    assert "syntax_error" in result["static_validation_errors"]
    assert result["has_build_model"] is False
    assert result["static_validation_score"] == 0.0
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_static_validation.py -q
```

Expected: FAIL because `replenishverifier.pipeline.quality_signals` does not exist.

- [ ] **Step 4: Implement `quality_signals.py`**

Create `replenishverifier/pipeline/quality_signals.py`:

```python
import ast
import re


PATTERNS = {
    "inventory_balance": re.compile(r"inventory|balance|stock", re.IGNORECASE),
    "capacity": re.compile(r"capacity|cap_|_cap|limit|resource", re.IGNORECASE),
    "shortage": re.compile(r"shortage|backlog|unmet", re.IGNORECASE),
    "binary_order": re.compile(r"Binary|cat\s*=\s*['\"]Binary['\"]|order_binary|setup|open_order", re.IGNORECASE),
    "big_m": re.compile(r"big_m|bigm|\bM\b|\*\s*y|y\s*\*", re.IGNORECASE),
    "fixed_order_cost": re.compile(r"fixed_order|setup_cost|fixed_cost|ordering_fixed", re.IGNORECASE),
}


class _PulpModelVisitor(ast.NodeVisitor):
    def __init__(self):
        self.has_build_model = False
        self.has_pulp_problem = False
        self.has_objective = False
        self.has_constraints = False

    def visit_FunctionDef(self, node):
        if node.name == "build_model":
            self.has_build_model = True
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "LpProblem":
                self.has_pulp_problem = True
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Add):
            if isinstance(node.value, ast.Tuple) and len(node.value.elts) >= 2:
                self.has_constraints = True
            elif self.has_objective:
                self.has_constraints = True
            else:
                self.has_objective = True
        self.generic_visit(node)


def _base_result():
    return {
        "has_build_model": False,
        "has_pulp_problem": False,
        "has_objective": False,
        "has_constraints": False,
        "has_inventory_balance_pattern": False,
        "has_capacity_pattern": False,
        "has_shortage_pattern": False,
        "has_binary_order_pattern": False,
        "has_big_m_pattern": False,
        "has_fixed_order_cost_pattern": False,
        "static_validation_errors": [],
        "static_validation_score": 0.0,
    }


def _score(result):
    checks = [
        "has_build_model",
        "has_pulp_problem",
        "has_objective",
        "has_constraints",
    ]
    return sum(1.0 for key in checks if result[key]) / len(checks)


def compute_static_validation(generated_code: str, problem_type: str | None = None) -> dict:
    code = generated_code or ""
    result = _base_result()
    if not code.strip():
        result["static_validation_errors"].append("empty_code")
        return result
    if "```" in code:
        result["static_validation_errors"].append("contains_markdown_fence")

    try:
        tree = ast.parse(code)
    except SyntaxError:
        result["static_validation_errors"].append("syntax_error")
        return result

    visitor = _PulpModelVisitor()
    visitor.visit(tree)
    result["has_build_model"] = visitor.has_build_model or "def build_model" in code
    result["has_pulp_problem"] = visitor.has_pulp_problem or "pulp.LpProblem" in code
    result["has_objective"] = visitor.has_objective or "prob +=" in code or "model +=" in code
    result["has_constraints"] = visitor.has_constraints or bool(re.search(r"(<=|>=|==).*,\s*['\"]", code))
    result["has_inventory_balance_pattern"] = bool(PATTERNS["inventory_balance"].search(code))
    result["has_capacity_pattern"] = bool(PATTERNS["capacity"].search(code))
    result["has_shortage_pattern"] = bool(PATTERNS["shortage"].search(code))
    result["has_binary_order_pattern"] = bool(PATTERNS["binary_order"].search(code))
    result["has_big_m_pattern"] = bool(PATTERNS["big_m"].search(code))
    result["has_fixed_order_cost_pattern"] = bool(PATTERNS["fixed_order_cost"].search(code))

    if not result["has_build_model"]:
        result["static_validation_errors"].append("missing_build_model")
    if not result["has_pulp_problem"]:
        result["static_validation_errors"].append("missing_pulp_lp_problem")
    if not result["has_objective"]:
        result["static_validation_errors"].append("missing_objective_surface")
    if not result["has_constraints"]:
        result["static_validation_errors"].append("missing_constraints_surface")

    result["static_validation_score"] = float(_score(result))
    return result
```

- [ ] **Step 5: Reuse static validation in `baselines.py`**

Modify `replenishverifier/experiments/baselines.py`:

```python
import ast

from replenishverifier.pipeline.quality_signals import compute_static_validation
```

Replace `code_output_format_valid()` body with:

```python
def code_output_format_valid(generated_code):
    """Generic code-format validity signal used by OR-R1-like voting.

    This intentionally checks only solver-code surface format. It does not inspect
    replenishment-specific structures such as inventory balance or Big-M links.
    """
    validation = compute_static_validation(generated_code)
    return (
        validation["has_build_model"]
        and validation["has_pulp_problem"]
        and validation["has_objective"]
        and "contains_markdown_fence" not in validation["static_validation_errors"]
        and "syntax_error" not in validation["static_validation_errors"]
    )
```

Keep `import ast` only if another function still uses it. If no remaining code uses `ast`, remove the import.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python -m pytest tests/test_static_validation.py tests/test_strong_baselines.py::test_code_output_format_accepts_runner_compatible_build_model tests/test_strong_baselines.py::test_code_output_format_rejects_syntax_errors tests/test_strong_baselines.py::test_code_output_format_rejects_markdown_fences -q
```

Expected: PASS.

- [ ] **Step 7: Checkpoint without commit**

Run:

```bash
git status --short
```

Expected: shows the new test and module plus the `baselines.py` change. Do not commit unless the user explicitly asks.

---

### Task 2: Attach static validation to generation and evaluation rows

**Files:**
- Modify: `replenishverifier/llm/run_generation.py`
- Modify: `replenishverifier/experiments/methods.py`
- Test: `tests/test_run_generation_output_format.py`
- Test: `tests/test_static_validation.py`

**Interfaces:**
- Consumes: `compute_static_validation(generated_code, problem_type=None) -> dict`
- Produces generation-row fields: top-level static validation fields plus existing `code_output_format_valid`
- Produces evaluation-row fields: top-level static validation fields and `static_validation` dict

- [ ] **Step 1: Add a test that generation rows contain static validation fields**

Extend `tests/test_run_generation_output_format.py` with:

```python

def test_run_generation_adds_static_validation_fields(monkeypatch, tmp_path):
    from replenishverifier.llm import run_generation as module

    benchmark_path = tmp_path / "benchmark.jsonl"
    out_path = tmp_path / "candidates.jsonl"
    benchmark_path.write_text('{"id":"p0","problem_type":"single_item_multi_period","prompt":"make model"}\n', encoding="utf-8")

    class FakeTokenizer:
        pad_token = None
        eos_token = "</s>"
        eos_token_id = 1
        pad_token_id = 1

        def apply_chat_template(self, *args, **kwargs):
            return "prompt"

        def __call__(self, prompt, return_tensors=None):
            return {"input_ids": FakeTensor()}

        def decode(self, generated_ids, skip_special_tokens=True):
            return ""

    class FakeTensor:
        shape = [1, 1]

        def to(self, device):
            return self

    class FakeModel:
        def parameters(self):
            class Param:
                device = "cpu"
            return iter([Param()])

    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x, "total_cost"
    prob += x >= 1, "demand_constraint"
    return prob
'''

    monkeypatch.setattr(module, "load_model_and_tokenizer", lambda *args, **kwargs: (FakeModel(), FakeTokenizer()))
    monkeypatch.setattr(module, "generate_one", lambda *args, **kwargs: code)

    rows = module.run_generation(
        benchmark_path=benchmark_path,
        out_path=out_path,
        model_name_or_path="fake-model",
        k=1,
    )

    assert rows[0]["has_build_model"] is True
    assert rows[0]["has_pulp_problem"] is True
    assert rows[0]["static_validation_score"] == 1.0
    assert rows[0]["static_validation_errors"] == []
```

If the existing file already has fake model helpers, reuse them instead of duplicating.

- [ ] **Step 2: Run the new generation-row test to verify it fails**

Run:

```bash
python -m pytest tests/test_run_generation_output_format.py::test_run_generation_adds_static_validation_fields -q
```

Expected: FAIL because static validation fields are not yet written.

- [ ] **Step 3: Modify `run_generation.py` to attach static validation fields**

In `replenishverifier/llm/run_generation.py`, add import:

```python
from replenishverifier.pipeline.quality_signals import compute_static_validation
```

After `generated_code = extract_code(raw_generated_text)`, compute and attach:

```python
static_validation = compute_static_validation(generated_code, problem_type=sample.get("problem_type"))
row["raw_generated_text"] = raw_generated_text
row["generated_text"] = generated_code
row["generated_code"] = generated_code
row["code_output_format_valid"] = code_output_format_valid(generated_code)
row["static_validation"] = static_validation
row.update(static_validation)
```

In the exception path, also attach an empty validation result based on current code:

```python
static_validation = compute_static_validation(row.get("generated_code", ""), problem_type=sample.get("problem_type"))
row["static_validation"] = static_validation
row.update(static_validation)
```

- [ ] **Step 4: Add evaluation-row test**

Append to `tests/test_static_validation.py`:

```python

def test_evaluation_row_can_store_static_validation_fields():
    from replenishverifier.pipeline.quality_signals import compute_static_validation

    code = '''import pulp


def build_model():
    prob = pulp.LpProblem("x", pulp.LpMinimize)
    x = pulp.LpVariable("x", lowBound=0)
    prob += x, "total_cost"
    prob += x >= 1, "constraint_0"
    return prob
'''
    validation = compute_static_validation(code, problem_type="single_period_newsvendor")
    row = {"generated_code": code, "static_validation": validation, **validation}

    assert row["static_validation"]["has_build_model"] is True
    assert row["has_constraints"] is True
    assert row["static_validation_score"] == 1.0
```

This is a small contract test for the row shape later used by `methods.py`.

- [ ] **Step 5: Modify `methods.py` to attach static validation during evaluation**

In `replenishverifier/experiments/methods.py`, add import:

```python
from replenishverifier.pipeline.quality_signals import compute_static_validation
```

Inside `evaluate_candidate(...)`, after `generated_code` is known and before returning the row, compute:

```python
static_validation = compute_static_validation(generated_code, problem_type=reference.get("problem_type"))
```

Then add to the returned row dict:

```python
"static_validation": static_validation,
**static_validation,
```

If the returned row is built incrementally, use:

```python
row["static_validation"] = static_validation
row.update(static_validation)
```

Do not alter evaluation-only fields such as `objective_correct` or `relative_error`.

- [ ] **Step 6: Run focused tests**

Run:

```bash
python -m pytest tests/test_static_validation.py tests/test_run_generation_output_format.py -q
```

Expected: PASS.

- [ ] **Step 7: Checkpoint without commit**

Run:

```bash
git status --short
```

Expected: includes quality signal, generation, evaluation, and test changes. Do not commit unless the user explicitly asks.

---

### Task 3: Add bounded generation retry and attempt metadata

**Files:**
- Modify: `replenishverifier/llm/run_generation.py`
- Test: `tests/test_run_generation_retry.py`

**Interfaces:**
- Consumes: `compute_static_validation()` and `code_output_format_valid()`
- Produces CLI args: `--max_generation_attempts_per_candidate`, `--require_static_valid_code`, `--retry_on_invalid_code`
- Produces row fields: `attempt_count`, `attempts`

- [ ] **Step 1: Write failing retry success test**

Create `tests/test_run_generation_retry.py`:

```python
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
```

- [ ] **Step 2: Write failing retry exhaustion test**

Append to `tests/test_run_generation_retry.py`:

```python

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
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_run_generation_retry.py -q
```

Expected: FAIL because the new `run_generation()` keyword arguments do not exist.

- [ ] **Step 4: Add helper functions in `run_generation.py`**

Add these functions near `generate_one()`:

```python
def _attempt_metadata(attempt_index, raw_generated_text, generated_code, static_validation, accepted, error=None):
    return {
        "attempt_index": attempt_index,
        "raw_contains_think": "<think" in (raw_generated_text or "").lower(),
        "extracted_code_chars": len(generated_code or ""),
        "code_output_format_valid": code_output_format_valid(generated_code),
        "static_validation_score": float(static_validation.get("static_validation_score", 0.0)),
        "static_validation_errors": list(static_validation.get("static_validation_errors", [])),
        "accepted": bool(accepted),
        "error": error,
    }


def _should_accept_generation(raw_generated_text, generated_code, static_validation, require_static_valid_code=False):
    if "<think" in (raw_generated_text or "").lower():
        return False
    if not code_output_format_valid(generated_code):
        return False
    if require_static_valid_code and static_validation.get("static_validation_errors"):
        return False
    return True
```

- [ ] **Step 5: Extend `run_generation()` signature and config**

Change the function signature:

```python
def run_generation(
    benchmark_path,
    out_path,
    model_name_or_path,
    k=4,
    max_samples=None,
    max_new_tokens=2048,
    temperature=0.2,
    top_p=0.95,
    trust_remote_code=True,
    use_chat_template=True,
    prompt_type="hidden_verifier",
    seed=None,
    max_generation_attempts_per_candidate=1,
    require_static_valid_code=False,
    retry_on_invalid_code=False,
):
```

Add to `generation_config`:

```python
"max_generation_attempts_per_candidate": max_generation_attempts_per_candidate,
"require_static_valid_code": require_static_valid_code,
"retry_on_invalid_code": retry_on_invalid_code,
```

Normalize attempts:

```python
max_generation_attempts_per_candidate = max(1, int(max_generation_attempts_per_candidate or 1))
```

- [ ] **Step 6: Replace single generation call with bounded attempt loop**

Inside the candidate loop, replace the single `try` generation block with:

```python
attempts = []
max_attempts = max_generation_attempts_per_candidate if retry_on_invalid_code else 1
for attempt_index in range(1, max_attempts + 1):
    raw_generated_text = ""
    generated_code = ""
    try:
        raw_generated_text = generate_one(
            model,
            tokenizer,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        generated_code = extract_code(raw_generated_text)
        static_validation = compute_static_validation(generated_code, problem_type=sample.get("problem_type"))
        accepted = _should_accept_generation(
            raw_generated_text,
            generated_code,
            static_validation,
            require_static_valid_code=require_static_valid_code,
        )
        attempts.append(_attempt_metadata(attempt_index, raw_generated_text, generated_code, static_validation, accepted))
        row["raw_generated_text"] = raw_generated_text
        row["generated_text"] = generated_code
        row["generated_code"] = generated_code
        row["code_output_format_valid"] = code_output_format_valid(generated_code)
        row["static_validation"] = static_validation
        row.update(static_validation)
        if accepted:
            break
    except Exception as exc:
        LOGGER.exception("Generation failed for %s candidate %d attempt %d", sample["id"], idx, attempt_index)
        static_validation = compute_static_validation(generated_code, problem_type=sample.get("problem_type"))
        attempts.append(_attempt_metadata(attempt_index, raw_generated_text, generated_code, static_validation, False, error=repr(exc)))
        row["error"] = repr(exc)
row["attempts"] = attempts
row["attempt_count"] = len(attempts)
if "static_validation" not in row:
    static_validation = compute_static_validation(row.get("generated_code", ""), problem_type=sample.get("problem_type"))
    row["static_validation"] = static_validation
    row.update(static_validation)
```

- [ ] **Step 7: Add CLI arguments and pass them through**

In `main()` add parser arguments:

```python
parser.add_argument("--max_generation_attempts_per_candidate", type=int, default=1)
parser.add_argument("--require_static_valid_code", action="store_true", default=False)
parser.add_argument("--retry_on_invalid_code", action="store_true", default=False)
```

Pass them into `run_generation()`:

```python
max_generation_attempts_per_candidate=args.max_generation_attempts_per_candidate,
require_static_valid_code=args.require_static_valid_code,
retry_on_invalid_code=args.retry_on_invalid_code,
```

- [ ] **Step 8: Run focused retry tests**

Run:

```bash
python -m pytest tests/test_run_generation_retry.py tests/test_run_generation_output_format.py -q
```

Expected: PASS.

- [ ] **Step 9: Checkpoint without commit**

Run:

```bash
git status --short
```

Expected: includes retry test and `run_generation.py` changes. Do not commit unless the user explicitly asks.

---

### Task 4: Strengthen no-reference structure-aware selection and tie-breakers

**Files:**
- Modify: `replenishverifier/experiments/methods.py`
- Optionally modify: `replenishverifier/pipeline/scoring.py`
- Test: `tests/test_selection_gating.py`
- Existing related test: `tests/test_hard_selection_gate.py`

**Interfaces:**
- Consumes evaluated rows with `execution`, `structure_verification`, `structure_score`, `static_validation_score`, `feedback`.
- Produces unchanged selected row shape with `selection_score`, `uses_reference_objective_for_selection=False`, `selection_policy`.
- Produces helper: `_critical_structure_multiplier(row, problem_type: str | None) -> float` or public equivalent.

- [ ] **Step 1: Write failing Direct preservation test**

Create `tests/test_selection_gating.py`:

```python
from replenishverifier.experiments.methods import select_for_method


def _row(candidate_id, idx, missing=None, structure_score=1.0, objective=10.0, consensus=0.0):
    missing = missing or []
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "candidate_index": idx,
        "execution": {"executable": True, "status": "Optimal", "objective": objective, "lp_path": f"{candidate_id}.lp"},
        "structure_score": structure_score,
        "structure_verification": {
            "structure_score": structure_score,
            "missing": missing,
            "required_structures": ["inventory_balance", "capacity_constraint"],
            "certificates": [
                {"rule_name": "inventory_balance", "score": 1.0 if "inventory_balance" not in missing else 0.0},
                {"rule_name": "capacity_constraint", "score": 1.0 if "capacity_constraint" not in missing else 0.0},
            ],
        },
        "constraint_coverage": structure_score,
        "feedback": "" if not missing else "missing structure",
        "static_validation_score": 1.0,
        "objective_consensus_score": consensus,
        "score": structure_score,
        "selection_score": structure_score,
        "raw_inference_score": structure_score,
        "uses_reference_objective_for_selection": False,
    }


def test_direct_still_selects_first_candidate_even_if_weaker():
    rows = [_row("first_bad", 0, missing=["capacity_constraint"], structure_score=0.5), _row("second_good", 1)]

    selected = select_for_method("Direct", {"p0": rows}, {"p0": {"problem_type": "multi_item_capacity"}})

    assert selected[0]["candidate_id"] == "first_bad"
```

- [ ] **Step 2: Write failing critical-structure penalty test**

Append:

```python

def test_structure_grounded_selection_penalizes_missing_capacity_over_consensus():
    rows = [
        _row("consensus_missing_capacity", 0, missing=["capacity_constraint"], structure_score=0.75, objective=20.0, consensus=1.0),
        _row("complete_minority", 1, missing=[], structure_score=1.0, objective=99.0, consensus=0.25),
    ]

    selected = select_for_method("Structure-Grounded Consistency", {"p0": rows}, {"p0": {"problem_type": "multi_item_capacity"}})

    assert selected[0]["candidate_id"] == "complete_minority"
    assert selected[0]["uses_reference_objective_for_selection"] is False
```

- [ ] **Step 3: Write failing Best-of-K tie-breaker test**

Append:

```python

def test_best_of_k_uses_structure_tiebreaker_instead_of_first_viable():
    rows = [
        _row("first_viable_weaker", 0, missing=["inventory_balance"], structure_score=0.6),
        _row("second_viable_stronger", 1, missing=[], structure_score=1.0),
    ]

    selected = select_for_method("Best-of-K", {"p0": rows}, {"p0": {"problem_type": "single_item_multi_period"}})

    assert selected[0]["candidate_id"] == "second_viable_stronger"
```

- [ ] **Step 4: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_selection_gating.py -q
```

Expected: at least the critical-structure or Best-of-K tests fail under current selector behavior.

- [ ] **Step 5: Add helper functions in `methods.py`**

Add near selection helpers:

```python
STRUCTURE_AWARE_METHODS = {
    "Structure only",
    "Structure-Only",
    "Solver + Structure",
    "Structure + Consensus",
    "Solver + Structure + Consensus",
    "Structure-Grounded Consistency",
    "ReplenishVerifier-Full",
    "ReplenishVerifier-Repair",
}


def _required_missing(row):
    structure = row.get("structure_verification") or {}
    missing = set(structure.get("missing") or [])
    required = structure.get("required_structures")
    if required:
        missing &= set(required)
    return missing


def _critical_structure_multiplier(row, problem_type):
    missing = _required_missing(row)
    if "inventory_balance" in missing:
        return 0.05
    if problem_type == "multi_item_capacity" and "capacity_constraint" in missing:
        return 0.05
    if problem_type == "single_item_multi_period_shortage" and ({"shortage_variable", "shortage_cost"} & missing):
        return 0.05
    if problem_type == "fixed_order_cost_big_m" and ({"binary_order_variable", "big_m_constraint", "fixed_order_cost"} & missing):
        return 0.05
    return 1.0


def _certificate_score(row, rule_name):
    structure = row.get("structure_verification") or {}
    for cert in structure.get("certificates") or []:
        if cert.get("rule_name") == rule_name:
            return float(cert.get("score", 0.0) or 0.0)
    if rule_name in (structure.get("missing") or []):
        return 0.0
    return 1.0


def _repair_feedback_count(row):
    feedback = row.get("feedback") or ""
    if isinstance(feedback, list):
        return len(feedback)
    return len([line for line in str(feedback).splitlines() if line.strip()])


def _candidate_index(row):
    if "candidate_index" in row:
        return int(row.get("candidate_index") or 0)
    candidate_id = str(row.get("candidate_id") or "")
    if "_k" in candidate_id:
        suffix = candidate_id.rsplit("_k", 1)[-1]
        if suffix.isdigit():
            return int(suffix)
    return 0


def _selection_tiebreak_key(row, score):
    return (
        float(score or 0.0),
        float(row.get("structure_score", 0.0) or 0.0),
        _certificate_score(row, "inventory_balance"),
        float(row.get("constraint_coverage", row.get("structure_score", 0.0)) or 0.0),
        -_repair_feedback_count(row),
        float(row.get("static_validation_score", 0.0) or 0.0),
        -_candidate_index(row),
    )
```

- [ ] **Step 6: Apply penalties in `_method_gated_score()`**

Change `_method_gated_score(row, method_name, allow_feasible_selection=False)` so it can access problem type. If current signature cannot, update callers to pass `problem_type`:

```python
def _method_gated_score(row, method_name, allow_feasible_selection=False, problem_type=None):
    raw_score = _method_raw_score(row, method_name)
    gated = hard_selection_gate(row.get("execution") or {}, raw_score, allow_feasible_selection=allow_feasible_selection)
    if method_name in STRUCTURE_AWARE_METHODS:
        gated *= _critical_structure_multiplier(row, problem_type)
    return float(gated)
```

Update each call site inside `select_for_method()` to pass the benchmark problem type:

```python
problem_type = (benchmark.get(problem_id) or {}).get("problem_type")
score = _method_gated_score(row, method_name, allow_feasible_selection=allow_feasible_selection, problem_type=problem_type)
```

- [ ] **Step 7: Update Best-of-K and generic selection max logic**

For Direct, keep:

```python
best = rows[0]
```

For Best-of-K, replace first-viable selection with:

```python
scored = [
    (row, _method_gated_score(row, method_name, allow_feasible_selection=allow_feasible_selection, problem_type=problem_type))
    for row in rows
]
viable = [(row, score) for row, score in scored if score > 0.0]
if viable:
    best, best_score = max(viable, key=lambda item: _selection_tiebreak_key(item[0], item[1]))
else:
    executable = [(row, 0.0) for row in rows if (row.get("execution") or {}).get("executable")]
    best, best_score = max(executable, key=lambda item: _selection_tiebreak_key(item[0], item[1])) if executable else (rows[0], 0.0)
```

For other non-Direct methods:

```python
best, best_score = max(
    ((row, _method_gated_score(row, method_name, allow_feasible_selection=allow_feasible_selection, problem_type=problem_type)) for row in rows),
    key=lambda item: _selection_tiebreak_key(item[0], item[1]),
)
```

Ensure the selected row receives:

```python
selected_row["selection_score"] = float(best_score)
selected_row["score"] = float(best_score)
selected_row["uses_reference_objective_for_selection"] = False
```

- [ ] **Step 8: Run focused selection tests**

Run:

```bash
python -m pytest tests/test_selection_gating.py tests/test_hard_selection_gate.py tests/test_strong_baselines.py::test_reward_style_selector_uses_consensus_structure_and_no_reference_objective -q
```

Expected: PASS.

- [ ] **Step 9: Run leakage audit unit tests**

Run:

```bash
python -m pytest tests/test_strong_baselines.py::test_reward_style_methods_are_in_no_leakage_audit -q
```

Expected: PASS.

- [ ] **Step 10: Checkpoint without commit**

Run:

```bash
git status --short
```

Expected: includes selector and test changes. Do not commit unless the user explicitly asks.

---

### Task 5: Add diagnostic run script and failure examples

**Files:**
- Create: `replenishverifier/experiments/diagnose_run.py`
- Test: `tests/test_diagnose_run.py`

**Interfaces:**
- Consumes: benchmark JSONL, `candidate_evaluations.jsonl`, `main_results.jsonl`
- Produces files: `problem_diagnostics.jsonl`, `problem_type_summary.csv`, `candidate_diversity.csv`, `missing_structure_distribution.csv`, `failure_examples.jsonl`, `summary.md`
- Uses: `classify_error_type(row)` from `experiments.baselines`, `strict_objective_correct()` from `pipeline.scoring`, `read_jsonl()` and `write_jsonl()` from `utils.io`

- [ ] **Step 1: Write failing diagnostic output test**

Create `tests/test_diagnose_run.py`:

```python
from pathlib import Path

from replenishverifier.utils.io import read_jsonl, write_jsonl


def _candidate(pid, cid, idx, objective, reference, structure_score, missing):
    return {
        "problem_id": pid,
        "candidate_id": cid,
        "candidate_index": idx,
        "problem_type": "multi_item_capacity",
        "generated_code": "import pulp\n\ndef build_model():\n    return pulp.LpProblem('x', pulp.LpMinimize)\n",
        "execution": {"executable": True, "status": "Optimal", "objective": objective},
        "reference_objective": reference,
        "objective_correct": 1.0 if objective == reference else 0.0,
        "structure_score": structure_score,
        "structure_verification": {"missing": missing, "required_structures": ["inventory_balance", "capacity_constraint"]},
        "static_validation_errors": [] if structure_score == 1.0 else ["missing_constraints_surface"],
        "feedback": "missing capacity" if missing else "",
    }


def test_diagnose_run_writes_problem_and_summary_outputs(tmp_path):
    from replenishverifier.experiments.diagnose_run import diagnose_run

    benchmark_path = tmp_path / "benchmark.jsonl"
    candidate_path = tmp_path / "candidate_evaluations.jsonl"
    main_path = tmp_path / "main_results.jsonl"
    out_dir = tmp_path / "diagnostics"

    write_jsonl(benchmark_path, [{"id": "p0", "problem_type": "multi_item_capacity", "reference_objective": 10.0}])
    candidates = [
        _candidate("p0", "qwen_k0", 0, 20.0, 10.0, 0.5, ["capacity_constraint"]),
        _candidate("p0", "qwen_k1", 1, 10.0, 10.0, 1.0, []),
    ]
    write_jsonl(candidate_path, candidates)
    selected = {**candidates[0], "method_name": "ReplenishVerifier-Full", "selected": True}
    write_jsonl(main_path, [selected])

    diagnose_run(benchmark_path, candidate_path, main_path, out_dir)

    problem_rows = read_jsonl(out_dir / "problem_diagnostics.jsonl")
    failure_rows = read_jsonl(out_dir / "failure_examples.jsonl")

    assert problem_rows[0]["direct_objective_correct"] is False
    assert problem_rows[0]["any_objective_correct_candidate"] is True
    assert problem_rows[0]["any_structurally_complete_candidate"] is True
    assert problem_rows[0]["selection_missed_oracle_best"] is True
    assert problem_rows[0]["selected_missing_structures"] == ["capacity_constraint"]
    assert failure_rows[0]["reference_objective"] == 10.0
    assert (out_dir / "problem_type_summary.csv").exists()
    assert (out_dir / "candidate_diversity.csv").exists()
    assert (out_dir / "missing_structure_distribution.csv").exists()
    assert (out_dir / "summary.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_diagnose_run.py -q
```

Expected: FAIL because `diagnose_run.py` does not exist.

- [ ] **Step 3: Implement CSV and Markdown helpers**

Create `replenishverifier/experiments/diagnose_run.py` with imports and helpers:

```python
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from replenishverifier.experiments.baselines import classify_error_type
from replenishverifier.pipeline.scoring import strict_objective_correct
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _write_csv(path, rows):
    path = Path(path)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _missing(row):
    structure = row.get("structure_verification") or {}
    return sorted(structure.get("missing") or [])


def _structure_signature(row):
    return tuple(_missing(row))


def _candidate_index(row):
    if "candidate_index" in row:
        return int(row.get("candidate_index") or 0)
    cid = str(row.get("candidate_id") or "")
    if "_k" in cid and cid.rsplit("_k", 1)[-1].isdigit():
        return int(cid.rsplit("_k", 1)[-1])
    return 0
```

- [ ] **Step 4: Implement per-problem diagnostics**

Add:

```python
def _problem_diagnostic(pid, benchmark_row, candidates, selected_rows):
    reference_obj = benchmark_row.get("reference_objective")
    direct = min(candidates, key=_candidate_index) if candidates else {}
    selected = selected_rows[0] if selected_rows else {}
    selected_obj = (selected.get("execution") or {}).get("objective")
    objective_values = [
        (row.get("execution") or {}).get("objective")
        for row in candidates
        if (row.get("execution") or {}).get("objective") is not None
    ]
    rounded_objectives = {round(float(value), 6) for value in objective_values}
    oracle_candidates = [
        row for row in candidates
        if strict_objective_correct((row.get("execution") or {}).get("objective"), reference_obj)
    ]
    structurally_complete = [row for row in candidates if not _missing(row)]
    selected_correct = strict_objective_correct(selected_obj, reference_obj)
    oracle_best_exists = bool(oracle_candidates)
    selected_cid = selected.get("candidate_id")
    oracle_cids = {row.get("candidate_id") for row in oracle_candidates}
    return {
        "problem_id": pid,
        "problem_type": benchmark_row.get("problem_type"),
        "direct_candidate_id": direct.get("candidate_id"),
        "direct_objective_correct": strict_objective_correct((direct.get("execution") or {}).get("objective"), reference_obj),
        "any_objective_correct_candidate": oracle_best_exists,
        "any_structurally_complete_candidate": bool(structurally_complete),
        "selected_method": selected.get("method_name"),
        "selected_candidate_id": selected_cid,
        "selected_candidate_index": _candidate_index(selected) if selected else None,
        "selected_objective_correct": selected_correct,
        "selection_missed_oracle_best": bool(oracle_best_exists and selected_cid not in oracle_cids),
        "selected_missing_structures": _missing(selected),
        "selected_static_validation_errors": selected.get("static_validation_errors") or [],
        "unique_objective_values": len(rounded_objectives),
        "unique_structure_signatures": len({_structure_signature(row) for row in candidates}),
    }
```

- [ ] **Step 5: Implement summary tables**

Add:

```python
def _problem_type_summary(problem_rows, selected_rows):
    by_type = defaultdict(list)
    for row in selected_rows:
        by_type[row.get("problem_type")].append(row)
    summaries = []
    for problem_type, rows in sorted(by_type.items()):
        error_counts = Counter(classify_error_type(row) for row in rows)
        summaries.append({
            "problem_type": problem_type,
            "n": len(rows),
            "executable_rate": _mean(bool((row.get("execution") or {}).get("executable")) for row in rows),
            "optimal_rate": _mean((row.get("execution") or {}).get("status") == "Optimal" for row in rows),
            "objective_accuracy": _mean(float(row.get("objective_correct", 0.0) or 0.0) for row in rows),
            "structure_completeness": _mean(float(row.get("structure_score", 0.0) or 0.0) for row in rows),
            "main_error_type_distribution": dict(error_counts),
        })
    return summaries


def _diversity_rows(problem_rows):
    return [
        {
            "problem_id": row["problem_id"],
            "problem_type": row.get("problem_type"),
            "unique_objective_values": row["unique_objective_values"],
            "unique_structure_signatures": row["unique_structure_signatures"],
            "selected_candidate_index": row.get("selected_candidate_index"),
        }
        for row in problem_rows
    ]


def _missing_distribution(selected_rows):
    keys = [
        "capacity_constraint",
        "inventory_balance",
        "shortage_variable",
        "big_m_constraint",
        "fixed_order_cost",
    ]
    counts = Counter()
    for row in selected_rows:
        for key in _missing(row):
            if key in keys:
                counts[f"missing_{key}"] += 1
    return [{"missing_structure": f"missing_{key}", "count": counts.get(f"missing_{key}", 0)} for key in keys]
```

- [ ] **Step 6: Implement failure examples and top-level function**

Add:

```python
def _code_excerpt(row, max_chars=600):
    code = row.get("generated_code") or row.get("generated_text") or ""
    return code[:max_chars]


def _failure_examples(selected_rows, limit_per_error=5):
    grouped = defaultdict(list)
    for row in selected_rows:
        error_type = classify_error_type(row)
        if error_type != "no_error_detected":
            grouped[error_type].append(row)
    examples = []
    for error_type, rows in sorted(grouped.items()):
        for row in rows[:limit_per_error]:
            execution = row.get("execution") or {}
            examples.append({
                "error_type": error_type,
                "problem_id": row.get("problem_id"),
                "problem_type": row.get("problem_type"),
                "selected_method": row.get("method_name"),
                "selected_candidate_id": row.get("candidate_id"),
                "candidate_objective": execution.get("objective"),
                "reference_objective": row.get("reference_objective"),
                "missing_structures": _missing(row),
                "static_validation_errors": row.get("static_validation_errors") or [],
                "generated_code_excerpt": _code_excerpt(row),
                "repair_feedback": row.get("feedback") or row.get("generic_repair_feedback") or "",
            })
    return examples


def _write_summary(path, problem_rows, type_rows, missing_rows, failure_rows):
    lines = [
        "# Run Diagnostics",
        "",
        f"Problems analyzed: {len(problem_rows)}",
        f"Failure examples: {len(failure_rows)}",
        "",
        "## Problem Type Summary",
        "",
    ]
    for row in type_rows:
        lines.append(f"- {row['problem_type']}: n={row['n']}, objective_accuracy={row['objective_accuracy']:.4f}, structure_completeness={row['structure_completeness']:.4f}")
    lines.extend(["", "## Missing Structure Distribution", ""])
    for row in missing_rows:
        lines.append(f"- {row['missing_structure']}: {row['count']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def diagnose_run(benchmark_path, candidate_evaluations_path, main_results_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    benchmark = {row["id"]: row for row in read_jsonl(benchmark_path)}
    candidates = read_jsonl(candidate_evaluations_path)
    selected_rows = read_jsonl(main_results_path)

    candidates_by_pid = defaultdict(list)
    for row in candidates:
        candidates_by_pid[row.get("problem_id")].append(row)
    selected_by_pid = defaultdict(list)
    for row in selected_rows:
        selected_by_pid[row.get("problem_id")].append(row)

    problem_rows = []
    for pid, benchmark_row in benchmark.items():
        problem_rows.append(_problem_diagnostic(pid, benchmark_row, candidates_by_pid.get(pid, []), selected_by_pid.get(pid, [])))

    type_rows = _problem_type_summary(problem_rows, selected_rows)
    diversity = _diversity_rows(problem_rows)
    missing_rows = _missing_distribution(selected_rows)
    failure_rows = _failure_examples(selected_rows)

    write_jsonl(out_dir / "problem_diagnostics.jsonl", problem_rows)
    write_jsonl(out_dir / "failure_examples.jsonl", failure_rows)
    _write_csv(out_dir / "problem_type_summary.csv", type_rows)
    _write_csv(out_dir / "candidate_diversity.csv", diversity)
    _write_csv(out_dir / "missing_structure_distribution.csv", missing_rows)
    _write_summary(out_dir / "summary.md", problem_rows, type_rows, missing_rows, failure_rows)
    return {
        "problem_diagnostics": problem_rows,
        "problem_type_summary": type_rows,
        "candidate_diversity": diversity,
        "missing_structure_distribution": missing_rows,
        "failure_examples": failure_rows,
    }
```

- [ ] **Step 7: Add CLI entry point**

Append:

```python
def main():
    parser = argparse.ArgumentParser(description="Diagnose ReplenishVerifier experiment bottlenecks.")
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--candidate_evaluations", required=True)
    parser.add_argument("--main_results", required=True)
    parser.add_argument("--out_dir", required=True)
    args = parser.parse_args()
    diagnose_run(args.benchmark, args.candidate_evaluations, args.main_results, args.out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run focused tests**

Run:

```bash
python -m pytest tests/test_diagnose_run.py -q
```

Expected: PASS.

- [ ] **Step 9: Checkpoint without commit**

Run:

```bash
git status --short
```

Expected: includes diagnostic script and test. Do not commit unless the user explicitly asks.

---

### Task 6: Keep repair prompt generation separate and enrich optional repair context

**Files:**
- Modify: `replenishverifier/llm/prompt_builder.py`
- Modify: `replenishverifier/llm/run_repair_generation.py`
- Optionally modify: `replenishverifier/experiments/run_all_methods.py`
- Test: `tests/test_repair_generation_dry_run.py`
- Test: `tests/test_repair_prompt_fairness.py`

**Interfaces:**
- Consumes repair rows with `static_validation_errors` when present.
- Produces repair prompts that include static validation errors only for structure-aware repair.
- Keeps generic repair prompt fairness intact.
- Keeps LLM repair off by default.

- [ ] **Step 1: Inspect existing repair prompt builder before editing**

Read `replenishverifier/llm/prompt_builder.py` and identify:

```python
def build_repair_prompt(...):
    ...


def build_generic_repair_prompt(...):
    ...


def build_repair_chat_messages(...):
    ...
```

Do not add structure labels to `build_generic_repair_prompt()`.

- [ ] **Step 2: Write failing test for structure-aware static validation context**

Add to `tests/test_repair_generation_dry_run.py` or create a focused test if the existing file is too specific:

```python

def test_structure_aware_repair_prompt_includes_static_validation_errors():
    from replenishverifier.llm.prompt_builder import build_repair_prompt

    sample = {"id": "p0", "problem_type": "multi_item_capacity", "prompt": "Build an inventory model.", "params": {}}
    repair_row = {
        "problem_id": "p0",
        "candidate_id": "cand0",
        "missing": ["capacity_constraint"],
        "feedback": "Missing capacity constraint.",
        "static_validation_errors": ["missing_constraints_surface"],
    }

    prompt = build_repair_prompt(sample, repair_row, original_code="import pulp\n")

    assert "missing_constraints_surface" in prompt
    assert "Static validation errors" in prompt
```

- [ ] **Step 3: Write generic fairness regression test**

Append to `tests/test_repair_prompt_fairness.py`:

```python

def test_generic_repair_prompt_does_not_include_static_structure_labels():
    from replenishverifier.llm.prompt_builder import build_generic_repair_prompt

    sample = {"id": "p0", "problem_type": "fixed_order_cost_big_m", "prompt": "Build model", "params": {}}
    repair_row = {
        "problem_id": "p0",
        "candidate_id": "cand0",
        "generic_repair_feedback": "Add a clear objective and constraints.",
        "static_validation_errors": ["missing_big_m_constraint", "missing_inventory_balance"],
    }

    prompt = build_generic_repair_prompt(sample, repair_row, original_code="import pulp\n")

    assert "missing_big_m_constraint" not in prompt
    assert "missing_inventory_balance" not in prompt
    assert "fixed_order_cost_big_m" not in prompt
```

- [ ] **Step 4: Run repair tests to verify failure/safety**

Run:

```bash
python -m pytest tests/test_repair_generation_dry_run.py tests/test_repair_prompt_fairness.py -q
```

Expected: structure-aware static-validation test fails until prompt builder is updated; generic fairness tests should pass or be fixed if they fail.

- [ ] **Step 5: Update structure-aware repair prompt builder**

In `replenishverifier/llm/prompt_builder.py`, inside `build_repair_prompt()`, add a static-validation section only when errors exist:

```python
static_errors = repair_row.get("static_validation_errors") or []
static_section = ""
if static_errors:
    static_section = "\nStatic validation errors:\n" + "\n".join(f"- {err}" for err in static_errors) + "\n"
```

Include `static_section` in the structure-aware prompt near verifier feedback. Do not add this section to `build_generic_repair_prompt()`.

- [ ] **Step 6: Decide whether to add `run_all_methods.py` repair orchestration**

If `run_all_methods.py` can add flags without loading model dependencies unless enabled, add parser args:

```python
parser.add_argument("--enable_llm_repair", action="store_true", default=False)
parser.add_argument("--repair_rounds", type=int, default=1)
parser.add_argument("--repair_model", default=None)
parser.add_argument("--repair_only_failed_or_low_structure", action="store_true", default=False)
```

Then guard any repair generation call with:

```python
if enable_llm_repair:
    if not repair_model:
        raise ValueError("--repair_model is required when --enable_llm_repair is set")
```

If this creates broad orchestration changes, do not implement it in this task. Instead, document the existing explicit repair command in `progress.md` and keep `run_repair_generation.py` as the true repair path. This keeps implementation small and avoids accidentally running LLM repair by default.

- [ ] **Step 7: Run focused repair tests**

Run:

```bash
python -m pytest tests/test_repair_generation_dry_run.py tests/test_repair_prompt_fairness.py -q
```

Expected: PASS.

- [ ] **Step 8: Checkpoint without commit**

Run:

```bash
git status --short
```

Expected: includes repair prompt/test changes if implemented. Do not commit unless the user explicitly asks.

---

### Task 7: Update progress docs and run verification

**Files:**
- Modify: `progress.md`
- Optional read-only verification: `task_plan.md`, `findings.md`

**Interfaces:**
- Consumes test results from Tasks 1-6.
- Produces session progress entry with changed files, tests, and constraints preserved.

- [ ] **Step 1: Run focused test group**

Run:

```bash
python -m pytest tests/test_static_validation.py tests/test_run_generation_retry.py tests/test_diagnose_run.py tests/test_selection_gating.py tests/test_repair_generation_dry_run.py tests/test_repair_prompt_fairness.py -q
```

Expected: PASS.

- [ ] **Step 2: Run existing related tests**

Run:

```bash
python -m pytest tests/test_hard_selection_gate.py tests/test_strong_baselines.py tests/test_run_generation_output_format.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS. Warning count may include existing PuLP/Torch warnings.

- [ ] **Step 4: Append progress entry**

Append this section to `progress.md`, filling in the exact test result lines observed from Steps 1-3:

```markdown
## 2026-06-18 — Experiment diagnosis, quality signals, and selection hardening

### User request

The user asked to improve Qwen3-8B ReplenishVerifier experiment code to raise objective accuracy and structure completeness while preserving no-reference selection and avoiding leakage.

### Actions completed

1. Added shared static candidate quality signals in `replenishverifier/pipeline/quality_signals.py`.
2. Attached static validation fields to generation and evaluation rows.
3. Added bounded Qwen generation retry options and per-attempt metadata.
4. Strengthened structure-aware selection so critical missing structures are penalized and consensus cannot dominate them.
5. Added deterministic no-reference tie-breakers while preserving Direct as candidate index 0.
6. Added `replenishverifier.experiments.diagnose_run` for JSONL/CSV/Markdown bottleneck diagnostics and failure examples.
7. Kept real LLM repair off by default and preserved generic repair fairness.

### Verification

- Focused new tests: `[PASTE RESULT]`
- Existing related tests: `[PASTE RESULT]`
- Full suite: `[PASTE RESULT]`

### Notes

No existing experiment results were deleted or overwritten. No large real LLM generation was run. No model weights were uploaded or bundled. Formal selection still does not use `reference_objective`, reference answers, reference LPs, or reference solver status. Diagnostic oracle fields are post-selection analysis only.
```

Replace each `[PASTE RESULT]` with the actual command result, such as `21 passed in 1.20s`.

- [ ] **Step 5: Run leakage audit on real runs only when requested**

Do not run a large experiment. If the user asks to validate an existing real run after implementation, run:

```bash
python -m replenishverifier.experiments.audit_leakage --exp_dir runs/qwen3_8b_k4_50_formatfix_v2 --write_report
```

Expected: audit passes before paper use. This is not part of normal unit verification because it reads existing run artifacts.

- [ ] **Step 6: Final status check without commit**

Run:

```bash
git status --short
```

Expected: shows only intended source, tests, docs, and plan/spec changes. Do not commit unless the user explicitly asks.

---

## Self-Review Checklist

- Spec coverage:
  - Diagnostic script is covered by Task 5.
  - Static validation quality signals are covered by Tasks 1 and 2.
  - Generation retry and attempt metadata are covered by Task 3.
  - No-reference selection penalties and tie-breakers are covered by Task 4.
  - Optional repair remains off by default and repair prompt context is covered by Task 6.
  - Tests and progress documentation are covered by Task 7.

- Leakage boundary:
  - No task uses `reference_objective` for formal selection.
  - Diagnostic oracle fields are confined to `diagnose_run.py` outputs.
  - Generic baselines remain generic.
  - Direct remains candidate-index-0.

- Placeholder scan:
  - This plan does not contain implementation placeholders in code steps.
  - The only bracketed values are explicit instructions to paste observed test results into `progress.md` after tests run.

- Type consistency:
  - `compute_static_validation(generated_code: str, problem_type: str | None = None) -> dict` is the shared interface across tasks.
  - Row fields use consistent names: `static_validation`, `static_validation_errors`, `static_validation_score`, `attempt_count`, `attempts`.
  - Selection helper names are internal and consistently prefixed with `_`.
