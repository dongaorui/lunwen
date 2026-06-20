# Selector Diagnostics Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair `ReplenishVerifier-TypeAware-Consensus` and `ReplenishVerifier-Full` so they use distinct, no-reference selector logic and no longer collapse by construction to TypeAware or Structure only.

**Architecture:** Keep changes concentrated in `replenishverifier/experiments/methods.py`. Add small helper functions for finite objective/LP health/Full composite components and adjust only method-specific raw scores/tie-breaks. Use synthetic tests in `tests/test_selection_gating.py` to prove the intended separation before implementation.

**Tech Stack:** Python 3.10+, pytest, existing ReplenishVerifier experiment modules.

## Global Constraints

- Do not regenerate candidates.
- Do not modify `replenishverifier/llm/run_generation.py`.
- Do not delete existing methods.
- Keep backward-compatible method names and output fields.
- Formal selection must not use `reference_objective`, `objective_correct`, `objective_accuracy` as correctness labels, `relative_error`, oracle fields, reference LP, or reference answer.
- Reference/correctness fields may appear only in post-hoc evaluation and diagnostics.
- Use TDD: write failing tests first and verify they fail before production-code changes.

---

## File Structure

- Modify `tests/test_selection_gating.py`: add regression tests for TypeAware-Consensus cluster-first behavior and Full tie-window behavior.
- Modify `replenishverifier/experiments/methods.py`: add no-reference helper functions and update `ReplenishVerifier-TypeAware-Consensus` and `ReplenishVerifier-Full` ranking/annotation logic.
- Modify `task_plan.md`, `findings.md`, `progress.md`: record phase completion, findings, verification output, and errors.
- Use existing experiment package files under `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/` for rerun inputs and outputs; decompress the existing `.jsonl.gz` candidates only as an input conversion step.

---

### Task 1: Add failing selector-regression tests

**Files:**
- Modify: `tests/test_selection_gating.py`

**Interfaces:**
- Consumes: existing `_row()`, `_benchmark()`, and `select_for_method()` helpers.
- Produces: two tests that must fail before implementation and pass after implementation.

- [ ] **Step 1: Add imports if needed**

No new imports are required beyond the existing `select_for_method` import.

- [ ] **Step 2: Add TypeAware-Consensus cluster-first regression test**

Append this test near the existing TypeAware-Consensus tests:

```python
def test_type_aware_consensus_prefers_majority_objective_cluster_over_isolated_typeaware_score():
    rows = [
        _row("c0", structure_score=1.0, missing=[], consensus=1 / 3),
        _row("c1", structure_score=0.92, missing=[], consensus=2 / 3),
        _row("c2", structure_score=0.90, missing=[], consensus=2 / 3),
    ]
    rows[0]["execution"]["objective"] = 100.0
    rows[1]["execution"]["objective"] = 42.0
    rows[2]["execution"]["objective"] = 42.000001
    rows[0]["objective_term_coverage"] = 1.0
    rows[1]["objective_term_coverage"] = 0.9
    rows[2]["objective_term_coverage"] = 0.88
    rows[0]["type_aware_static_validation"] = {
        "score": 1.0,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
    }
    rows[1]["type_aware_static_validation"] = {
        "score": 0.92,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
    }
    rows[2]["type_aware_static_validation"] = {
        "score": 0.90,
        "hard_gate_score": 1.0,
        "hard_gate_failures": [],
        "missing_items": [],
    }
    for row in rows:
        row["type_aware_static_validation_errors"] = []
        row["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 3, "variables_count": 3}
        row["code_output_format_valid"] = True
        row["static_validation_score"] = 1.0

    type_aware = select_for_method("ReplenishVerifier-TypeAware", {"p0": rows}, _benchmark())
    consensus = select_for_method("ReplenishVerifier-TypeAware-Consensus", {"p0": rows}, _benchmark())

    assert type_aware[0]["candidate_id"] == "c0"
    assert consensus[0]["candidate_id"] in {"c1", "c2"}
    assert consensus[0]["selection_components"]["consensus_cluster_support"] == 2 / 3
    assert consensus[0]["selection_components"].keys().isdisjoint({
        "reference_objective",
        "objective_correct",
        "relative_error",
        "oracle",
        "reference_lp",
        "reference_answer",
    })
```

