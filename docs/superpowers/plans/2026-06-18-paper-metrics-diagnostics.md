# Paper Metrics Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade ReplenishVerifier evaluation into a paper-grade, method-specific metric suite with diagnostics that prove selection and aggregation are correct without rerunning LLM generation.

**Architecture:** Add small focused modules for objective-term coverage, paper metric aggregation, and selection/metric diagnostics. Keep formal selection no-reference; post-hoc/oracle metrics may read reference-derived evaluation fields only in explicitly labeled analysis paths. Preserve existing `run_all_methods` outputs while adding richer metadata and CLIs.

**Tech Stack:** Python 3.10+, stdlib `argparse`, `csv`, `json`, `statistics`, `random`, existing `numpy`, existing project JSONL/table helpers, pytest.

## Global Constraints

- Communicate with the user in Chinese.
- Modify files directly under `/home/dongaorui/projects/lunwen`; do not create git worktrees, temporary project copies, side branches, or agent workspaces.
- Before implementation, run `git status`; after implementation, run `git status` and `git diff --name-only`.
- Do not run large model generation and do not regenerate 50-problem candidates.
- Re-evaluate only from existing candidates if needed.
- Formal candidate selection must not use `reference_objective`, `objective_correct`, reference LP, or oracle metrics.
- `reference_objective` is allowed only for post-hoc evaluation metrics such as objective accuracy, relative error, oracle upper bound, and pass@k analysis.
- Missing fields must degrade gracefully; paper tables must output `N/A` rather than invented values.
- Rates, runtimes, gaps, and confidence intervals should be rounded to 4 decimals in CSV/Markdown outputs.
- `--model_label` must be optional; if absent, old generation behavior must remain compatible.
- All code changes must be covered by focused tests before full pytest.

---

## File Structure

- Modify `replenishverifier/llm/run_generation.py`: add optional `model_label`, generation timing, `model` field, and compatible candidate IDs.
- Create `replenishverifier/experiments/objective_terms.py`: evaluation-only heuristic objective-term coverage.
- Modify `replenishverifier/experiments/methods.py`: attach objective-term coverage to candidate evaluation rows and ensure selected rows carry diagnostics.
- Modify `replenishverifier/experiments/evaluation.py`: expose helper-safe metric recomputation where useful without breaking existing summaries.
- Create `replenishverifier/experiments/paper_metrics.py`: pure functions for method-specific selected-row aggregation, pass@k/oracle metrics, bootstrap CI, selection diagnostics, and table formatting.
- Create `replenishverifier/experiments/diagnose_selection_metrics.py`: CLI for independent recompute and reported-vs-recomputed comparison.
- Create `replenishverifier/experiments/build_paper_metrics.py`: CLI for paper-grade CSV/Markdown tables.
- Modify `replenishverifier/experiments/audit_leakage.py`: distinguish formal selection rows from post-hoc evaluation/oracle rows and fail on reference-use markers in formal selection.
- Modify or add tests:
  - `tests/test_run_generation_model_label.py`
  - `tests/test_objective_term_coverage.py`
  - `tests/test_paper_metrics.py`
  - `tests/test_diagnose_selection_metrics.py`
  - `tests/test_leakage_audit.py` or existing leakage tests
  - existing selection tests as needed.
- Modify `progress.md` after implementation and verification to record what changed.

---

### Task 1: Add compatible generation metadata and `--model_label`

**Files:**
- Modify: `replenishverifier/llm/run_generation.py`
- Test: `tests/test_run_generation_model_label.py`

**Interfaces:**
- Consumes: existing `run_generation(...)` function and existing generation row schema.
- Produces: `run_generation(..., model_label: str | None = None)`; candidate rows containing `model`, optional `model_label`, `generation_time_sec`, `attempt_count`, `code_output_format_valid`, `static_validation`, and backwards-compatible `model_name_or_path`.

- [ ] **Step 1: Write failing tests for model_label and compatibility**

Create `tests/test_run_generation_model_label.py`:

```python
from pathlib import Path

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
    monkeypatch.setattr(rg, "generate_one", lambda *args, **kwargs: "import pulp\n\ndef build_model():\n    return pulp.LpProblem('x', pulp.LpMinimize)\n")


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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_run_generation_model_label.py -q
```

Expected: FAIL because `run_generation()` does not accept `model_label` and rows do not include `generation_time_sec` / `model`.

- [ ] **Step 3: Implement `model_label` and timing**

In `replenishverifier/llm/run_generation.py`:

1. Add `model_label=None` to `run_generation(...)` signature.
2. Add `"model_label": model_label` and `"model": str(model_name_or_path)` to `generation_config` and row.
3. Replace candidate ID construction with:

```python
candidate_prefix = str(model_label) if model_label else Path(str(model_name_or_path)).name
candidate_id = f"{candidate_prefix}_k{idx}"
```

4. Around each model generation attempt, record elapsed generation time:

```python
attempt_start = time.perf_counter()
raw_generated_text = generate_one(...)
generation_time_sec = time.perf_counter() - attempt_start
```

5. Initialize row with:

```python
"model": str(model_name_or_path),
"model_label": model_label,
"generation_time_sec": 0.0,
```

6. After every successful attempt, set:

```python
row["generation_time_sec"] = float(generation_time_sec)
```

7. In exception path, set elapsed time if available.
8. Add CLI argument:

```python
parser.add_argument("--model_label", default=None, help="Optional stable label used in candidate_id and candidate metadata.")
```

9. Pass `model_label=args.model_label` to `run_generation()`.
10. Ensure `import time` exists at top of file.

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_run_generation_model_label.py tests/test_run_generation_output_format.py -q
```

Expected: PASS.

---

### Task 2: Add evaluation-only objective-term coverage

**Files:**
- Create: `replenishverifier/experiments/objective_terms.py`
- Modify: `replenishverifier/experiments/methods.py`
- Test: `tests/test_objective_term_coverage.py`

**Interfaces:**
- Produces: `expected_objective_terms(problem_type: str | None) -> list[str]`
- Produces: `evaluate_objective_terms(row: dict, parsed=None, generated_code: str | None = None) -> dict`
- Candidate evaluation rows gain `objective_term_verification`, `objective_term_coverage`, `expected_objective_terms`, `detected_objective_terms`, `missing_objective_terms`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_objective_term_coverage.py`:

