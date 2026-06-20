# k8 Diagnostics Minimal Gap Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the remaining k=8 diagnostics reporting gaps by adding selected-source provenance, candidate-rank parse reasons, and more TypeAware-Consensus debug fields without changing generation or formal no-reference selection.

**Architecture:** Keep candidate-id parsing and selected/candidate matching centralized in `replenishverifier/experiments/paper_metrics.py`. Keep CSV/Markdown writing in `replenishverifier/experiments/diagnose_selection_metrics.py`. Add tests in the existing diagnostics test module before production changes.

**Tech Stack:** Python 3.10+, pytest, existing CSV/Markdown helpers in ReplenishVerifier.

## Global Constraints

- Do not regenerate candidates.
- Do not modify `replenishverifier/llm/run_generation.py`.
- Do not call any LLM.
- Formal selection must not use `reference_objective`, `objective_correct`, oracle metrics, reference LP, or reference answers.
- Keep backward compatibility for existing k=1/2/4 flows.
- The real 800-row k=8/100 experiment is not run in this checkout; only tests and small diagnostics behavior are verified locally.
- No git commit or push is performed unless the user explicitly asks.

---

### Task 1: Add diagnostics regression tests for unmatched provenance and parse reasons

**Files:**
- Modify: `tests/test_diagnose_selection_metrics.py`

**Interfaces:**
- Consumes: `compute_and_write_diagnostics(exp_dir, out_dir)` from `replenishverifier.experiments.diagnose_selection_metrics`.
- Produces: Failing tests that require `diagnostic_join_unmatched` rows to include `selected_file_or_source`, `candidate_rank_parse_reason`, and `matched_candidate_id`, and require CSV output to contain those headers.

- [ ] **Step 1: Write failing test**

Add a test near the existing unmatched diagnostics tests:

```python
def test_diagnostic_join_unmatched_records_source_and_rank_parse_reason(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    _write_jsonl(exp_dir / "main_results.jsonl", [
        _selected(
            "ReplenishVerifier-TypeAware-Consensus",
            "p0",
            "Qwen3-8B_candidate_without_rank",
            selected_file_or_source="main_results.jsonl",
        ),
    ])
    _write_jsonl(exp_dir / "candidate_evaluations.jsonl", [
        _candidate("p0", "Qwen3-8B_k7"),
    ])

    result = compute_and_write_diagnostics(exp_dir, exp_dir / "diagnostics")

    unmatched = result["diagnostic_join_unmatched"]
    assert unmatched == [{
        "method": "ReplenishVerifier-TypeAware-Consensus",
        "problem_id": "p0",
        "candidate_id": "Qwen3-8B_candidate_without_rank",
        "parsed_candidate_rank": None,
        "candidate_rank_parse_reason": "no_k_rank_pattern",
        "reason": "candidate_id_not_found_for_problem",
        "matched_candidate_id": "",
        "selected_file_or_source": "main_results.jsonl",
    }]
    csv_text = (exp_dir / "diagnostics" / "diagnostic_join_unmatched.csv").read_text(encoding="utf-8")
    assert "selected_file_or_source" in csv_text
    assert "candidate_rank_parse_reason" in csv_text
```

If existing helpers do not accept `selected_file_or_source`, add it to the row dict after constructing the selected row inside the test.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python -m pytest tests/test_diagnose_selection_metrics.py::test_diagnostic_join_unmatched_records_source_and_rank_parse_reason -q
```

Expected: FAIL because the current diagnostics rows and CSV headers do not contain `selected_file_or_source` / `candidate_rank_parse_reason`.

---

### Task 2: Implement selected-source and parse-reason diagnostics

**Files:**
- Modify: `replenishverifier/experiments/paper_metrics.py`
- Modify: `replenishverifier/experiments/diagnose_selection_metrics.py`

**Interfaces:**
- Produces: `normalize_candidate_id(candidate_id)` returns `candidate_id`, `parsed_candidate_rank`, and `candidate_rank_parse_reason`.
- Produces: `compute_selection_diagnostics()` unmatched rows include `candidate_rank_parse_reason`, `matched_candidate_id`, and `selected_file_or_source`.
- Produces: `diagnostic_join_unmatched.csv` writes the new fields.

- [ ] **Step 1: Update candidate-id normalization**

In `paper_metrics.py`, change `normalize_candidate_id()` to return parse reason:

```python
def candidate_rank_parse_reason(candidate_id):
    text = str(candidate_id or "").strip()
    if not text:
        return "empty_candidate_id"
    if parse_candidate_rank(text) is None:
        return "no_k_rank_pattern"
    return "ok"


