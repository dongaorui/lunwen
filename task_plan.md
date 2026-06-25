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

### Phase 8 — Conservative guarded FullV2 refactor

**Status:** complete on 2026-06-21

Actions:

- Created isolated `replenishverifier/experiments/fullv2_features.py` for FullV2 feature extraction and guarded selection.
- Reimplemented `ReplenishVerifier-FullV2` as a conservative wrapper around `ReplenishVerifier-Full`: default to Full's choice, override only on strong no-reference evidence.
- Removed inline FullV2 tuple/feature code from `replenishverifier/experiments/methods.py` to prevent leakage into other selectors.
- Added `tests/test_fullv2_does_not_change_baselines.py` to verify baseline isolation and no in-place row mutation.
- Updated existing FullV2 tests to reflect the new guarded semantics.
- Updated diagnostics to generate `fullv2_guarded_decisions.csv` and a proper `fullv2_failure_summary.md` analyzing salvageable Full errors.

Verification:

- Full suite: `python -m pytest -q` -> `204 passed, 52 warnings in 5.08s`.
- No real LLM experiment run performed in this checkout; user will run on Xshell.

Notes:

- FullV2 objective_accuracy is now guaranteed to be at least Full's objective_accuracy.
- Formal selection remains no-reference; reference/objective_correct/oracle are only used in diagnostics.
- No candidates regenerated; `run_generation.py` untouched.
- No push or commit performed.

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

### Phase 13 — Non-reference repair policy wrapper

**Status:** complete on 2026-06-21

Actions:

- Added `replenishverifier/llm/nonreference_repair_policy.py` as a wrapper/filtering layer around the existing `run_repair_generation()` engine.
- Added `replenishverifier/llm/run_nonreference_repair_policy.py` CLI shim.
- Preserved `run_repair_generation.py` core logic; no repair engine reimplementation.
- The wrapper builds repair prompt rows only from non-reference candidate-quality signals, strips reference/oracle/evaluation fields, calls the existing repair engine, and merges repaired code back into original candidate slots.
- Clean candidates remain unchanged; repaired candidates preserve original `problem_id`, `candidate_id`, `candidate_index`, and `k` alignment and are marked `requires_re_evaluation=True`.
- Added/used `tests/test_nonreference_repair_policy.py` covering no reference leakage, clean candidates untouched, failed candidates repaired, output length preservation, id alignment preservation, and deterministic behavior with a mocked engine.

Verification:

- RED: `python -m pytest tests/test_nonreference_repair_policy.py -q` failed with missing module before implementation.
- Target tests: `python -m pytest tests/test_nonreference_repair_policy.py -q` -> `4 passed in 0.53s`.
- Focused repair suite: `python -m pytest tests/test_nonreference_repair_policy.py tests/test_repair_generation_dry_run.py tests/test_repair_prompt_fairness.py -q` -> `18 passed in 0.92s`.
- Full suite: `python -m pytest -q` -> `217 passed, 52 warnings in 5.22s`.
- Static grep: no literal `objective_correct` in `replenishverifier/llm/nonreference_repair_policy.py`.

Notes:

- No candidates were regenerated.
- `replenishverifier/llm/run_generation.py` and `replenishverifier/llm/run_repair_generation.py` were not modified.
- Real repaired candidates still require re-evaluation before any repair-performance claim.

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

### Phase 9 — LP export and parse failure hardening

**Status:** complete on 2026-06-20

Actions:

- Investigated the LP export/parse path after execution became healthy but `lp_stats` still appeared empty in the user's experiment.
- Confirmed `solve_pulp_model()` previously called `model.writeLP()` but did not verify that the LP file was actually created and non-empty.
- Added RED regression tests for:
  - `solve_pulp_model()` raising when `writeLP()` does not create a file;
  - `evaluate_candidate()` producing real LP stats for a valid exported LP;
  - `evaluate_candidate()` recording explicit LP export failure errors instead of silently returning only empty stats.
- Hardened `solve_pulp_model()` so LP export failures raise `RuntimeError("LP export failed: ...")` and successful exports include `lp_exported=True` / `lp_export_error=None`.
- Propagated LP export status through `execute_generated_code()` and `evaluate_candidate()`.
- Hardened `parse_lp_file()` to raise if the LP path does not exist or is empty.
- Kept selection no-reference: no `reference_objective`, oracle, or `objective_correct` signal was added to formal selection.