```python
from replenishverifier.experiments.objective_terms import expected_objective_terms, evaluate_objective_terms


def test_expected_terms_by_problem_type():
    assert expected_objective_terms("single_period_newsvendor") == ["ordering_cost", "holding_cost", "shortage_cost"]
    assert expected_objective_terms("single_item_multi_period") == ["ordering_cost", "holding_cost"]
    assert expected_objective_terms("single_item_multi_period_shortage") == ["ordering_cost", "holding_cost", "shortage_cost"]
    assert expected_objective_terms("multi_item_capacity") == ["ordering_cost", "holding_cost"]
    assert expected_objective_terms("fixed_order_cost_big_m") == ["ordering_cost", "holding_cost", "fixed_order_cost"]


def test_detects_terms_from_generated_code_names():
    row = {"problem_type": "fixed_order_cost_big_m"}
    code = "model += unit_order_cost * Q[t] + holding_cost * I[t] + fixed_order_cost * Y[t]"

    result = evaluate_objective_terms(row, generated_code=code)

    assert result["expected_objective_terms"] == ["ordering_cost", "holding_cost", "fixed_order_cost"]
    assert result["detected_objective_terms"] == ["ordering_cost", "holding_cost", "fixed_order_cost"]
    assert result["missing_objective_terms"] == []
    assert result["objective_term_coverage"] == 1.0
    assert result["uses_reference_objective_for_objective_term_coverage"] is False


def test_missing_shortage_term_lowers_coverage():
    row = {"problem_type": "single_item_multi_period_shortage"}
    code = "model += order_cost * Q[t] + holding_cost * I[t]"

    result = evaluate_objective_terms(row, generated_code=code)

    assert result["detected_objective_terms"] == ["ordering_cost", "holding_cost"]
    assert result["missing_objective_terms"] == ["shortage_cost"]
    assert result["objective_term_coverage"] == 2 / 3


def test_unknown_problem_type_returns_na_shape():
    result = evaluate_objective_terms({"problem_type": "unknown"}, generated_code="model += x")

    assert result["expected_objective_terms"] == []
    assert result["detected_objective_terms"] == []
    assert result["missing_objective_terms"] == []
    assert result["objective_term_coverage"] is None
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_objective_term_coverage.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement objective term module**

Create `replenishverifier/experiments/objective_terms.py`:

```python
import re

EXPECTED_OBJECTIVE_TERMS_BY_TYPE = {
    "single_period_newsvendor": ["ordering_cost", "holding_cost", "shortage_cost"],
    "single_item_multi_period": ["ordering_cost", "holding_cost"],
    "single_item_multi_period_shortage": ["ordering_cost", "holding_cost", "shortage_cost"],
    "multi_item_capacity": ["ordering_cost", "holding_cost"],
    "fixed_order_cost_big_m": ["ordering_cost", "holding_cost", "fixed_order_cost"],
}

TERM_PATTERNS = {
    "ordering_cost": [r"unit[_ ]?order", r"order[_ ]?cost", r"ordering[_ ]?cost", r"purchase[_ ]?cost", r"\bQ\b", r"Q_"],
    "holding_cost": [r"holding[_ ]?cost", r"hold[_ ]?cost", r"inventory[_ ]?cost", r"\bI\b", r"I_"],
    "shortage_cost": [r"shortage[_ ]?cost", r"backorder[_ ]?cost", r"penalty[_ ]?cost", r"\bS\b", r"S_", r"short"],
    "fixed_order_cost": [r"fixed[_ ]?order", r"setup[_ ]?cost", r"fixed[_ ]?cost", r"\bY\b", r"Y_", r"binary"],
}


def expected_objective_terms(problem_type):
    return list(EXPECTED_OBJECTIVE_TERMS_BY_TYPE.get(problem_type or "", []))


def _haystack(row, parsed=None, generated_code=None):
    parts = [generated_code or row.get("generated_code", "") or row.get("generated_text", "") or ""]
    if parsed is not None:
        objective = getattr(parsed, "objective", None)
        variable_names = getattr(parsed, "variable_names", None)
        parts.append(str(objective or ""))
        if variable_names:
            parts.append(" ".join(str(name) for name in variable_names))
    lp_stats = row.get("lp_stats") or {}
    parts.append(str(lp_stats.get("objective", "")))
    return "\n".join(parts).lower()


def _detect(term, text):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in TERM_PATTERNS.get(term, []))


def evaluate_objective_terms(row, parsed=None, generated_code=None):
    expected = expected_objective_terms(row.get("problem_type"))
    if not expected:
        return {
            "expected_objective_terms": [],
            "detected_objective_terms": [],
            "missing_objective_terms": [],
            "objective_term_coverage": None,
            "uses_reference_objective_for_objective_term_coverage": False,
        }
    text = _haystack(row, parsed=parsed, generated_code=generated_code)
    detected = [term for term in expected if _detect(term, text)]
    missing = [term for term in expected if term not in detected]
    return {
        "expected_objective_terms": expected,
        "detected_objective_terms": detected,
        "missing_objective_terms": missing,
        "objective_term_coverage": float(len(detected) / len(expected)),
        "uses_reference_objective_for_objective_term_coverage": False,
    }
```

- [ ] **Step 4: Attach objective-term fields during candidate evaluation**

In `replenishverifier/experiments/methods.py`:

1. Add import:

```python
from replenishverifier.experiments.objective_terms import evaluate_objective_terms
```

2. After `runtime_fields` and before `base.update(compute_score(...))`, compute:

```python
objective_term_result = evaluate_objective_terms(
    {"problem_type": reference.get("problem_type"), "generated_code": generated_code},
    parsed=parsed,
    generated_code=generated_code,
)
```

3. Add to `base`:

```python
"objective_term_verification": objective_term_result,
"objective_term_coverage": objective_term_result.get("objective_term_coverage"),
"expected_objective_terms": objective_term_result.get("expected_objective_terms", []),
"detected_objective_terms": objective_term_result.get("detected_objective_terms", []),
"missing_objective_terms": objective_term_result.get("missing_objective_terms", []),
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_objective_term_coverage.py tests/test_strong_baselines.py -q
```

Expected: PASS.

---

### Task 3: Add paper metric aggregation primitives

**Files:**
- Create: `replenishverifier/experiments/paper_metrics.py`
- Test: `tests/test_paper_metrics.py`

**Interfaces:**
- Produces: `compute_selected_method_metrics(rows: list[dict]) -> list[dict]`
- Produces: `compute_error_type_summary(rows: list[dict]) -> list[dict]`
- Produces: `compute_selection_diagnostics(main_rows: list[dict], candidate_rows: list[dict]) -> dict[str, list[dict]]`
- Produces: `compute_pass_at_k(candidate_rows: list[dict], k_values: list[int]) -> list[dict]`
- Produces: `add_bootstrap_ci(metric_rows: list[dict], selected_rows: list[dict], metrics: list[str], samples: int, seed: int) -> list[dict]`
- Produces: `format_metric_value(value) -> str`

- [ ] **Step 1: Write failing tests for selected-row aggregation**

Create `tests/test_paper_metrics.py` with this first test block:

```python
from replenishverifier.experiments.paper_metrics import (
    compute_selected_method_metrics,
    compute_error_type_summary,
    compute_pass_at_k,
    compute_selection_diagnostics,
    format_metric_value,
)


