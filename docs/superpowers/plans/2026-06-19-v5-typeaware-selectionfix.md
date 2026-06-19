# v5 TypeAware Selectionfix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make TypeAware v5 selection ablations cleaner and diagnostics/reporting more informative without changing generation-time validation or retry.

**Architecture:** Keep the existing experiment pipeline and add focused helpers in `methods.py`, `paper_metrics.py`, `diagnose_selection_metrics.py`, and `build_paper_metrics.py`. Use tests to prove no-reference selection behavior and post-hoc-only diagnostics.

**Tech Stack:** Python 3.10+, pytest, existing ReplenishVerifier experiment JSONL/CSV/Markdown utilities.

## Global Constraints

- Do not modify `replenishverifier/llm/run_generation.py` generation acceptance/retry logic in this round.
- Formal selection must not use `reference_objective`, `objective_correct`, reference LPs, reference answers, relative error, oracle metrics, or pass@k metrics.
- Keep existing method names and outputs backward compatible.
- New functionality requires tests and full pytest must pass.

---

### Task 1: Revert generation-stage changes

**Files:**
- Verify clean: `replenishverifier/llm/run_generation.py`
- Verify clean: `tests/test_run_generation_retry.py`

**Interfaces:**
- Produces: no content diff in generation acceptance/retry code or tests.

- [x] Remove type-aware generation acceptance/retry changes from `run_generation.py`.
- [x] Remove generation retry tests that assert type-aware hard rejection.
- [x] Run `python -m pytest tests/test_run_generation_retry.py -q` and confirm pass.
- [x] Confirm `git diff -- replenishverifier/llm/run_generation.py tests/test_run_generation_retry.py` is empty.

### Task 2: Method-specific selection tie-breakers

**Files:**
- Modify: `replenishverifier/experiments/methods.py`
- Test: `tests/test_selection_gating.py`

**Interfaces:**
- Produces: `_selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=False)`.
- Produces: `_type_aware_candidate_pool_filter(rows, allow_feasible_selection=False)`.

- [x] Add tests proving Solver-Filter tie-break ignores structure advantage.
- [x] Add tests proving Structure-Only tie-break ignores consensus advantage.
- [x] Add tests proving TypeAware critical pool prefers capacity-complete candidate.
- [x] Add tests proving TypeAware fallback metadata when all viable candidates miss critical structures.
- [x] Implement method-specific tie-breakers and TypeAware-only pool filter.
- [x] Run `python -m pytest tests/test_selection_gating.py -q` and confirm pass.

### Task 3: Objective-term and reporting metrics

**Files:**
- Modify: `replenishverifier/experiments/objective_terms.py`
- Modify: `replenishverifier/experiments/paper_metrics.py`
- Modify: `replenishverifier/experiments/build_paper_metrics.py`
- Test: `tests/test_objective_term_coverage.py`
- Test: `tests/test_paper_metrics.py`

**Interfaces:**
- Produces: `objective_term_surface_coverage`, `objective_term_lp_coefficient_coverage`, and final `objective_term_coverage`.
- Produces: paper metric count denominators and objective-term split tables.

- [x] Add tests for surface coverage without LP coefficient evidence.
- [x] Add tests for fixed-order Big-M missing binary objective coefficient.
- [x] Add paper-metric tests for count denominators and objective-term split columns.
- [x] Implement parsed-objective coefficient coverage and reporting columns.
- [x] Run `python -m pytest tests/test_objective_term_coverage.py tests/test_paper_metrics.py -q` and confirm pass.

### Task 4: Selection diagnostics

**Files:**
- Modify: `replenishverifier/experiments/paper_metrics.py`
- Modify: `replenishverifier/experiments/diagnose_selection_metrics.py`
- Modify: `replenishverifier/experiments/build_paper_metrics.py`
- Test: `tests/test_diagnose_selection_metrics.py`

**Interfaces:**
- Produces: `compute_missed_oracle_summary(main_rows, candidate_rows)`.
- Produces: `compute_paired_method_comparison(rows, target_method="ReplenishVerifier-TypeAware", baseline_methods=None)`.
- Diagnostics write `missed_oracle_summary.csv/md` and `paired_method_comparison.csv/md`.

- [x] Add tests for missed-oracle counting.
- [x] Add tests for paired TypeAware-vs-baseline wins/losses and error reductions.
- [x] Add tests that diagnostics write the new output files.
- [x] Implement the metrics and wire them into diagnostics and paper metrics.
- [x] Run `python -m pytest tests/test_diagnose_selection_metrics.py -q` and confirm pass.

### Task 5: Verification and experiment/report run

**Files:**
- Modify: `progress.md`

**Interfaces:**
- Produces: verified code and a truthful comparison report.

- [x] Run focused tests for selectionfix scope.
- [x] Run full `python -m pytest -q`.
- [x] Run requested real v5 command with `--no_demo_if_empty` to verify input availability; report missing candidates instead of producing fake Qwen results.
- [x] Run diagnostics/paper metrics on existing debug v5 artifacts.
- [x] Run same-benchmark demo selectionfix comparison using existing demo candidates for smoke validation.
- [x] Run `git diff --check` and `py_compile` on changed modules.
