# Task Plan

## Goal

Use `planning-with-files` to initialize persistent planning documents for the current `lunwen` / ReplenishVerifier project and summarize the work that has already been done so future sessions can resume without losing context.

## Current Project Summary

The project is **ReplenishVerifier: LP-Structure-Grounded Verification for LLM-Based Replenishment Optimization Modeling**. Its intended contribution is a replenishment-specific LP-structure supervision layer for LLM-generated PuLP optimization models, focused on inventory replenishment rather than a general LLM-for-OR framework.

The repository already contains code and outputs for:

- benchmark/problem generation and reference LP export;
- PuLP candidate execution and LP artifact generation;
- LP parsing and replenishment-structure verification;
- candidate scoring and no-reference selection policies;
- lightweight `*-like` baselines inspired by OR-R1, SIRL, OptArgus, and OptiRepair;
- smoke/demo experiment runs;
- paper-oriented tables, case studies, error analysis, leakage audits, and revision documents.

## Key Principle to Preserve

Formal candidate selection must **not** use `reference_objective`. Reference objectives are only for final evaluation metrics such as objective accuracy and relative error.

This principle is repeated in `README.md`, `docs/paper_experiment_revision_plan.md`, `docs/code_and_claim_risk_audit.md`, and `docs/real_llm_experiment_checklist.md`.

## Phases

### Phase 1 — Restore existing planning context

**Status:** complete

Actions:

- Checked whether `task_plan.md`, `findings.md`, `progress.md`, or `.planning/` already existed in the project root.
- Confirmed that no planning-with-files artifacts existed before this initialization.
- Ran the planning-with-files `session-catchup.py` script against the current project directory.
- The catchup script produced no output, so no previous planning context was automatically recoverable.

### Phase 2 — Summarize existing project work

**Status:** complete

Actions:

- Read `README.md` to capture the project scope, method pipeline, module layout, experiment workflow, and claim boundaries.
- Scanned project files to identify code, docs, benchmark data, outputs, and experiment result directories.
- Read selected documents and result summaries:
  - `docs/paper_experiment_revision_plan.md`
  - `docs/code_and_claim_risk_audit.md`
  - `docs/real_llm_experiment_checklist.md`
  - `runs/smoke_literature_driven/summary.md`

Summary:

- The project has progressed beyond a skeleton: it includes verifier code, solver/executor code, baseline/evaluation code, LLM generation/repair support, smoke runs, and paper-facing documentation.
- Several risk audits and revision docs already exist and should guide future work.
- Current smoke results are useful for sanity checking but should not be treated as main paper evidence.
- The next major milestone is real LLM candidate generation/evaluation, leakage audit, case study extraction, and paper table construction.

### Phase 3 — Create planning-with-files documents

**Status:** complete

Actions:

- Created `task_plan.md`.
- Created `findings.md`.
- Created `progress.md`.

### Phase 4 — Recommended next work

**Status:** pending

Recommended next steps:

1. Confirm code and docs are aligned with the current repository state.
2. Run or re-run tests if a test suite is available.
3. Generate a real 50-instance benchmark split if not already finalized.
4. Generate K=4 real LLM candidates using the intended local or Hugging Face model.
5. Run all no-reference selection methods.
6. Run leakage audit and only use results if the audit passes.
7. Analyze errors and extract case studies from real LLM outputs.
8. Build paper tables from real LLM runs.
9. Run actual second-round repair candidates before making any repair-performance claim.

## Decisions