def _row(method, pid, cid, selected=True, executable=True, status="Optimal", objective_correct=1.0, structure_score=1.0):
    return {
        "method_name": method,
        "problem_id": pid,
        "candidate_id": cid,
        "selected": selected,
        "execution": {"executable": executable, "status": status, "objective": 10.0},
        "objective_correct": objective_correct,
        "relative_error": 0.0 if objective_correct else 0.5,
        "structure_score": structure_score,
        "structure_verification": {
            "expected": {"inventory_balance": True, "capacity_constraint": False},
            "detected": {"inventory_balance": structure_score >= 1.0, "capacity_constraint": False},
            "required_structures": ["inventory_balance"],
            "missing": [] if structure_score >= 1.0 else ["inventory_balance"],
            "structure_score": structure_score,
        },
        "objective_term_coverage": 1.0,
        "runtime_sec": 0.25,
        "feedback": "",
        "code_output_format_valid": True,
        "selection_score": 0.8,
        "objective_consensus_score": 0.5,
    }


def test_compute_selected_method_metrics_uses_only_selected_rows():
    rows = [
        _row("Direct", "p0", "k0", selected=True, objective_correct=1.0, structure_score=1.0),
        _row("Direct", "p1", "k0", selected=True, objective_correct=0.0, structure_score=0.0),
        _row("Direct", "p2", "k1", selected=False, objective_correct=1.0, structure_score=1.0),
    ]

    metrics = compute_selected_method_metrics(rows)

    assert metrics == [{
        "method": "Direct",
        "n": 2,
        "code_validity_rate": 1.0,
        "executable_rate": 1.0,
        "optimal_rate": 1.0,
        "solver_status_optimal_rate": 1.0,
        "solver_status_infeasible_rate": 0.0,
        "solver_status_timeout_rate": 0.0,
        "solver_status_error_rate": 0.0,
        "objective_accuracy": 0.5,
        "mean_relative_error": 0.25,
        "median_relative_error": 0.25,
        "mean_objective_gap": 0.25,
        "median_objective_gap": 0.25,
        "structure_completeness": 0.5,
        "inventory_balance_accuracy": 0.5,
        "constraint_coverage": 0.5,
        "objective_term_coverage": 1.0,
        "average_runtime_sec": 0.25,
        "median_runtime_sec": 0.25,
        "average_repair_feedback_count": 0.5,
    }]


def test_format_metric_value_outputs_na_and_four_decimals():
    assert format_metric_value(None) == "N/A"
    assert format_metric_value(0.123456) == "0.1235"
    assert format_metric_value("Direct") == "Direct"
```

- [ ] **Step 2: Write failing tests for error/pass@k/selection diagnostics**

Append to `tests/test_paper_metrics.py`:

```python

def test_error_type_summary_counts_selected_rows_by_method():
    rows = [
        _row("Direct", "p0", "k0", executable=False, status="Error"),
        _row("Direct", "p1", "k0"),
    ]

    summary = compute_error_type_summary(rows)

    assert {item["error_type"]: item["count"] for item in summary if item["method"] == "Direct"} == {
        "execution_error": 1,
        "no_error_detected": 1,
    }
    assert all("rate" in item for item in summary)


def test_compute_pass_at_k_reports_oracle_upper_bounds():
    candidate_rows = [
        _row("candidate", "p0", "m_k0", objective_correct=0.0, structure_score=0.0),
        _row("candidate", "p0", "m_k1", objective_correct=1.0, structure_score=1.0),
        _row("candidate", "p1", "m_k0", objective_correct=0.0, structure_score=1.0),
        _row("candidate", "p1", "m_k1", objective_correct=0.0, structure_score=1.0),
    ]

    rows = compute_pass_at_k(candidate_rows, [1, 2])

    by_k = {row["k"]: row for row in rows}
    assert by_k[1]["pass_at_k_objective"] == 0.0
    assert by_k[2]["pass_at_k_objective"] == 0.5
    assert by_k[2]["oracle_structure_completeness_at_k"] == 1.0
    assert by_k[2]["uses_reference_for_oracle_metrics"] is True
    assert by_k[2]["formal_selection_metric"] is False


def test_compute_selection_diagnostics_outputs_same_rate_and_rank_distribution():
    main_rows = [
        _row("Direct", "p0", "model_k0"),
        _row("Best-of-K", "p0", "model_k1"),
        _row("Direct", "p1", "model_k0"),
        _row("Best-of-K", "p1", "model_k0"),
    ]
    candidate_rows = [
        _row("candidate", "p0", "model_k0"),
        _row("candidate", "p0", "model_k1"),
        _row("candidate", "p1", "model_k0"),
        _row("candidate", "p1", "model_k1"),
    ]

    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows)

    same = diagnostics["same_selection_rate"]
    direct_vs_best = [row for row in same if row["method_a"] == "Direct" and row["method_b"] == "Best-of-K"][0]
    assert direct_vs_best["same_selection_rate"] == 0.5
    distribution = diagnostics["candidate_rank_distribution"]
    assert {row["method"]: row["k0"] for row in distribution} == {"Best-of-K": 1, "Direct": 2}
    debug = diagnostics["selection_score_debug"]
    assert {"method", "problem_id", "candidate_id", "objective_correct_posthoc", "selected"} <= set(debug[0])
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_paper_metrics.py -q
```

Expected: FAIL because `paper_metrics.py` does not exist.

- [ ] **Step 4: Implement `paper_metrics.py`**

Create `replenishverifier/experiments/paper_metrics.py` with these functions:

```python
import csv
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from replenishverifier.experiments.baselines import classify_error_type

BASE_METRICS = [
    "executable_rate",
    "optimal_rate",
    "objective_accuracy",
    "structure_completeness",
    "inventory_balance_accuracy",
    "constraint_coverage",
    "average_runtime_sec",
    "average_repair_feedback_count",
]


def safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values):
    vals = [safe_float(v) for v in values]
    vals = [v for v in vals if v is not None]
    return None if not vals else float(sum(vals) / len(vals))


def median(values):
    vals = [safe_float(v) for v in values]
    vals = [v for v in vals if v is not None]
    return None if not vals else float(statistics.median(vals))


def rate(values):
    vals = [v for v in values if v is not None]
    return None if not vals else float(sum(1.0 if v else 0.0 for v in vals) / len(vals))


def feedback_count(row):
    structure = row.get("structure_verification") or {}
    if "missing" in structure:
        return len(structure.get("missing") or [])
    text = row.get("feedback") or ""
    return len([line for line in str(text).splitlines() if line.strip()])


def constraint_coverage(row):
    structure = row.get("structure_verification") or {}
    required = structure.get("required_structures")
    if required is None:
        expected = structure.get("expected") or {}
        required = [key for key, value in expected.items() if value]
    missing = set(structure.get("missing") or [])
    if not required:
        return safe_float(row.get("structure_score", structure.get("structure_score")))
    return float(len([key for key in required if key not in missing]) / len(required))


def inventory_balance_hit(row):
    structure = row.get("structure_verification") or {}
    expected = structure.get("expected") or {}
    if not expected.get("inventory_balance"):
        return None
    detected = structure.get("detected") or {}
    return bool(detected.get("inventory_balance"))


