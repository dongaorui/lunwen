# TypeAware-Consensus Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add concise main/appendix method grouping, a no-reference `ReplenishVerifier-TypeAware-Consensus` selector, diagnostics reports, paper metrics tables, and tests.

**Architecture:** Keep selection logic in `replenishverifier/experiments/methods.py`, experiment orchestration in `run_all_methods.py`, post-hoc diagnostics in `diagnose_selection_metrics.py`, and reusable aggregations in `paper_metrics.py`. The new selector is consensus-first with TypeAware-safe reranking and must not read oracle/reference evaluation fields.

**Tech Stack:** Python 3.10+, pytest, existing JSONL/CSV/Markdown utilities, PuLP-based candidate evaluation pipeline.

## Global Constraints

- Do not modify LLM generation.
- Do not modify `replenishverifier/llm/run_generation.py`.
- Do not regenerate candidates.
- Do not add generation-time TypeAware validation or retry.
- Formal selection must not use `reference_objective`, `objective_correct`, reference LP, reference answer, `relative_error`, pass@k, or oracle metrics.
- Reference/oracle fields may be used only for post-hoc evaluation, oracle/pass@k, diagnostics, error analysis, and paper metrics.
- Do not delete old methods; preserve backward compatibility.
- Add tests for new behavior.
- Run pytest before final report.
- Do not automatically git push.

---

## Files

- Modify: `replenishverifier/experiments/methods.py` — method grouping constants, TypeAware-Consensus score/components, selection policy, method dispatch.
- Modify: `replenishverifier/experiments/run_all_methods.py` — default main methods vs optional all-method main table, manifest metadata.
- Modify: `replenishverifier/experiments/diagnose_selection_metrics.py` — write redundancy, saturation, avoidable-error reports.
- Modify: `replenishverifier/experiments/paper_metrics.py` — by-problem-type and selection-collapse aggregations.
- Modify: `replenishverifier/experiments/build_paper_metrics.py` — emit new paper tables.
- Modify: `replenishverifier/experiments/audit_leakage.py` — include new formal method.
- Modify: `tests/test_selection_gating.py` — selector and no-reference component tests.
- Modify: `tests/test_diagnose_selection_metrics.py` — diagnostics report tests.
- Modify: `tests/test_paper_metrics.py` — new table tests.
- Create/modify: `docs/superpowers/specs/2026-06-19-typeaware-consensus-diagnostics-design.md` and this plan.
- Modify: `task_plan.md`, `findings.md`, `progress.md` after implementation with final facts.

## Task 1: Method grouping and TypeAware-Consensus selector

**Interfaces:**
- Produces `MAIN_METHODS: list[str]`, `APPENDIX_METHODS: list[str]`, `METHODS: list[str]`.
- Produces `type_aware_consensus_selection_components(row: dict) -> dict`.
- Produces `type_aware_consensus_selection_score(row: dict) -> float`.

**Steps:**
- [ ] Add failing tests in `tests/test_selection_gating.py` for method grouping and TypeAware-Consensus behavior.
- [ ] Run targeted tests and confirm failures mention missing `MAIN_METHODS` / unknown method / wrong selection.
- [ ] Implement constants, components, score, dispatch, selected metadata, and policy.
- [ ] Run targeted tests and confirm pass.

## Task 2: Main vs appendix orchestration

**Interfaces:**
- `run_experiments(..., appendix_methods_in_main: bool = False)` uses `MAIN_METHODS` by default and `METHODS` when true.
- CLI flag: `--appendix_methods_in_main`.

**Steps:**
- [ ] Add tests or targeted assertions for method lists.
- [ ] Update `run_all_methods.py` imports and selection loop.
- [ ] Add new method to ablation and low-resource lists.
- [ ] Include `main_methods`, `appendix_methods`, `appendix_methods_in_main` in manifest.

## Task 3: Diagnostics reports

**Interfaces:**
- `build_method_redundancy_report(recomputed_metrics, same_selection_rate, threshold=0.95) -> str`.
- `build_metric_saturation_report(recomputed_metrics, same_selection_rate, low_unique_threshold=2) -> str`.
- `compute_avoidable_error_summary(main_rows, candidate_rows, methods=None) -> list[dict]`.
- `write_diagnostic_reports(...)` integrated into `diagnose_selection_metrics()`.

**Steps:**
- [ ] Add failing diagnostics tests for high-overlap pair, exact metric duplicate grouping, metric saturation, and avoidable error counts.
- [ ] Implement helper functions without using oracle fields outside diagnostics.
- [ ] Write `method_redundancy_report.md`, `metric_saturation_report.md`, `avoidable_error_summary.csv`, `avoidable_error_summary.md`.
- [ ] Run targeted diagnostics tests.

## Task 4: Paper metrics tables

**Interfaces:**
- `compute_metrics_by_problem_type(rows, methods=None) -> list[dict]`.
- `compute_selection_collapse_summary(main_rows, candidate_rows=None, threshold=0.95) -> list[dict]`.
- `build_paper_metrics()` writes `table_by_problem_type.*` and `table_selection_collapse.*`.

**Steps:**
- [ ] Add failing paper metric tests for new tables and TypeAware-Consensus rows.
- [ ] Implement aggregation functions.
- [ ] Wire new tables in `build_paper_metrics.py`.
- [ ] Run targeted paper metric tests.

## Task 5: Leakage audit and docs/progress

**Interfaces:**
- `audit_leakage.FORMAL_METHODS` includes `ReplenishVerifier-TypeAware-Consensus`.

**Steps:**
- [ ] Add/adjust test if needed for formal methods.
- [ ] Update audit list.
- [ ] Update `task_plan.md`, `findings.md`, `progress.md` with concise Chinese entries.
- [ ] Run focused tests and full pytest.
- [ ] Run diagnostics/paper metrics on available existing v5 run if present; otherwise report absent.
- [ ] Run leakage audit on available target run if present.
- [ ] Run git status.

## Self-Review

- Spec coverage: method grouping, new selector, diagnostics, paper metrics, audit inclusion, tests, and final checklist all have tasks.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: function names used by tests and implementation are defined in the plan.