- [ ] **Step 3: Add Full vs Structure-only tie-window regression test**

Append this test near the Full/Structure tests:

```python
def test_full_can_select_different_candidate_from_structure_only_when_structure_ties():
    rows = [
        _row("c0", score=0.80, structure_score=0.80, missing=[], consensus=0.10),
        _row("c1", score=0.80, structure_score=0.80, missing=[], consensus=0.90),
    ]
    rows[0]["execution"] = {"executable": True, "status": "Optimal", "objective": 100.0, "lp_path": "a.lp"}
    rows[1]["execution"] = {"executable": True, "status": "Optimal", "objective": 42.0, "lp_path": "b.lp"}
    rows[0]["objective_term_coverage"] = 0.6
    rows[1]["objective_term_coverage"] = 1.0
    rows[0]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 1, "variables_count": 2}
    rows[1]["lp_stats"] = {"lp_exported": True, "objective_present": True, "constraints_count": 4, "variables_count": 4}
    rows[0]["type_aware_static_validation"] = {"score": 0.7, "hard_gate_score": 0.7, "hard_gate_failures": ["weak"], "missing_items": ["weak"]}
    rows[1]["type_aware_static_validation"] = {"score": 1.0, "hard_gate_score": 1.0, "hard_gate_failures": [], "missing_items": []}
    rows[0]["type_aware_static_validation_errors"] = ["weak"]
    rows[1]["type_aware_static_validation_errors"] = []
    rows[0]["code_output_format_valid"] = False
    rows[1]["code_output_format_valid"] = True
    rows[0]["static_validation_score"] = 0.5
    rows[1]["static_validation_score"] = 1.0

    structure_only = select_for_method("Structure only", {"p0": rows}, _benchmark())
    full = select_for_method("ReplenishVerifier-Full", {"p0": rows}, _benchmark())

    assert structure_only[0]["candidate_id"] == "c0"
    assert full[0]["candidate_id"] == "c1"
    assert full[0]["selection_components"]["consensus_score"] == 0.90
    assert full[0]["selection_components"].keys().isdisjoint({
        "reference_objective",
        "objective_correct",
        "relative_error",
        "oracle",
        "reference_lp",
        "reference_answer",
    })
```

- [ ] **Step 4: Run the two new tests and verify RED**

Run:

```bash
python -m pytest \
  tests/test_selection_gating.py::test_type_aware_consensus_prefers_majority_objective_cluster_over_isolated_typeaware_score \
  tests/test_selection_gating.py::test_full_can_select_different_candidate_from_structure_only_when_structure_ties \
  -q
```

Expected before implementation:

- At least one test fails.
- The TypeAware-Consensus test should fail because `consensus_cluster_support` is missing or the isolated candidate is selected.
- The Full test should fail because Full still selects `c0` or lacks `selection_components`.

---

### Task 2: Implement no-reference TypeAware-Consensus cluster-first ranking

**Files:**
- Modify: `replenishverifier/experiments/methods.py`
- Test: `tests/test_selection_gating.py`

**Interfaces:**
- Consumes: `row["objective_consensus_score"]`, `row["execution"]["objective"]`, `type_aware_selection_components(row)`, `_critical_missing_structures(row)`, `_lp_health_score(row)`, `_code_validity_score(row)`, `_static_validation_score(row)`.
- Produces: `type_aware_consensus_selection_components(row)` with `finite_objective`, `lp_health_score`, `code_validity_score`, `static_validation_score`, and `consensus_cluster_support`.

- [ ] **Step 1: Add finite objective helper**