| Decision | Rationale |
|---|---|
| Use project-root planning files rather than `.planning/<plan-id>/` | User asked to generate documentation now; only one active planning thread is being initialized. |
| Treat existing smoke/demo outputs as sanity-check evidence only | README and docs explicitly warn synthetic/demo outputs are not valid main-paper claims. |
| Keep `reference_objective` out of formal selection | This is the central no-leakage principle of the project. |
| Describe baselines as lightweight `*-like` signal-isolation baselines | Docs warn against claiming full reproductions of SIRL, OptArgus, OptiRepair, OR-R1, or StepORLM. |
| Add replenishment-specific semantic benchmark metadata without changing reference models | `semantic_frame`, `replenishment_entities`, and labeled `replenishment_modeling_steps` make the data support ReplenishVerifier's original LP-structure-grounded claim while preserving sampled parameters and objective semantics. |
| Keep OR-R1-like Voting as a generic legacy baseline and add a separate structure-grounded selector | Avoids claiming a full OR-R1 reproduction while making ReplenishVerifier's own selection signal explicit and no-reference. |
| Treat generic repair as a strict fair control | Generic LLM repair prompts must use only generic execution/solver/audit feedback, must not expose missing replenishment labels, and must not fall back to structure-aware feedback. |

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| `Read` tool rejected `pages: ""` while reading `README.md` | 1 | Recognized that `pages` should only be used for PDFs. |
| Repeated same invalid `pages: ""` argument | 2 | Stopped using empty page values. |
| Repeated same invalid `pages: ""` argument again | 3 | Used a non-empty page parameter to get the read to succeed in this environment; future reads of markdown should omit `pages` entirely. |
| Git commands failed with dubious ownership on the WSL UNC path | 2 | Did not change global git safe.directory configuration; proceeded with file-aware tools and pytest verification. |

## Files Created by This Initialization

- `task_plan.md` — phase plan, decisions, errors, next work.
- `findings.md` — durable findings from README/docs/results inspection.
- `progress.md` — session log of this initialization.

## Open Questions for User

- Which model should be used for the first real LLM experiment: local Qwen path, Hugging Face `Qwen/Qwen3-8B`, or another model?
- Should future planning use root files (`task_plan.md`, `findings.md`, `progress.md`) or isolated `.planning/<plan-id>/` directories?
- Should the next session prioritize real experiments, paper writing, code cleanup/tests, or claim-risk audit?

### Phase 5 — TypeAware-Consensus and selection diagnostics

**Status:** complete on 2026-06-19

Actions:

- Kept LLM generation untouched: no `run_generation.py` change, no candidate regeneration, no generation-time TypeAware validation/retry.
- Split default main methods from appendix methods while preserving all legacy methods through `METHODS` and `--appendix_methods_in_main`.
- Added `ReplenishVerifier-TypeAware-Consensus` as a consensus-first, TypeAware-safe no-reference selector.
- Kept old `ReplenishVerifier-TypeAware` as TypeAware-first ablation.
- Added diagnostic reports for method redundancy, metric saturation, and post-hoc avoidable errors.
- Added paper metrics tables for problem-type breakdown and selection-collapse diagnostics.
- Added tests for method grouping, selector behavior, diagnostics, paper metrics, and leakage-audit method coverage.

Verification:

- Focused tests: `40 passed in 1.15s`.
- Full suite: `150 passed, 52 warnings in 3.33s`.
- Existing debug smoke rerun with new method: `runs/debug_typeaware_consensus_demo15`.
- Leakage audit on the new debug smoke run passed.

Notes:

- `docs/experiment_results/qwen3_8b_k4_50_v5_typeaware_selectionfix_compare` contains archived Markdown/CSV diagnostics but no `main_results.jsonl` / `candidate_evaluations.jsonl`, so it could not be directly reprocessed with the new code in-place.
- New diagnostics were generated on `runs/debug_v5_typeaware_selectionfix_demo15` and on the new debug smoke run for code-path validation only; these remain smoke/debug outputs, not paper evidence.

### Phase 6 — Structure schema expected merge fix

**Status:** complete on 2026-06-19

Actions:

- Investigated `split_expected_structures()` in `replenishverifier/data/structure_schema.py` and its `check_structures()` caller.
- Confirmed the old logic used truthy explicit `expected_structures` as a full replacement required set whenever any truthy key existed.
- Added a failing regression test for partial explicit expected maps merging with default schema required structures.
- Fixed `split_expected_structures()` so schema required structures are the base when `problem_type` is known, then truthy explicit expected keys are unioned into required.
- Updated caller-level structure-rules regression test to assert the new merge contract.
- Saved execution plan at `docs/superpowers/plans/2026-06-19-structure-schema-merge-fix.md`.

Verification:

- RED test before fix: `python -m pytest tests/test_structure_schema.py::test_explicit_expected_structures_merge_with_default_schema -q` failed as expected because only `capacity_constraint` was required.
- Focused tests: `python -m pytest tests/test_structure_schema.py tests/test_structure_rules.py -q` -> `19 passed, 18 warnings in 0.79s`.
- Full suite: `python -m pytest -q` -> `150 passed, 52 warnings in 2.68s`.
- `python -m py_compile replenishverifier/data/structure_schema.py` passed.