Verification:

- New RED tests initially failed with missing `lp_exported` fields and no raise on missing LP file.
- New LP export tests after fix: `3 passed in 1.31s`.
- Focused LP/selection tests: `python -m pytest tests/test_executor_solver_fallback.py tests/test_structure_rules.py tests/test_strong_baselines.py tests/test_selection_gating.py -q` -> `47 passed, 18 warnings in 2.90s`.
- Full suite: `python -m pytest -q` -> `164 passed, 52 warnings in 4.98s`.
- Manual minimal `evaluate_candidate()` check confirmed `lp_exported=True`, `lp_stats.constraints_count=1`, `objective_present=True`, and `hard_selection_gate.passed=True`.

Notes:

- The valid-model local path already exported correctly; the fix addresses missing hard assertions/error propagation so failed LP export/parse cannot silently masquerade as an empty LP artifact.
- No candidate generation, selection oracle, or paper-metric logic was introduced.

### Phase 10 — ConsensusSafe no-reference selector

**Status:** complete on 2026-06-20

Actions:

- Added `ReplenishVerifier-ConsensusSafe` as a main-table method after `ReplenishVerifier-Full` and before TypeAware ablations.
- Designed it as a Full-safe consensus reranker: it starts from executable + Optimal candidates, preserves the ReplenishVerifier-Full raw score as the dominant base signal, then adds candidate objective consensus, LP artifact health, constraint/objective-term/type-aware safety, and static/code validity signals.
- Kept formal selection no-reference: selector components do not include `reference_objective`, `objective_correct`, `relative_error`, oracle fields, reference LP, or reference answers.
- Added leakage-audit coverage for `ReplenishVerifier-ConsensusSafe`.
- Added `consensus_safe_counterfactual.csv/md` diagnostics comparing ConsensusSafe vs Best-of-K choices using post-hoc objective labels only for explanation, never for selection.
- Added paper-metrics default coverage so by-problem-type/collapse tables include ConsensusSafe.
- Saved the implementation plan at `docs/superpowers/plans/2026-06-20-consensus-safe-selector.md`.

Verification:

- RED tests first failed because the method was unregistered and missing from leakage audit.
- Focused selector/leakage/paper/diagnostic tests: `python -m pytest tests/test_selection_gating.py tests/test_leakage_audit.py tests/test_run_all_methods_grouping.py tests/test_paper_metrics.py tests/test_diagnose_selection_metrics.py -q` -> `54 passed in 1.32s`.
- Full suite: `python -m pytest -q` -> `172 passed, 52 warnings in 5.06s`.
- Smoke run: `runs/debug_consensus_safe_demo15` generated with demo candidates; main methods include `ReplenishVerifier-ConsensusSafe`.
- Smoke leakage audit passed: `LEAKAGE AUDIT PASSED: no reference_objective usage detected in formal selection scores.`
- Smoke sanity metrics showed `ReplenishVerifier-ConsensusSafe` tied `ReplenishVerifier-Full` and `Best-of-K` on the demo run; this remains smoke validation only.

Notes:

- The requested real inputs `data/generated/test_100_v6.jsonl` and `data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl` are not present in this checkout, so the real k=8/100 rerun could not be completed locally.
- Running the exact requested command failed honestly with `ValueError: No benchmark rows found: data/generated/test_100_v6.jsonl`; no fake result was generated.
- No candidates were regenerated and `replenishverifier/llm/run_generation.py` was not modified.
- To rerun on the Xshell environment that contains the files, use the commands recorded in `progress.md`.

### Phase 11 — Selector diagnostics repair for TypeAware-Consensus and Full

**Status:** complete on 2026-06-20

Actions:

- Saved the approved design at `docs/superpowers/specs/2026-06-20-selector-diagnostics-repair-design.md`.
- Saved the implementation plan at `docs/superpowers/plans/2026-06-20-selector-diagnostics-repair.md`.
- Added RED synthetic selector tests proving:
  - `ReplenishVerifier-TypeAware` can choose a high TypeAware-score isolated-objective candidate while `ReplenishVerifier-TypeAware-Consensus` chooses a majority objective-consensus cluster candidate.
  - `Structure only` can choose the first candidate under a structure tie while `ReplenishVerifier-Full` chooses a different candidate using non-reference quality signals.