Add near `_has_objective_score()`:

```python
def _finite_objective_score(row):
    objective = (row.get("execution") or {}).get("objective")
    if objective is None:
        return 0.0
    try:
        value = float(objective)
    except (TypeError, ValueError):
        return 0.0
    if value != value or value in {float("inf"), float("-inf")}:
        return 0.0
    return 1.0
```

- [ ] **Step 2: Extend TypeAware-Consensus components**

Replace `type_aware_consensus_selection_components(row)` with:

```python
def type_aware_consensus_selection_components(row):
    base = type_aware_selection_components(row)
    critical_missing = _critical_missing_structures(row)
    cluster_support = float(row.get("objective_consensus_score", base.get("consensus_score", 0.0)) or 0.0)
    base["finite_objective"] = _finite_objective_score(row)
    base["lp_health_score"] = _lp_health_score(row)
    base["code_validity_score"] = _code_validity_score(row)
    base["static_validation_score"] = _static_validation_score(row)
    base["critical_missing_count"] = float(len(critical_missing))
    base["critical_structure_pass"] = 1.0 if not critical_missing else 0.0
    base["critical_missing_structures"] = critical_missing
    base["consensus_cluster_support"] = cluster_support
    base["consensus_bucket"] = round(cluster_support / 0.05) * 0.05
    return base
```

- [ ] **Step 3: Update TypeAware-Consensus score to make cluster support dominant after hard viability**

Replace `type_aware_consensus_selection_score(row)` with:

```python
def type_aware_consensus_selection_score(row):
    c = type_aware_consensus_selection_components(row)
    return float(
        100000.0 * c["executable"]
        + 50000.0 * c["solver_optimal"]
        + 10000.0 * c["finite_objective"]
        + 5000.0 * c["consensus_cluster_support"]
        + 350.0 * c["lp_health_score"]
        + 250.0 * c["structure_completeness"]
        + 200.0 * c["constraint_coverage"]
        + 150.0 * c["objective_term_coverage"]
        + 80.0 * c["hard_gate_score"]
        + 40.0 * c["type_aware_score"]
        + 20.0 * c["code_validity_score"]
        + 10.0 * c["static_validation_score"]
        - 120.0 * c["critical_missing_count"]
        - 2.0 * c["repair_feedback_count"]
        - 0.1 * c["runtime_sec"]
    )
```

- [ ] **Step 4: Update TypeAware-Consensus tie-break key**

In `_selection_tie_break_key_for_method`, replace the TypeAware-Consensus tuple with:

```python
        return (
            gated,
            components["solver_optimal"],
            components["finite_objective"],
            components["consensus_cluster_support"],
            components["consensus_bucket"],
            components["lp_health_score"],
            components["critical_structure_pass"],
            -components["critical_missing_count"],
            components["constraint_coverage"],
            components["objective_term_coverage"],
            components["structure_completeness"],
            components["hard_gate_score"],
            components["type_aware_score"],
            components["code_validity_score"],
            components["static_validation_score"],
            -components["repair_feedback_count"],
            runtime,
            candidate_order,
        )
```

- [ ] **Step 5: Run TypeAware-Consensus regression test and verify GREEN for this task**

Run:

```bash
python -m pytest tests/test_selection_gating.py::test_type_aware_consensus_prefers_majority_objective_cluster_over_isolated_typeaware_score -q
```

Expected: PASS.

---

### Task 3: Implement Full composite no-reference ranking with structure tie-window

**Files:**
- Modify: `replenishverifier/experiments/methods.py`
- Test: `tests/test_selection_gating.py`

**Interfaces:**
- Consumes: helpers from Task 2 plus `_structure_score(row)`, `_constraint_coverage(row)`, `_objective_term_coverage(row)`, `_critical_missing_structures(row)`, `_type_aware_validation_score(row)`, `_type_aware_hard_gate_score(row)`.
- Produces: `full_selection_components(row)` and `full_selection_score(row)`; selected Full rows receive `selection_components`.