def selected_rows(rows):
    return [row for row in rows if row.get("selected", False)]


def group_selected_by_method(rows):
    grouped = defaultdict(list)
    for row in selected_rows(rows):
        grouped[row.get("method_name") or row.get("method") or "unknown"].append(row)
    return grouped


def _status(row):
    return str((row.get("execution") or {}).get("status") or "").strip().lower()


def _is_structure_complete(row):
    return safe_float(row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score"))) == 1.0


def compute_selected_method_metrics(rows):
    result = []
    for method, items in sorted(group_selected_by_method(rows).items()):
        statuses = [_status(row) for row in items]
        rel_errors = [row.get("relative_error") for row in items]
        result.append({
            "method": method,
            "n": len(items),
            "code_validity_rate": rate([row.get("code_output_format_valid") for row in items]),
            "executable_rate": rate([(row.get("execution") or {}).get("executable") for row in items]),
            "optimal_rate": rate([_status(row) == "optimal" for row in items]),
            "solver_status_optimal_rate": rate([status == "optimal" for status in statuses]),
            "solver_status_infeasible_rate": rate([status == "infeasible" for status in statuses]),
            "solver_status_timeout_rate": rate([status == "timeout" for status in statuses]),
            "solver_status_error_rate": rate([status in {"error", "missing", "notrun", "not_run", ""} for status in statuses]),
            "objective_accuracy": mean([row.get("objective_correct", row.get("objective_accuracy")) for row in items]),
            "mean_relative_error": mean(rel_errors),
            "median_relative_error": median(rel_errors),
            "mean_objective_gap": mean(rel_errors),
            "median_objective_gap": median(rel_errors),
            "structure_completeness": mean([row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score")) for row in items]),
            "inventory_balance_accuracy": rate([inventory_balance_hit(row) for row in items]),
            "constraint_coverage": mean([constraint_coverage(row) for row in items]),
            "objective_term_coverage": mean([row.get("objective_term_coverage") for row in items]),
            "average_runtime_sec": mean([row.get("runtime_sec", row.get("total_candidate_evaluation_time")) for row in items]),
            "median_runtime_sec": median([row.get("runtime_sec", row.get("total_candidate_evaluation_time")) for row in items]),
            "average_repair_feedback_count": mean([feedback_count(row) for row in items]),
        })
    return result


def compute_error_type_summary(rows):
    result = []
    for method, items in sorted(group_selected_by_method(rows).items()):
        counts = Counter(classify_error_type(row) for row in items)
        total = len(items)
        for error_type, count in sorted(counts.items()):
            result.append({"method": method, "error_type": error_type, "count": count, "rate": float(count / total) if total else None})
    return result


def candidate_index(candidate_id):
    text = str(candidate_id or "")
    marker = text.rsplit("_k", 1)
    if len(marker) == 2 and marker[1].isdigit():
        return int(marker[1])
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def compute_pass_at_k(candidate_rows, k_values):
    by_problem = defaultdict(list)
    for row in candidate_rows:
        by_problem[row.get("problem_id")].append(row)
    result = []
    for k in k_values:
        objective_hits = []
        structure_hits = []
        both_hits = []
        for rows in by_problem.values():
            top = sorted(rows, key=lambda row: candidate_index(row.get("candidate_id")))[:k]
            has_obj = any(bool(safe_float(row.get("objective_correct", 0.0))) for row in top)
            has_struct = any(_is_structure_complete(row) for row in top)
            objective_hits.append(has_obj)
            structure_hits.append(has_struct)
            both_hits.append(has_obj and has_struct)
        result.append({
            "k": k,
            "pass_at_k_objective": rate(objective_hits),
            "pass_at_k_structure": rate(structure_hits),
            "pass_at_k_both": rate(both_hits),
            "oracle_objective_accuracy_at_k": rate(objective_hits),
            "oracle_structure_completeness_at_k": rate(structure_hits),
            "oracle_both_success_at_k": rate(both_hits),
            "uses_reference_for_oracle_metrics": True,
            "formal_selection_metric": False,
        })
    return result


def compute_selection_diagnostics(main_rows, candidate_rows):
    selected_by_method = defaultdict(dict)
    for row in selected_rows(main_rows):
        selected_by_method[row.get("method_name")][row.get("problem_id")] = row.get("candidate_id")
    methods = sorted(selected_by_method)
    same_rows = []
    for i, method_a in enumerate(methods):
        for method_b in methods[i + 1:]:
            common = sorted(set(selected_by_method[method_a]) & set(selected_by_method[method_b]))
            same = sum(1 for pid in common if selected_by_method[method_a][pid] == selected_by_method[method_b][pid])
            same_rows.append({
                "method_a": method_a,
                "method_b": method_b,
                "n_common": len(common),
                "same_count": same,
                "same_selection_rate": float(same / len(common)) if common else None,
            })
    distribution = []
    for method in methods:
        counts = Counter(candidate_index(cid) for cid in selected_by_method[method].values())
        row = {"method": method, "n": sum(counts.values())}
        for idx in range(4):
            row[f"k{idx}"] = counts.get(idx, 0)
        row["k_ge_4"] = sum(count for idx, count in counts.items() if idx >= 4)
        distribution.append(row)
    selected_keys = {(row.get("method_name"), row.get("problem_id"), row.get("candidate_id")) for row in selected_rows(main_rows)}
    debug = []
    by_problem = defaultdict(list)
    for row in candidate_rows:
        by_problem[row.get("problem_id")].append(row)
    for method in methods:
        for pid, rows in sorted(by_problem.items()):
            for row in sorted(rows, key=lambda item: candidate_index(item.get("candidate_id"))):
                execution = row.get("execution") or {}
                debug.append({
                    "method": method,
                    "problem_id": pid,
                    "candidate_id": row.get("candidate_id"),
                    "executable": bool(execution.get("executable")),
                    "solver_status": execution.get("status"),
                    "objective_correct_posthoc": row.get("objective_correct"),
                    "structure_score": row.get("structure_score", (row.get("structure_verification") or {}).get("structure_score")),
                    "consensus_score": row.get("objective_consensus_score"),
                    "selection_score": row.get("selection_score", row.get("score")),
                    "selected": (method, pid, row.get("candidate_id")) in selected_keys,
                })
    return {"same_selection_rate": same_rows, "candidate_rank_distribution": distribution, "selection_score_debug": debug}


def bootstrap_ci_for_metric(items, metric_fn, samples=1000, seed=42):
    if not items:
        return (None, None)
    rng = random.Random(seed)
    values = []
    for _ in range(samples):
        sampled = [items[rng.randrange(len(items))] for _ in items]
        value = metric_fn(sampled)
        if value is not None:
            values.append(value)
    if not values:
        return (None, None)
    values.sort()
    low_idx = int(0.025 * (len(values) - 1))
    high_idx = int(0.975 * (len(values) - 1))
    return (float(values[low_idx]), float(values[high_idx]))


def add_bootstrap_ci(metric_rows, selected_input_rows, metrics=None, samples=1000, seed=42):
    metrics = metrics or ["objective_accuracy", "structure_completeness", "constraint_coverage"]
    grouped = group_selected_by_method(selected_input_rows)
    out = []
    for metric_row in metric_rows:
        row = dict(metric_row)
        items = grouped.get(row["method"], [])
        for metric in metrics:
            if metric == "objective_accuracy":
                fn = lambda sample: mean([item.get("objective_correct", item.get("objective_accuracy")) for item in sample])
            elif metric == "structure_completeness":
                fn = lambda sample: mean([item.get("structure_score", (item.get("structure_verification") or {}).get("structure_score")) for item in sample])
            elif metric == "constraint_coverage":
                fn = lambda sample: mean([constraint_coverage(item) for item in sample])
            else:
                continue
            low, high = bootstrap_ci_for_metric(items, fn, samples=samples, seed=seed)
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
        out.append(row)
    return out


def format_metric_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path, rows, title):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text(f"# {title}\n\nNo rows.\n", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(format_metric_value(row.get(header)) for header in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_paper_metrics.py -q
```

Expected: PASS.

---

### Task 4: Add `diagnose_selection_metrics` CLI

**Files:**
- Create: `replenishverifier/experiments/diagnose_selection_metrics.py`
- Test: `tests/test_diagnose_selection_metrics.py`

**Interfaces:**
- Produces CLI: `python -m replenishverifier.experiments.diagnose_selection_metrics --exp_dir ... --candidates ... --benchmark ... --out_dir ...`
- Produces files: `metric_comparison.csv/md/jsonl`, `error_type_comparison.csv/md/jsonl`, `selection_score_debug.csv`, `same_selection_rate.csv`, `candidate_rank_distribution.csv`, `diagnostic_summary.md`.
- Produces function: `diagnose_selection_metrics(exp_dir, candidates_path=None, benchmark_path=None, out_dir=None) -> dict`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_diagnose_selection_metrics.py`:

```python
from pathlib import Path

from replenishverifier.experiments.diagnose_selection_metrics import diagnose_selection_metrics
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _selected(method, pid, cid, objective_correct=1.0):
    return {
        "method_name": method,
        "problem_id": pid,
        "candidate_id": cid,
        "selected": True,
        "execution": {"executable": True, "status": "Optimal", "objective": 1.0},
        "objective_correct": objective_correct,
        "relative_error": 0.0 if objective_correct else 0.5,
        "structure_score": 1.0,
        "structure_verification": {
            "expected": {"inventory_balance": True},
            "detected": {"inventory_balance": True},
            "required_structures": ["inventory_balance"],
            "missing": [],
            "structure_score": 1.0,
        },
        "runtime_sec": 0.1,
        "code_output_format_valid": True,
        "objective_term_coverage": 1.0,
    }


def test_diagnose_selection_metrics_writes_comparisons_and_debug(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    main_rows = [_selected("Direct", "p0", "m_k0"), _selected("Best-of-K", "p0", "m_k1", objective_correct=0.0)]
    candidate_rows = [dict(main_rows[0], method_name=None), dict(main_rows[1], method_name=None)]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)
    write_jsonl(exp_dir / "main_results_summary_reported.jsonl", [])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    assert (exp_dir / "diag" / "metric_comparison.csv").exists()
    assert (exp_dir / "diag" / "metric_comparison.md").exists()
    assert (exp_dir / "diag" / "selection_score_debug.csv").exists()
    assert (exp_dir / "diag" / "same_selection_rate.csv").exists()
    assert result["metric_comparison"]
    assert any(row["status"] in {"OK", "MISSING"} for row in result["metric_comparison"])
    debug_text = (exp_dir / "diag" / "selection_score_debug.csv").read_text(encoding="utf-8")
    assert "objective_correct_posthoc" in debug_text


def test_diagnose_detects_reported_mismatch(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "main_results.jsonl", [_selected("Direct", "p0", "m_k0")])
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [_selected("candidate", "p0", "m_k0")])
    write_jsonl(exp_dir / "reported_main_summary.jsonl", [{"method": "Direct", "executable_rate": 0.0}])

    result = diagnose_selection_metrics(exp_dir=exp_dir, out_dir=exp_dir / "diag")

    mismatches = [row for row in result["metric_comparison"] if row["status"] == "MISMATCH"]
    assert any(row["method"] == "Direct" and row["metric"] == "executable_rate" for row in mismatches)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_diagnose_selection_metrics.py -q
```

Expected: FAIL because CLI module does not exist.

- [ ] **Step 3: Implement CLI module**

Create `replenishverifier/experiments/diagnose_selection_metrics.py`:

```python
import argparse
import json
from pathlib import Path

from replenishverifier.experiments.paper_metrics import (
    BASE_METRICS,
    compute_error_type_summary,
    compute_selected_method_metrics,
    compute_selection_diagnostics,
    format_metric_value,
    write_csv,
    write_markdown,
)
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _load_reported_summary(exp_dir):
    candidates = [
        exp_dir / "main_results_summary.jsonl",
        exp_dir / "reported_main_summary.jsonl",
        exp_dir / "main_results.jsonl.summary",
    ]
    for path in candidates:
        if path.exists():
            rows = read_jsonl(path)
            if rows:
                return rows
    summary_md = exp_dir / "summary.md"
    main_md = exp_dir / "main_results.md"
    if summary_md.exists() or main_md.exists():
        return []
    return []


def _reported_by_method(rows):
    return {row.get("method") or row.get("method_name"): row for row in rows}


def _compare_metrics(recomputed, reported_rows):
    reported = _reported_by_method(reported_rows)
    comparisons = []
    for row in recomputed:
        method = row["method"]
        reported_row = reported.get(method)
        for metric in BASE_METRICS:
            recomputed_value = row.get(metric)
            if not reported_row or metric not in reported_row:
                status = "MISSING"
                reported_value = None
                delta = None
            else:
                reported_value = reported_row.get(metric)
                try:
                    delta = float(recomputed_value) - float(reported_value)
                except (TypeError, ValueError):
                    delta = None
                status = "OK" if delta is not None and abs(delta) <= 1e-6 else "MISMATCH"
            comparisons.append({
                "method": method,
                "metric": metric,
                "reported": reported_value,
                "recomputed": recomputed_value,
                "delta": delta,
                "status": status,
            })
    return comparisons


def _compare_error_types(recomputed, reported_rows):
    reported = {(row.get("method"), row.get("error_type")): row for row in reported_rows}
    comparisons = []
    for row in recomputed:
        key = (row.get("method"), row.get("error_type"))
        report = reported.get(key)
        if report is None:
            status = "MISSING"
            reported_count = None
            delta = None
        else:
            reported_count = report.get("count")
            delta = int(row.get("count", 0)) - int(reported_count)
            status = "OK" if delta == 0 else "MISMATCH"
        comparisons.append({
            "method": row.get("method"),
            "error_type": row.get("error_type"),
            "reported": reported_count,
            "recomputed": row.get("count"),
            "delta": delta,
            "status": status,
        })
    return comparisons


def diagnose_selection_metrics(exp_dir, candidates_path=None, benchmark_path=None, out_dir=None):
    exp_dir = Path(exp_dir)
    out_dir = Path(out_dir) if out_dir else exp_dir / "selection_metric_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    main_rows = read_jsonl(exp_dir / "main_results.jsonl")
    candidate_rows = read_jsonl(exp_dir / "candidate_evaluations.jsonl") if (exp_dir / "candidate_evaluations.jsonl").exists() else []
    reported_summary = _load_reported_summary(exp_dir)
    recomputed_metrics = compute_selected_method_metrics(main_rows)
    metric_comparison = _compare_metrics(recomputed_metrics, reported_summary)

    recomputed_errors = compute_error_type_summary(main_rows)
    reported_error_path = exp_dir / "error_type_summary.jsonl"
    reported_errors = read_jsonl(reported_error_path) if reported_error_path.exists() else []
    error_comparison = _compare_error_types(recomputed_errors, reported_errors)

    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows)

    write_jsonl(out_dir / "metric_comparison.jsonl", metric_comparison)
    write_csv(out_dir / "metric_comparison.csv", metric_comparison)
    write_markdown(out_dir / "metric_comparison.md", metric_comparison, "Metric Comparison")
    write_jsonl(out_dir / "error_type_comparison.jsonl", error_comparison)
    write_csv(out_dir / "error_type_comparison.csv", error_comparison)
    write_markdown(out_dir / "error_type_comparison.md", error_comparison, "Error Type Comparison")
    write_csv(out_dir / "selection_score_debug.csv", diagnostics["selection_score_debug"])
    write_csv(out_dir / "same_selection_rate.csv", diagnostics["same_selection_rate"])
    write_csv(out_dir / "candidate_rank_distribution.csv", diagnostics["candidate_rank_distribution"])

    status_counts = {}
    for row in metric_comparison + error_comparison:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    summary = {
        "exp_dir": str(exp_dir),
        "candidates_path": str(candidates_path) if candidates_path else None,
        "benchmark_path": str(benchmark_path) if benchmark_path else None,
        "status_counts": status_counts,
        "note": "objective_correct_posthoc appears only in diagnostics and is not a formal selection signal.",
    }
    (out_dir / "diagnostic_summary.md").write_text(
        "# Selection Metric Diagnostics\n\n"
        + "```json\n"
        + json.dumps(summary, ensure_ascii=False, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    return {
        "metric_comparison": metric_comparison,
        "error_type_comparison": error_comparison,
        "selection_diagnostics": diagnostics,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Diagnose method-specific selection and metric aggregation.")
    parser.add_argument("--exp_dir", required=True)
    parser.add_argument("--candidates", default=None)
    parser.add_argument("--benchmark", default=None)
    parser.add_argument("--out_dir", default=None)
    args = parser.parse_args()
    diagnose_selection_metrics(args.exp_dir, candidates_path=args.candidates, benchmark_path=args.benchmark, out_dir=args.out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py -q
```

Expected: PASS.

---

### Task 5: Add `build_paper_metrics` CLI and paper tables

**Files:**
- Create: `replenishverifier/experiments/build_paper_metrics.py`
- Test: extend `tests/test_paper_metrics.py`

**Interfaces:**
- Produces CLI: `python -m replenishverifier.experiments.build_paper_metrics --exp_dir ... --out_dir ... --k_values 1,2,4 --bootstrap_samples 1000 --seed 42`
- Produces function: `build_paper_metrics(exp_dir, out_dir, k_values, bootstrap_samples=1000, seed=42) -> dict`
- Produces Markdown and CSV tables with stable names.

- [ ] **Step 1: Add failing test for paper table outputs**

Append to `tests/test_paper_metrics.py`:

```python
from replenishverifier.experiments.build_paper_metrics import build_paper_metrics
from replenishverifier.utils.io import write_jsonl


def test_build_paper_metrics_writes_expected_tables(tmp_path):
    exp_dir = tmp_path / "exp"
    out_dir = tmp_path / "paper"
    exp_dir.mkdir()
    main_rows = [_row("Direct", "p0", "model_k0")]
    candidate_rows = [_row("candidate", "p0", "model_k0")]
    write_jsonl(exp_dir / "main_results.jsonl", main_rows)
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", candidate_rows)

    result = build_paper_metrics(exp_dir, out_dir, k_values=[1], bootstrap_samples=20, seed=1)

    expected = [
        "table_main_metrics",
        "table_solver_status",
        "table_objective_gap",
        "table_structure_metrics",
        "table_objective_terms",
        "table_pass_at_k_oracle",
        "table_selection_diagnostics",
        "table_error_taxonomy",
        "table_runtime_cost",
        "table_bootstrap_ci",
    ]
    assert set(result["tables"]) == set(expected)
    for name in expected:
        assert (out_dir / f"{name}.csv").exists()
        assert (out_dir / f"{name}.md").exists()
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_paper_metrics.py::test_build_paper_metrics_writes_expected_tables -q
```

Expected: FAIL because `build_paper_metrics.py` does not exist.

- [ ] **Step 3: Implement `build_paper_metrics.py`**

Create `replenishverifier/experiments/build_paper_metrics.py`:

```python
import argparse
from pathlib import Path

from replenishverifier.experiments.paper_metrics import (
    add_bootstrap_ci,
    compute_error_type_summary,
    compute_pass_at_k,
    compute_selected_method_metrics,
    compute_selection_diagnostics,
    write_csv,
    write_markdown,
)
from replenishverifier.utils.io import read_jsonl


def parse_k_values(text):
    return [int(part.strip()) for part in str(text).split(",") if part.strip()]


def _select_columns(rows, columns):
    return [{column: row.get(column) for column in columns} for row in rows]


def _write_table(out_dir, name, title, rows):
    write_csv(out_dir / f"{name}.csv", rows)
    write_markdown(out_dir / f"{name}.md", rows, title)


def build_paper_metrics(exp_dir, out_dir, k_values, bootstrap_samples=1000, seed=42):
    exp_dir = Path(exp_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    main_rows = read_jsonl(exp_dir / "main_results.jsonl")
    candidate_rows = read_jsonl(exp_dir / "candidate_evaluations.jsonl") if (exp_dir / "candidate_evaluations.jsonl").exists() else []

    metrics = compute_selected_method_metrics(main_rows)
    metrics_with_ci = add_bootstrap_ci(metrics, main_rows, samples=bootstrap_samples, seed=seed)
    errors = compute_error_type_summary(main_rows)
    pass_at_k = compute_pass_at_k(candidate_rows, k_values) if candidate_rows else []
    diagnostics = compute_selection_diagnostics(main_rows, candidate_rows) if candidate_rows else {"same_selection_rate": [], "candidate_rank_distribution": [], "selection_score_debug": []}

    tables = {
        "table_main_metrics": _select_columns(metrics, ["method", "n", "code_validity_rate", "executable_rate", "optimal_rate", "objective_accuracy", "structure_completeness", "constraint_coverage", "objective_term_coverage"]),
        "table_solver_status": _select_columns(metrics, ["method", "n", "solver_status_optimal_rate", "solver_status_infeasible_rate", "solver_status_timeout_rate", "solver_status_error_rate"]),
        "table_objective_gap": _select_columns(metrics, ["method", "n", "objective_accuracy", "mean_relative_error", "median_relative_error", "mean_objective_gap", "median_objective_gap"]),
        "table_structure_metrics": _select_columns(metrics, ["method", "n", "structure_completeness", "inventory_balance_accuracy", "constraint_coverage"]),
        "table_objective_terms": _select_columns(metrics, ["method", "n", "objective_term_coverage"]),
        "table_pass_at_k_oracle": pass_at_k,
        "table_selection_diagnostics": diagnostics["candidate_rank_distribution"],
        "table_error_taxonomy": errors,
        "table_runtime_cost": _select_columns(metrics, ["method", "n", "average_runtime_sec", "median_runtime_sec", "average_repair_feedback_count"]),
        "table_bootstrap_ci": metrics_with_ci,
    }

    titles = {
        "table_main_metrics": "Table: Main Paper Metrics",
        "table_solver_status": "Table: Solver Status Metrics",
        "table_objective_gap": "Table: Objective Accuracy and Gap",
        "table_structure_metrics": "Table: Structure Metrics",
        "table_objective_terms": "Table: Objective Term Coverage",
        "table_pass_at_k_oracle": "Table: Pass@K and Oracle Upper Bounds",
        "table_selection_diagnostics": "Table: Selection Diagnostics",
        "table_error_taxonomy": "Table: Error Taxonomy",
        "table_runtime_cost": "Table: Runtime and Repair Feedback Cost",
        "table_bootstrap_ci": "Table: Bootstrap Confidence Intervals",
    }
    for name, rows in tables.items():
        _write_table(out_dir, name, titles[name], rows)
    return {"exp_dir": str(exp_dir), "out_dir": str(out_dir), "tables": list(tables)}


def main():
    parser = argparse.ArgumentParser(description="Build paper-grade metric tables from an existing experiment directory.")
    parser.add_argument("--exp_dir", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--k_values", default="1,2,4")
    parser.add_argument("--bootstrap_samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    build_paper_metrics(args.exp_dir, args.out_dir, parse_k_values(args.k_values), bootstrap_samples=args.bootstrap_samples, seed=args.seed)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_paper_metrics.py -q
```

Expected: PASS.

---

### Task 6: Strengthen leakage audit for formal vs post-hoc paths

**Files:**
- Modify: `replenishverifier/experiments/audit_leakage.py`
- Test: update `tests/test_preference_metadata.py`, `tests/test_strong_baselines.py`, or create/extend `tests/test_leakage_audit.py`

**Interfaces:**
- Existing `_audit_rows(rows, source, require_selected=True)` remains compatible.
- Add helper `is_posthoc_metric_row(row: dict) -> bool`.
- Formal rows fail if `uses_reference_objective_for_selection` is not False or if `selection_policy`/score metadata declares reference use.
- Post-hoc rows with `formal_selection_metric=False` may include oracle/reference metric flags.

- [ ] **Step 1: Write failing leakage tests**

Create `tests/test_leakage_audit.py`:

```python
from replenishverifier.experiments.audit_leakage import _audit_rows


def _formal_row(**updates):
    row = {
        "method_name": "Direct",
        "selected": True,
        "uses_reference_objective_for_selection": False,
        "selection_policy": "candidate order only; no reference objective",
        "score": 1.0,
        "selection_score": 1.0,
    }
    row.update(updates)
    return row


def test_formal_selection_rejects_reference_policy_marker():
    issues = _audit_rows([
        _formal_row(selection_policy="select closest to reference_objective")
    ], "main_results", require_selected=True)

    assert any("reference" in issue.lower() for issue in issues)


def test_formal_selection_rejects_reference_usage_flag():
    issues = _audit_rows([
        _formal_row(uses_reference_objective_for_selection=True)
    ], "main_results", require_selected=True)

    assert any("uses_reference_objective_for_selection" in issue for issue in issues)


def test_posthoc_oracle_metric_rows_are_allowed_when_marked_nonformal():
    issues = _audit_rows([
        {
            "k": 4,
            "formal_selection_metric": False,
            "uses_reference_for_oracle_metrics": True,
            "oracle_objective_accuracy_at_k": 1.0,
        }
    ], "paper_metrics", require_selected=False)

    assert issues == []
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_leakage_audit.py -q
```

Expected: At least one failure because post-hoc distinction or policy marker check is missing.

- [ ] **Step 3: Implement audit changes**

In `replenishverifier/experiments/audit_leakage.py`:

1. Add:

```python
def is_posthoc_metric_row(row):
    return row.get("formal_selection_metric") is False or row.get("uses_reference_for_oracle_metrics") is True
```

2. At top of row loop in `_audit_rows`, skip formal checks for post-hoc rows when `require_selected=False`:

```python
if not require_selected and is_posthoc_metric_row(row):
    continue
```

3. Add selection-policy text check for formal rows:

```python
policy = str(row.get("selection_policy") or "").lower()
for forbidden in ["closest to reference", "reference_objective", "objective_correct", "oracle"]:
    if forbidden in policy and "no reference objective" not in policy:
        issues.append(f"{source}: row {idx} selection_policy appears to use forbidden reference signal: {row.get('selection_policy')}")
```

4. Add explicit formal score provenance checks:

```python
if row.get("uses_reference_objective_for_selection") is not False:
    issues.append(...)
if row.get("uses_reference_for_oracle_metrics") is True and row.get("formal_selection_metric") is not False:
    issues.append(...)
```

Keep existing tests passing.

- [ ] **Step 4: Run focused leakage tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_leakage_audit.py tests/test_preference_metadata.py tests/test_strong_baselines.py -q
```

Expected: PASS.

---

### Task 7: Integrate diagnostics with existing outputs and run existing candidate re-evaluation only if fast enough

**Files:**
- Modify: `replenishverifier/experiments/evaluation.py` only if Task 3 reveals mismatch with expected old summaries.
- Modify: `progress.md`
- No new tests unless integration reveals a failure.

**Interfaces:**
- Existing `run_all_methods` output names remain compatible.
- Existing `analyze_error_types` remains selected-row based.

- [ ] **Step 1: Confirm old summary aggregation is selected-row specific**

Inspect `replenishverifier/experiments/evaluation.py`:

- `summarize_by_method()` must group only rows where `row.get("selected", False)` is true.
- `summarize_rows()` must compute from the supplied method rows and not from candidate pool or Direct rows.

If this is already true, do not change it.

- [ ] **Step 2: If mismatch exists, patch old summary helper**

Only if needed, modify `summarize_rows()` to keep the existing fields but delegate the shared definitions to `paper_metrics` helpers for:

- `constraint_coverage`
- `inventory_balance_accuracy`
- `average_repair_feedback_count`

Keep output keys unchanged to avoid breaking old docs/tests.

- [ ] **Step 3: Run focused metric tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_paper_metrics.py tests/test_diagnose_selection_metrics.py tests/test_type_aware_analysis.py -q
```

Expected: PASS.

- [ ] **Step 4: Run optional existing candidate re-evaluation without model generation**

If `data/candidates/qwen3_8b_k4_50_v3.jsonl` exists, run:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50_v3.jsonl \
  --out_dir runs/qwen3_8b_k4_50_v3_metricsfix \
  --k_values 1,2,4 \
  --timeout 30 \
  --no_demo_if_empty
```

Expected: completes using existing candidates only. If file is missing or command takes too long, stop and report that no model generation was run.

- [ ] **Step 5: Run post-processing on the metricsfix run if Step 4 completed**

Run:

```bash
python -m replenishverifier.experiments.analyze_error_types --exp_dir runs/qwen3_8b_k4_50_v3_metricsfix
python -m replenishverifier.experiments.diagnose_selection_metrics \
  --exp_dir runs/qwen3_8b_k4_50_v3_metricsfix \
  --candidates data/candidates/qwen3_8b_k4_50_v3.jsonl \
  --benchmark data/generated/test_50.jsonl
python -m replenishverifier.experiments.build_paper_metrics \
  --exp_dir runs/qwen3_8b_k4_50_v3_metricsfix \
  --out_dir runs/paper_metrics_qwen3_8b_k4_50_v3_metricsfix \
  --k_values 1,2,4
```

Expected: diagnostic and paper metric files are written. Do not alter candidates.

- [ ] **Step 6: Update `progress.md`**

Append a dated entry with:

```markdown
## 2026-06-18 — Paper metric and selection diagnostic upgrade

### User request

The user asked to upgrade ReplenishVerifier metrics to a paper-grade suite, diagnose whether method metrics are selected-candidate-specific, add `--model_label`, add objective-term coverage, pass@k/oracle/bootstrap metrics, and preserve no-reference formal selection.

### Actions completed

- Added optional generation `model_label` metadata while keeping legacy candidate IDs when omitted.
- Added evaluation-only objective-term coverage.
- Added paper metric aggregation and table builder.
- Added method-specific selection/metric diagnostics.
- Strengthened leakage audit separation between formal selection and post-hoc oracle metrics.

### Verification

- Focused tests: [fill with exact command and result after running].
- Full tests: [fill with exact command and result after running].

### Notes

No LLM generation or candidate regeneration was run. Formal selection remains no-reference; oracle/pass@k metrics are post-hoc evaluation-only.
```

Replace bracketed verification lines with exact command/result observed before writing.

---

### Task 8: Final verification and required status/diff reporting

**Files:**
- No code changes unless verification fails.

**Interfaces:**
- Produces final user-facing summary with exact answers to the requested 20-point checklist.

- [ ] **Step 1: Run formatting/syntax checks**

Run:

```bash
git diff --check
python -m py_compile \
  replenishverifier/llm/run_generation.py \
  replenishverifier/experiments/objective_terms.py \
  replenishverifier/experiments/paper_metrics.py \
  replenishverifier/experiments/diagnose_selection_metrics.py \
  replenishverifier/experiments/build_paper_metrics.py \
  replenishverifier/experiments/audit_leakage.py
```

Expected: both commands pass. If `git diff --check` reports existing unrelated line-ending warnings only, report them precisely.

- [ ] **Step 2: Run focused tests**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest \
  tests/test_run_generation_model_label.py \
  tests/test_objective_term_coverage.py \
  tests/test_paper_metrics.py \
  tests/test_diagnose_selection_metrics.py \
  tests/test_leakage_audit.py \
  -q
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Expected: PASS. Record count and warnings exactly.

- [ ] **Step 4: Run final git status and diff name list**

Run:

```bash
git status --short
git diff --name-only
```

Expected: shows modified/created files in the main repository. It may also show pre-existing `.claude/worktrees/...` deletion entries; do not modify or clean those unless explicitly asked.

- [ ] **Step 5: Final response content**

Answer in Chinese and include:

1. Current directory is `/home/dongaorui/projects/lunwen` or report if not.
2. Whether any worktree was created; expected answer: no.
3. Whether `--model_label` was missing and whether it was added.
4. Whether `diagnose_selection_metrics` was added.
5. Whether `build_paper_metrics` was added.
6. What diagnostics show for v3 vs v2 similarity if the runs were analyzed; if not analyzed, state not run yet.
7. Same-selection rates for Direct / ReplenishVerifier-Full / Best-of-K / Consensus if diagnostics ran; otherwise point to command to generate them.
8. k0/k1/k2/k3 distribution if diagnostics ran; otherwise point to output file path.
9. Whether reported vs recomputed main results are consistent if diagnostics ran.
10. Files changed.
11. New metrics added.
12. Definitions of each new metric family.
13. Which metrics are formal-selection-eligible and which are post-hoc only.
14. Whether objective-term coverage is implemented.
15. Whether pass@k / oracle upper bound is implemented.
16. Whether bootstrap CI is implemented.
17. Whether leakage audit was updated.
18. Pytest result.
19. Whether metricsfix main_results changed versus previous run if re-evaluation ran; if not compared, state not compared.
20. Next commands the user should run to generate paper tables.

---

## Self-Review

### Spec coverage

- Direct main-directory modification and no worktree: covered by Global Constraints and final verification.
- `--model_label` compatibility: Task 1.
- `diagnose_selection_metrics`: Task 4.
- Paper metrics/tables/pass@k/oracle/bootstrap CI: Tasks 3 and 5.
- Objective-term coverage: Task 2.
- Selection/metrics bug diagnosis and selected-row recomputation: Tasks 3 and 4.
- Selection score debug and same-selection/rank distribution: Tasks 3 and 4.
- Leakage audit: Task 6.
- Existing candidates only, no LLM generation: Global Constraints and Task 7.
- Tests and final status/diff: Tasks 1-8.

### Placeholder scan

This plan intentionally contains no `TBD`, no open-ended implementation placeholders, and no steps that say only “write tests” without test code.

### Type consistency

The new functions are consistently named across tasks:

- `evaluate_objective_terms`
- `compute_selected_method_metrics`
- `compute_error_type_summary`
- `compute_pass_at_k`
- `compute_selection_diagnostics`
- `diagnose_selection_metrics`
- `build_paper_metrics`