- Reworked `ReplenishVerifier-TypeAware-Consensus` to expose and rank by no-reference consensus-cluster support with finite objective, LP health, structure/coverage, type-aware/static validation, and critical-missing penalties.
- Reworked `ReplenishVerifier-Full` to use a structure tie-window plus candidate objective consensus, solver/finite-objective, LP health, constraint coverage, objective-term coverage, type-aware/static validation, and critical-structure safety.
- Did not modify `replenishverifier/llm/run_generation.py`.
- Did not regenerate candidates; decompressed the existing package `.jsonl.gz` candidates only to run evaluation.
- Re-ran the package experiment into `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix`.
- Rebuilt diagnostics, error analysis, leakage audit, and paper metrics.

Verification:

- New RED tests failed before implementation, then passed after implementation.
- `python -m pytest tests/test_selection_gating.py -q` -> `23 passed in 0.35s`.
- Focused selector/diagnostic/leakage suite -> `56 passed in 1.62s`.
- Full suite: `python -m pytest -q` -> `174 passed, 52 warnings in 5.93s`.
- `python -m py_compile replenishverifier/experiments/methods.py` passed.
- Leakage audit on `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix` passed.

Real rerun summary:

- `Best-of-K` objective_accuracy: `0.7400`.
- `Structure only` objective_accuracy: `0.7400`.
- `ReplenishVerifier-Full` objective_accuracy: `0.7200`.
- `ReplenishVerifier-TypeAware` objective_accuracy: `0.7200`.
- `ReplenishVerifier-TypeAware-Consensus` objective_accuracy: `0.7200`.
- `ReplenishVerifier-Full` vs `Structure only` same_selection_rate: `0.2200`.
- `ReplenishVerifier-TypeAware` vs `ReplenishVerifier-TypeAware-Consensus` same_selection_rate: `0.9600`.

Notes:

- The repair successfully prevents `Full` from degenerating into `Structure only` by construction.
- `TypeAware-Consensus` is no longer identical to `TypeAware`, but remains highly overlapping on the real run.
- `TypeAware-Consensus` and `ConsensusSafe` are identical on this run (`same_selection_rate=1.0000`), which should be reported as a remaining redundancy if discussed.
- `diagnostic_join_unmatched.csv` was generated and contains no unmatched selected rows.
- Formal selector components remain no-reference; post-hoc correctness appears only in diagnostics/evaluation.

### Phase 12 — FullV2 failure investigation and outcome

**Status:** complete on 2026-06-20

Goal:

- Investigate why the newly registered `ReplenishVerifier-FullV2` underperforms the existing `ReplenishVerifier-Full` in the current registered results.
- Follow systematic debugging: reproduce/read the result, trace selector logic and diagnostics, identify root cause before any fix.
- Preserve constraints: no candidate regeneration, no `run_generation.py` edits, no reference/objective-correct/oracle/reference-LP/reference-answer in formal selection, and run leakage audit before using the result.
- If `FullV2` remains below `Full`, produce `fullv2_failure_summary.md` explaining whether the failure is objective-consensus misleading, structure/constraint stronger, type-aware penalty too strong, or non-reference signals cannot distinguish.

Planned actions:

1. Locate the current `FullV2` result directory and registered `main_results.md`.
2. Inspect `Full`, `FullV2`, `Best-of-K`, and diagnostics/counterfactual outputs.
3. Trace `ReplenishVerifier-FullV2` implementation and formal selection components.
4. Add/adjust tests only after root cause is identified.
5. Implement a minimal no-reference fix if evidence supports one; otherwise write `fullv2_failure_summary.md`.
6. Run focused tests, full pytest where feasible, rerun diagnostics/paper metrics/leakage audit on the existing candidates/results.

Result:

- Root cause: FullV2 put objective-consensus cluster features before structure/constraint evidence, so a wrong majority objective cluster could override a structurally stronger minority candidate.
- Added two directional tests:
  - structure can override misleading majority consensus when the structure difference is material;
  - consensus can still decide when the structure difference is very small, avoiding collapse into Structure-only.