Notes:

- No caller code change was required; `check_structures()` automatically uses the corrected merge behavior.
- One caller-level test expectation was updated because it encoded the obsolete full-override behavior.
- No git push or commit was performed.

### Phase 7 — k=8/100 diagnostics and TypeAware fixes

**Status:** complete on 2026-06-19

Actions:

- Investigated diagnostics candidate-id parsing and selected/candidate join logic for k=8 IDs such as `Qwen3-8B_k4` through `Qwen3-8B_k7`.
- Added normalized candidate-id/rank parsing and dynamic candidate-rank distribution columns.
- Added `diagnostic_join_unmatched.csv` output for unmatched selected rows, including method, problem_id, candidate_id, parsed_candidate_rank, and reason.
- Fixed empty type-aware checklist scoring so no-applicable-checklist cases are neutral (`score=1.0`) rather than penalized (`score=0.0`).
- Made `ReplenishVerifier-TypeAware-Consensus` less alias-like by keeping it consensus-first and removing it from the global TypeAware-first critical-structure multiplier; critical missing structures remain in its own score/tie-breaker.
- Added tests for k4-k7 diagnostics matching, unique parsed-rank matching, unmatched selected rows, empty checklist neutrality, and TypeAware-Consensus non-alias behavior.

Verification:

- New regression tests initially failed as expected before implementation.
- Focused tests: `python -m pytest tests/test_static_validation.py tests/test_selection_gating.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_run_all_methods_grouping.py tests/test_leakage_audit.py -q` -> `53 passed in 1.34s`.
- Full suite: `python -m pytest -q` -> `156 passed, 52 warnings in 3.08s`.
- `git diff --check` produced only existing LF/CRLF warnings; changed modules compiled successfully.

Notes:

- The user's real k=8/100 data is on Xshell, not in this checkout; no large experiment was run here.
- No candidates were regenerated.
- `replenishverifier/llm/run_generation.py` was not modified.
- Formal selection remains no-reference: no `reference_objective`, `objective_correct`, oracle, reference LP, or reference answer is used in selection components.
- No push or commit was performed.
- Formal selection components for the new method do not include reference/oracle fields.

### Phase 8 — Executor top-level solver bypass fix

**Status:** complete on 2026-06-20

Actions:

- Checked `replenishverifier/experiments/methods.py::evaluate_candidate` and confirmed it calls `execute_generated_code()` from `replenishverifier.solver.code_executor`.
- Investigated `code_executor.py` and found the runner imported candidate code with `spec.loader.exec_module(mod)`, which executes top-level candidate code before calling `build_model()`.
- Added a failing regression test showing a candidate with top-level `model = build_model(); model.solve(pulp.PULP_CBC_CMD(...))` / top-level runtime code should still be evaluated through the project solver path.
- Fixed only the executor path: the runner now parses candidate source with `ast`, loads imports, definitions, docstring, and literal assignments needed by `build_model()`, then calls `build_model()` and `solve_pulp_model()` itself.
- Did not modify selection, diagnostics, paper metrics, LLM generation, candidates, or experiment result logic.

Verification:

- RED before fix: `python -m pytest tests/test_executor_solver_fallback.py::test_execute_generated_code_ignores_top_level_candidate_solver_and_uses_project_solver -q` failed because execution imported the full candidate module and hit top-level candidate code.
- Executor tests: `python -m pytest tests/test_executor_solver_fallback.py -q` -> `4 passed in 1.45s`.
- Focused tests: `python -m pytest tests/test_executor_solver_fallback.py tests/test_runtime_overhead.py tests/test_strong_baselines.py -q` -> `17 passed in 2.23s`.
- Full suite: `python -m pytest -q` -> `161 passed, 52 warnings in 4.01s`.

Notes:

- The old main-block test already proved `if __name__ == '__main__'` was not executed; the newly fixed gap was top-level solver/export code outside a main guard.
- `evaluate_candidate` still calls `execute_generated_code`; the fix is intentionally centralized in the executor.
