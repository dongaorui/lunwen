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
- Formal selection components for the new method do not include reference/oracle fields.