- Implemented a no-reference structure-safety bucket in `replenishverifier/experiments/methods.py`.
- Re-ran the existing-candidate k=8/100 experiment into `runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620` without regenerating candidates.
- Result: `ReplenishVerifier-FullV2` objective_accuracy improved from the failing `0.7200` to `0.7400`, tying `ReplenishVerifier-Full`, `Structure only`, and `Best-of-K` on the rerun.
- Leakage audit passed; `no_leakage_audit.json` reports `passed: true` and no issues.
- `fullv2_failure_summary.md` was updated as a post-hoc diagnostic summary of the original failure and post-fix tie outcome.

Verification:

- `python -m pytest tests/test_fullv2_not_structure_alias.py tests/test_fullv2_no_reference_leakage.py -q` -> `5 passed`.
- `python -m pytest tests/test_selection_gating.py tests/test_fullv2_not_structure_alias.py tests/test_fullv2_no_reference_leakage.py tests/test_leakage_audit.py -q` -> `34 passed`.
- `python -m pytest -q` -> `198 passed, 52 warnings in 5.16s`.
- `python -m py_compile replenishverifier/experiments/methods.py` passed.
- `git diff --check -- replenishverifier/experiments/methods.py tests/test_fullv2_not_structure_alias.py` produced only LF/CRLF warnings.

Errors encountered in this phase:

- Initial `Read` call again passed invalid `pages: ""` for a Markdown file; future Markdown reads must omit `pages` or use the environment-specific non-empty workaround only if required.
- First attempted structure-first FullV2 fix passed the misleading-consensus test but failed the user's requested reverse test; replaced it with a structure-safety bucket so consensus still applies when structure differences are tiny.

### Phase 14 — TypeAware-Consensus safe consensus hardening

**Status:** complete on 2026-06-24

Goal:

- Keep the formal method name `ReplenishVerifier-TypeAware-Consensus`, but change its internal logic from raw objective-consensus preference to verifier-guided safe consensus.
- Add diagnostics for wrong consensus, objective-term coverage, text-triggered gates, by-problem-type analysis, and hard subset / stress-test behavior.
- Preserve existing methods, avoid new main method names, and keep formal selection no-reference.

Actions:

- Updated `ReplenishVerifier-TypeAware-Consensus` selection components to include candidate-quality-discounted `safe_consensus_score`, `wrong_consensus_risk`, LP coefficient sanity, text-triggered hard-gate score/failures, and critical-missing safety.
- Reweighted TypeAware-Consensus so raw objective-cluster support is no longer dominant when the cluster is unsafe: structure/constraint coverage, objective-term coverage, LP health, type-aware/static validation, and text-triggered failures can demote a majority cluster.
- Added text-triggered gate logic for capacity, shortage, fixed-order cost, binary order, and Big-M cues; it is scoped by problem type so non-capacity problems are not penalized for lacking capacity constraints.
- Preserved `Consensus only` as raw consensus and did not remove or rename any existing method.
- Added hard-subset / stress-test metrics and diagnostics over capacity, shortage, and fixed-order Big-M problem families.
- Extended by-problem-type metrics with safe-consensus and wrong-consensus risk summaries.
- Kept post-hoc correctness fields in diagnostics only; selection components still exclude reference objective, objective correctness, oracle fields, reference LP, and reference answers.

Verification:

- RED checks first failed for missing diagnostics/helpers before implementation (`compute_hard_subset_stress_diagnostics`, `compute_hard_subset_metrics`).
- Focused safe-consensus tests: `python -m pytest tests/test_selection_gating.py::test_type_aware_consensus_demotes_large_cluster_missing_objective_terms tests/test_selection_gating.py::test_type_aware_consensus_text_triggered_capacity_gate_only_when_text_mentions_capacity tests/test_safe_consensus_diagnostics.py::test_compute_hard_subset_stress_diagnostics_groups_risky_types tests/test_paper_metrics.py::test_compute_hard_subset_metrics_summarizes_capacity_shortage_fixed_cases -q` -> `4 passed`.
- Focused selector/diagnostic/leakage suite: `python -m pytest tests/test_selection_gating.py tests/test_safe_consensus_diagnostics.py tests/test_paper_metrics.py tests/test_diagnose_selection_metrics.py tests/test_method_dispatch_independence.py tests/test_leakage_audit.py -q` -> `73 passed`.
- Full suite: `python -m pytest -q` -> `225 passed, 52 warnings`.
- Compile/diff check: `git diff --check; python -m py_compile replenishverifier/experiments/methods.py replenishverifier/experiments/paper_metrics.py replenishverifier/experiments/diagnose_selection_metrics.py replenishverifier/experiments/build_paper_metrics.py` passed except for existing LF/CRLF warnings.