- [ ] **Step 1: Add Full component helper**

Add before `consensus_safe_selection_components(row)`:

```python
def full_selection_components(row):
    execution = row.get("execution") or {}
    status = str(execution.get("status") or "")
    executable = 1.0 if execution.get("executable") else 0.0
    solver_optimal = 1.0 if status == "Optimal" else 0.0
    critical_missing = _critical_missing_structures(row)
    structure = _structure_score(row)
    constraint = _constraint_coverage(row)
    objective_terms = _objective_term_coverage(row)
    consensus = float(row.get("objective_consensus_score", 0.0) or 0.0)
    lp_health = _lp_health_score(row)
    type_aware_score = _type_aware_validation_score(row)
    hard_gate_score = _type_aware_hard_gate_score(row)
    static_score = _static_validation_score(row)
    code_score = _code_validity_score(row)
    finite_objective = _finite_objective_score(row)
    return {
        "executable": executable,
        "solver_optimal": solver_optimal,
        "finite_objective": finite_objective,
        "structure_completeness": structure,
        "structure_tie_bucket": round(structure / 0.05) * 0.05,
        "constraint_coverage": constraint,
        "objective_term_coverage": objective_terms,
        "consensus_score": consensus,
        "lp_health_score": lp_health,
        "type_aware_score": type_aware_score,
        "hard_gate_score": hard_gate_score,
        "static_validation_score": static_score,
        "code_validity_score": code_score,
        "critical_missing_count": float(len(critical_missing)),
        "critical_structure_pass": 1.0 if not critical_missing else 0.0,
        "critical_missing_structures": critical_missing,
        "repair_feedback_count": float(_type_aware_repair_feedback_count(row)),
        "runtime_sec": _runtime_sec(row),
    }
```

- [ ] **Step 2: Add Full score helper**

Add below `full_selection_components(row)`:

```python
def full_selection_score(row):
    c = full_selection_components(row)
    within_structure_bucket_quality = float(
        0.30 * c["consensus_score"]
        + 0.18 * c["solver_optimal"]
        + 0.12 * c["finite_objective"]
        + 0.12 * c["lp_health_score"]
        + 0.10 * c["constraint_coverage"]
        + 0.08 * c["objective_term_coverage"]
        + 0.04 * c["hard_gate_score"]
        + 0.03 * c["type_aware_score"]
        + 0.02 * c["static_validation_score"]
        + 0.01 * c["code_validity_score"]
    )
    return float(
        100000.0 * c["executable"]
        + 50000.0 * c["solver_optimal"]
        + 10000.0 * c["finite_objective"]
        + 2000.0 * c["structure_tie_bucket"]
        + 1000.0 * within_structure_bucket_quality
        + 300.0 * c["structure_completeness"]
        - 250.0 * c["critical_missing_count"]
        - 2.0 * c["repair_feedback_count"]
        - 0.1 * c["runtime_sec"]
    )
```

- [ ] **Step 3: Route Full raw score through new helper**

In `_method_raw_score(row, method_name)`, replace the Full branch:

```python
    if method_name in {"ReplenishVerifier-Full", "ReplenishVerifier-Repair"}:
        return row.get("raw_inference_score", row.get("score", 0.0))
```

with:

```python
    if method_name == "ReplenishVerifier-Full":
        return full_selection_score(row)
    if method_name == "ReplenishVerifier-Repair":
        return row.get("raw_inference_score", row.get("score", 0.0))
```

- [ ] **Step 4: Update Full tie-break key**

In `_selection_tie_break_key_for_method`, replace the `ReplenishVerifier-Full` branch with:

```python
    if method_name in {"ReplenishVerifier-Full", "ReplenishVerifier full"}:
        components = full_selection_components(row)
        return (
            gated,
            components["structure_tie_bucket"],
            components["consensus_score"],
            components["solver_optimal"],
            components["finite_objective"],
            components["lp_health_score"],
            components["constraint_coverage"],
            components["objective_term_coverage"],
            components["hard_gate_score"],
            components["type_aware_score"],
            components["static_validation_score"],
            components["code_validity_score"],
            components["structure_completeness"],
            components["critical_structure_pass"],
            -components["critical_missing_count"],
            candidate_order,
        )

    if method_name == "ReplenishVerifier-Repair":
        return (
            gated,
            _structure_score(row),
            _constraint_coverage(row),
            _objective_term_coverage(row),
            _rule_score(row, "inventory_balance"),
            _static_validation_score(row),
            candidate_order,
        )
```

- [ ] **Step 5: Annotate Full selected components**

In `_annotate_selected_score(best, method_name, allow_feasible_selection=False)`, add before the ConsensusSafe annotation:

```python
    if method_name == "ReplenishVerifier-Full":
        best["selection_components"] = full_selection_components(best)
        best["hard_gate_failures"] = _type_aware_hard_gate_failures(best)
        best["hard_gate_score"] = best["selection_components"]["hard_gate_score"]
        best["constraint_coverage"] = best["selection_components"]["constraint_coverage"]
        best["objective_term_coverage"] = best["selection_components"]["objective_term_coverage"]
        best["repair_feedback_count"] = best["selection_components"]["repair_feedback_count"]
```

- [ ] **Step 6: Update Full selection policy text**

In `select_for_method()`, add an explicit branch before ConsensusSafe:

```python
        elif method_name == "ReplenishVerifier-Full":
            best["selection_policy"] = "Hard Selection Gate over executable + optimal candidates, ranked by structure-first tie-window with candidate objective consensus, LP health, constraint coverage, objective-term coverage, type-aware/static validation, and critical-structure safety; no reference objective"
```

- [ ] **Step 7: Run Full regression test and verify GREEN for this task**

Run:

```bash
python -m pytest tests/test_selection_gating.py::test_full_can_select_different_candidate_from_structure_only_when_structure_ties -q
```

Expected: PASS.

---

### Task 4: Run focused regression and leakage tests

**Files:**
- No production code unless tests fail and root cause points to current changes.

**Interfaces:**
- Consumes: Tasks 1-3 completed.
- Produces: verified focused tests.

- [ ] **Step 1: Run selector tests**

Run:

```bash
python -m pytest tests/test_selection_gating.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run focused selector/diagnostic/leakage suite**

Run:

```bash
python -m pytest \
  tests/test_selection_gating.py \
  tests/test_diagnose_selection_metrics.py \
  tests/test_paper_metrics.py \
  tests/test_leakage_audit.py \
  tests/test_run_all_methods_grouping.py \
  -q
```

Expected: all tests pass.

- [ ] **Step 3: Run compile check**

Run:

```bash
python -m py_compile replenishverifier/experiments/methods.py
```

Expected: command exits successfully.

---

### Task 5: Re-run package experiment and diagnostics without candidate regeneration

**Files:**
- Read: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/data/generated/test_100_v6.jsonl`
- Read/decompress: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl.gz`
- Write run outputs under: `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix`
- Write paper metrics under: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_selectorfix_compare`

**Interfaces:**
- Consumes: existing package benchmark/candidates.
- Produces: fresh run, diagnostics, audit, and paper metrics.

- [ ] **Step 1: Decompress existing candidate artifact to a local input file**

Run:

```bash
python - <<'PY'
import gzip
from pathlib import Path
base = Path('experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026')
src = base / 'docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl.gz'
dst = base / 'docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl'
with gzip.open(src, 'rt', encoding='utf-8') as fin, dst.open('w', encoding='utf-8') as fout:
    for line in fin:
        fout.write(line)
print(dst)
PY
```

Expected: prints the decompressed `.jsonl` path. This is not candidate regeneration.

- [ ] **Step 2: Run all methods**