def normalize_candidate_id(candidate_id):
    text = str(candidate_id or "").strip()
    return {
        "candidate_id": text,
        "parsed_candidate_rank": parse_candidate_rank(text),
        "candidate_rank_parse_reason": candidate_rank_parse_reason(text),
    }
```

- [ ] **Step 2: Add selected-source helper**

In `paper_metrics.py`, add a helper near `_selected_candidate_match()`:

```python
def _selected_file_or_source(row):
    return (
        row.get("selected_file_or_source")
        or row.get("selected_source")
        or row.get("source")
        or row.get("source_file")
        or row.get("selected_file")
        or "main_results"
    )
```

- [ ] **Step 3: Extend unmatched rows**

In `compute_selection_diagnostics()`, unmatched rows should include:

```python
"candidate_rank_parse_reason": norm["candidate_rank_parse_reason"],
"matched_candidate_id": matched_candidate_id or "",
"selected_file_or_source": _selected_file_or_source(row),
```

Keep the existing fields unchanged.

- [ ] **Step 4: Extend selection-score debug rows**

In the debug row dict in `compute_selection_diagnostics()`, add safe candidate-visible fields:

```python
"candidate_rank_parse_reason": norm["candidate_rank_parse_reason"],
"matched_candidate_id": norm["candidate_id"],
"type_aware_score": row.get("type_aware_static_validation_score", (row.get("type_aware_static_validation") or {}).get("score")),
"hard_gate_score": (row.get("type_aware_static_validation") or {}).get("hard_gate_score"),
"type_aware_hard_gate_failures": ";".join((row.get("type_aware_static_validation") or {}).get("hard_gate_failures") or []),
"critical_missing_structures": ";".join(row.get("critical_missing_structures") or []),
```

These are candidate-visible diagnostics only and do not affect selection.

- [ ] **Step 5: Extend unmatched CSV headers**

In `diagnose_selection_metrics.py`, update `_write_join_unmatched_csv()` fields to include:

```python
fields = [
    "method",
    "problem_id",
    "candidate_id",
    "parsed_candidate_rank",
    "candidate_rank_parse_reason",
    "reason",
    "matched_candidate_id",
    "selected_file_or_source",
]
```

- [ ] **Step 6: Run RED test to verify GREEN**

Run:

```bash
python -m pytest tests/test_diagnose_selection_metrics.py::test_diagnostic_join_unmatched_records_source_and_rank_parse_reason -q
```

Expected: PASS.

---

### Task 3: Run focused and full verification, update planning files

**Files:**
- Modify: `progress.md`
- Modify: `task_plan.md`

**Interfaces:**
- Produces: Fresh evidence for diagnostics behavior and suite compatibility.

- [ ] **Step 1: Run diagnostics-focused tests**

Run:

```bash
python -m pytest tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run broader focused regression suite**

Run:

```bash
python -m pytest tests/test_static_validation.py tests/test_selection_gating.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_structure_schema.py tests/test_structure_rules.py tests/test_run_all_methods_grouping.py tests/test_leakage_audit.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run full suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass. Report warning count exactly.

- [ ] **Step 4: Compile changed Python modules**

Run:

```bash
python -m py_compile replenishverifier/experiments/paper_metrics.py replenishverifier/experiments/diagnose_selection_metrics.py
```

Expected: exit code 0.

- [ ] **Step 5: Update planning files**

Append a progress entry to `progress.md` and update `task_plan.md` with a new phase noting changed files, tests, and that no candidates were regenerated and `run_generation.py` was untouched.

---

## Self-Review

- Spec coverage: The plan covers selected-source provenance, parse reason diagnostics, debug-field enrichment, tests, focused/full verification, and planning-file updates.
- Placeholder scan: No TBD/TODO placeholders remain; code snippets name exact fields and files.
- Type consistency: New field names are consistent across tests, diagnostics dicts, and CSV headers.