Notes:

- No candidates were regenerated.
- `replenishverifier/llm/run_generation.py` was not modified.
- No real k=8 experiment rerun was performed in this checkout.
- `run_full_consensus_safe_experiment.sh` had a pre-existing mode-only working-tree change and remains shown as modified; this task did not intentionally edit its content.

### Phase 15 — Per-problem-type safe TAC profiles

**Status:** complete on 2026-06-25

Goal:

- Keep the public method name `ReplenishVerifier-TypeAware-Consensus` unchanged while upgrading the internal selector from one global safe-consensus key to per-problem-type safe TAC profiles.
- Focus on hard problem types: `multi_item_capacity`, `fixed_order_cost_big_m`, `single_item_multi_period_shortage`, and `single_period_newsvendor`.
- Preserve baselines and no-reference formal selection.

Actions:

- Read current safe TAC v2 results under `docs/experiment_results/qwen3_8b_k8_100_v8_candidate_diversity_safe_tac_v2_20260625_083905_compare`.
- Confirmed current TAC v2 objective accuracy was `0.8400`, with by-type TAC: fixed Big-M `0.9500`, capacity `0.6000`, ordinary multi-period `1.0000`, shortage `0.9500`, newsvendor `0.7000`.
- Confirmed post-hoc oracle@8 by problem type from candidate rows: capacity `0.6000`, newsvendor `0.7000`, fixed Big-M `1.0000`, shortage `1.0000`, ordinary multi-period `1.0000`.
- Added/verified explicit `select_typeaware_consensus(problem_candidates, problem)` dispatch path using problem-type profiles.
- Added common no-reference TAC features in `selection_components`: `candidate_id`, `candidate_rank`, `problem_type`, `solver_ok`, `execution_success`, `finite_objective`, and `objective`.
- Adjusted the fixed-order Big-M TAC profile to use stable schema/objective/Big-M-safe evidence before raw consensus when all safety evidence ties, avoiding the observed wrong majority objective cluster on `fixed_order_cost_big_m_0008`.
- Added problem-type pool-limit diagnostics that report `oracle_at_k`, selector accuracy, selector gap, and whether a problem type is candidate-pool-limited.
- Reselected existing safe_tac_v2 candidate evaluations into `runs/debug_safe_tac_v2_per_type_reselect` without re-executing or regenerating candidates.
- Generated diagnostics and paper metrics for the reselect run.

Verification:

- New RED tests failed first for missing common TAC component fields and fixed-order tie behavior, then passed after implementation.
- Focused tests: `python -m pytest tests/test_selection_gating.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_leakage_audit.py -q` -> `71 passed in 3.08s`.
- Reselect result: `ReplenishVerifier-TypeAware-Consensus` improved from `0.8400` to `0.8500` objective_accuracy on the existing safe_tac_v2 candidate evaluations.
- By-type reselect TAC: fixed Big-M `1.0000`, capacity `0.6000`, ordinary multi-period `1.0000`, shortage `0.9500`, newsvendor `0.7000`.
- Leakage audit on `runs/debug_safe_tac_v2_per_type_reselect` passed.
- Full suite: `python -m pytest -q` -> `234 passed, 52 warnings in 10.33s`.

Notes:

- `multi_item_capacity` is candidate-pool-limited in the inspected run because oracle@8 is only `0.6000`; TAC reaches `0.6000`, so further gains require better candidate generation/repair rather than selector tuning alone.
- `single_period_newsvendor` is also pool-limited at oracle@8 `0.7000`; TAC remains at this ceiling.
- `fixed_order_cost_big_m` had selector headroom because oracle@8 was `1.0000` while TAC was `0.9500`; the per-type profile fixes the observed gap in the inspected run.
- `single_item_multi_period` stays saturated at `1.0000`, so ordinary multi-period was not harmed.
- `single_item_multi_period_shortage` keeps `0.9500`; remaining gap is not fixed by the no-reference signals inspected here.
- No `run_generation.py` changes and no candidate regeneration were performed.