Run:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/data/generated/test_100_v6.jsonl \
  --candidates experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl \
  --out_dir runs/qwen3_8b_k8_100_v6_typeaware_selectorfix \
  --k_values 1,2,4,8 \
  --timeout 30 \
  --no_demo_if_empty
```

Expected: run completes and writes `main_results.jsonl`, `main_results.md`, and `candidate_evaluations.jsonl`.

- [ ] **Step 3: Run diagnostics**

Run:

```bash
python -m replenishverifier.experiments.diagnose_selection_metrics \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_selectorfix \
  --candidates experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl \
  --benchmark experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/data/generated/test_100_v6.jsonl \
  --out_dir runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/diagnostics
```

Expected: diagnostics include `diagnostic_join_unmatched.csv` and `method_redundancy_report.md`.

- [ ] **Step 4: Run error analysis**

Run:

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_selectorfix
```

Expected: error summary files are written in the run directory.

- [ ] **Step 5: Run leakage audit**

Run:

```bash
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_selectorfix \
  --write_report
```

Expected: `LEAKAGE AUDIT PASSED`.

- [ ] **Step 6: Build paper metrics**

Run:

```bash
python -m replenishverifier.experiments.build_paper_metrics \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_selectorfix \
  --out_dir experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_selectorfix_compare/paper_metrics \
  --k_values 1,2,4,8 \
  --bootstrap_samples 1000 \
  --seed 42
```

Expected: paper metric tables are written.

---

### Task 6: Full verification and report extraction

**Files:**
- Read: `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/main_results.md`
- Read: `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/diagnostics/method_redundancy_report.md`
- Read: `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/diagnostics/diagnostic_join_unmatched.csv`
- Read: `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/no_leakage_audit.json`
- Modify: `task_plan.md`, `findings.md`, `progress.md`

**Interfaces:**
- Consumes: completed rerun and diagnostics.
- Produces: final evidence summary for user.

- [ ] **Step 1: Run full pytest suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Extract main objective accuracies**

Read `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/main_results.md` and record objective_accuracy for all main methods.

- [ ] **Step 3: Extract redundancy rates**

Read `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/diagnostics/method_redundancy_report.md` and record:

- `ReplenishVerifier-TypeAware` vs `ReplenishVerifier-TypeAware-Consensus` same_selection_rate.
- `ReplenishVerifier-Full` vs `Structure only` same_selection_rate.

- [ ] **Step 4: Check diagnostic join unmatched output**

Read `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/diagnostics/diagnostic_join_unmatched.csv` and record whether it exists, row count, and reason counts.

- [ ] **Step 5: Update planning files**

Append concise updates to:

- `task_plan.md`: add new phase status, changed files, verification.
- `findings.md`: add root cause and final no-reference selector behavior.
- `progress.md`: add commands run and outputs.

- [ ] **Step 6: Final response**

Report exactly:

1. Changed files.
2. Old vs new TypeAware-Consensus logic.
3. Old vs new Full logic.
4. Synthetic tests added and result.
5. Whether diagnostics MISSING semantics are separated.
6. Whether `diagnostic_join_unmatched.csv` was generated.
7. No-leakage audit result.
8. Pytest result.
9. Re-run `main_results.md` objective_accuracy values.
10. Redundancy report rates for TypeAware vs TypeAware-Consensus and Full vs Structure only.

Do not claim real improvement if the rerun does not improve.

---

## Self-Review

- Spec coverage: Tasks 1-3 implement selector logic and tests; Tasks 4-6 verify diagnostics, leakage, pytest, and experiment rerun. All constraints from the design spec are represented.
- Placeholder scan: no TBD/TODO/fill-later placeholders remain; every code-changing step includes exact code.
- Type consistency: helper names used in later tasks (`_finite_objective_score`, `full_selection_components`, `full_selection_score`, `consensus_cluster_support`) are defined in earlier steps.
