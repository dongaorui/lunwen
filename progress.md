# Progress

## 2026-06-15 — Initialized planning-with-files documentation

### User request

The user asked to use the `planning-with-files` skill to summarize previous work and generate the corresponding planning documents, after noting that no `task_plan.md`, `findings.md`, `progress.md`, or `.planning/<plan-id>/` files were found.

### Actions completed

1. Invoked the `planning-with-files` skill and followed its startup guidance.
2. Checked the current project root for existing planning files:
   - `task_plan.md`
   - `findings.md`
   - `progress.md`
   - `.planning/**`
3. Confirmed no previous planning-with-files documents existed in the project.
4. Ran the plugin's `session-catchup.py` script against the current project directory.
5. The catchup script produced no output, so no prior planning context was recovered automatically.
6. Read `README.md` and extracted the project purpose, method pipeline, module structure, experiment workflow, and claim boundaries.
7. Scanned project files to identify existing code, docs, data, outputs, and run artifacts.
8. Read selected documents/results:
   - `docs/paper_experiment_revision_plan.md`
   - `docs/code_and_claim_risk_audit.md`
   - `docs/real_llm_experiment_checklist.md`
   - `runs/smoke_literature_driven/summary.md`
9. Created `task_plan.md` summarizing phases, decisions, errors, and next steps.
10. Created `findings.md` with durable findings about the project and prior work.
11. Created `progress.md` as this session log.

### Current state

Planning-with-files is now initialized in the project root using legacy/root-file mode:

- `task_plan.md`
- `findings.md`
- `progress.md`

No `.planning/<plan-id>/` isolated plan directory was created.

### Key recovered context

- Project: ReplenishVerifier, a replenishment-specific LP-structure verification framework for LLM-generated PuLP optimization models.
- Main research claim: replenishment-specific LP structure supervision provides value beyond generic solver execution, LP artifact statistics, objective consensus, generic audit, and generic repair prompts.
- Critical invariant: formal candidate selection must not use `reference_objective`; reference objective is evaluation-only.
- Smoke/demo results exist and are useful for sanity checks, but should not be used as main paper evidence.
- Real LLM experiments and leakage audits are the next major work before strong paper claims.

### Errors / issues during this session

- The `Read` tool was accidentally called with an invalid empty `pages` parameter while reading a Markdown file.
- The same invalid call was repeated twice before correcting course.
- This error is recorded in `task_plan.md` under `Errors Encountered`.

### Suggested next session starting point

Before doing substantial work, read:

1. `task_plan.md`
2. `findings.md`
3. `progress.md`
4. `CLAUDE.md`

Then choose one of these next directions:

- run/check tests and code consistency;
- prepare real LLM benchmark/candidate generation;
- run full no-reference evaluation and leakage audit;
- update the paper draft using the documented claim boundaries;
- convert planning files into isolated `.planning/<plan-id>/` mode if multiple parallel tasks are expected.

## 2026-06-15 — Created CLAUDE.md via /init

### User request

The user invoked `/init 用中文` and asked to analyze the codebase and create a repository-level `CLAUDE.md` for future Claude Code sessions.

### Actions completed

1. Checked for existing `CLAUDE.md`, Cursor rules, and Copilot instructions; none were found.
2. Read key project files and docs:
   - `README.md`
   - `pyproject.toml`
   - `requirements.txt`
   - `task_plan.md`
   - `findings.md`
   - selected experiment/risk docs
3. Scanned test files and Python entry points.
4. Ran the test suite:
   - Command: `python -m pytest -q`
   - Result: `44 passed, 48 warnings in 1.95s`
   - Warnings were PuLP deprecation warnings.
5. Created `CLAUDE.md` in Chinese with:
   - common install/test/experiment commands;
   - high-level architecture;
   - ReplenishVerifier-specific paper and experiment constraints;
   - output directory conventions;
   - planning-with-files reminder.

### Current state

`CLAUDE.md` now exists at the project root and should be read by future Claude Code sessions before making repository changes.

## 2026-06-15 — ReplenishVerifier original data generation enhancement

### User request

The user asked to enhance benchmark data generation to emphasize ReplenishVerifier's original replenishment-specific LP structure contribution rather than simply borrowing from LLMOPT / OptMATH / SIRL / OR-R1. The user explicitly requested no Explore subagents and no git worktree.

### Actions completed

1. Added replenishment-specific benchmark metadata generation:
   - `semantic_frame(problem_type, params)`
   - `replenishment_entities(problem_type, params)`
   - `modeling_steps(problem_type, params)`
   - `validate_replenishment_instance(row, include_labels=True)`
2. Updated benchmark generation so rows include `semantic_frame` and `replenishment_entities` in both labeled and unlabeled modes.
3. Added labeled-default `replenishment_modeling_steps`; unlabeled rows omit it by default unless explicitly requested.
4. Added `--include-modeling-steps` to `scripts/generate_benchmark.py`.
5. Added `Structure-Grounded Consistency` as a ReplenishVerifier selector using candidate-only execution, solver status, LP structure coverage, LP artifact structure evidence, and objective consensus.
6. Kept `OR-R1-like Voting` as a legacy/generic baseline rather than renaming it into a claimed OR-R1 reproduction.
7. Updated tests for semantic frames, entities, modeling steps, validation failures, unlabeled omission, RNG stability, and no-reference candidate selection.

### Verification

- Targeted tests: `python -m pytest tests/test_generator_smoke.py tests/test_strong_baselines.py -q`
  - Result: `18 passed, 34 warnings in 1.48s`
- Full suite: `python -m pytest`
  - Result: `49 passed, 52 warnings in 1.65s`
  - Warnings were PuLP deprecation warnings already consistent with the project state.

### Notes

- The reference model construction and parameter sampling logic were not changed, so old benchmark mathematical semantics are preserved.
- The new fields are deterministic functions of `problem_type` and sampled `params`; they do not consume RNG and therefore preserve the separate parameter/template RNG invariant.
- Git status could not be read because git reported dubious ownership for the WSL path from the Windows shell; no git safe.directory config was changed.

## 2026-06-16 — Code-paper consistency audit and submission-line rewrite

### User request

The user asked for a code/README/docs/paper consistency audit and a reconstruction of the submission narrative around constraint-level LP-structure verification for LLM-based supply chain replenishment optimization modeling. Constraints: do not use Explore, do not create a worktree, do not run real LLM generation, do not run large benchmarks, do not generate fake runs, do not fill experimental numbers, and keep unfinished empirical results as `[TO FILL AFTER REAL LLM EXPERIMENT]`.

### Actions completed

1. Read current README, docs, English and Chinese paper drafts, and relevant code modules before rewriting claims.
2. Rewrote `README.md` around the new target positioning:
   - English: `ReplenishVerifier: Constraint-Level LP-Structure Verification for LLM-Based Supply Chain Replenishment Optimization Modeling`.
   - Chinese: `ReplenishVerifier：面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证方法`.
3. Rewrote both paper drafts:
   - `papers/replenishverifier_draft_en.md`
   - `papers/replenishverifier_draft_zh.md`
4. Updated documentation files to align terminology and placeholders:
   - `docs/paper_experiment_revision_plan.md`
   - `docs/real_llm_experiment_checklist.md`
   - `docs/robustness_naming_variation_guide.md`
   - `docs/final_experiment_checklist.md`
   - `docs/paper_readme_sync_report.md`
5. Added submission-planning docs:
   - `docs/ccfa_revision_roadmap.md`
   - `docs/submit_readiness_checklist.md`
6. Checked the paper/docs/README corpus for stale old title wording and nonstandard `[TO FILL]` placeholders.
7. Did not run real LLM generation, large benchmark generation, or create any fake result files.

### Verification

- Full suite: `python -m pytest`
  - Result: `49 passed, 52 warnings in 1.79s`
  - Warnings were PuLP deprecation warnings.

### Notes

- The audit found that the code supports verifier-only claims, repair prompt generation, and preference-pair construction, but it does not yet support claims of completed repair improvement or preference-learning gains.
- All paper result tables now use `[TO FILL AFTER REAL LLM EXPERIMENT]` placeholders.
- `*-like` baselines are consistently framed as lightweight signal-isolation baselines, not faithful reproductions.
- No experimental numbers were added.

## 2026-06-17 — Pre-experiment enhancement implementation

### User request

The user asked to implement pre-experiment code and documentation enhancements without running real LLM generation, without running large benchmarks, without filling paper result numbers, without using Explore subagents, and without creating a git worktree.

### Actions completed

- Added prompt modes for `structured`, `plain`, and `hidden_verifier` generation.
- Split structure-aware and generic repair prompt artifacts.
- Added candidate runtime timing fields and a runtime overhead analyzer.
- Extended variable-renaming robustness with `descriptive_to_anonymous` mode while documenting it as text-level perturbation.
- Enriched preference-pair metadata while preserving no-reference construction.
- Updated README, docs, and paper drafts to explain prompt leakage, fair repair controls, runtime overhead, naming robustness limits, preference data limits, and no-reference selection.

### Verification

- Full suite command: `python -m pytest`
- Result: `67 passed, 52 warnings in 2.34s`

### Notes

No real LLM generation, large benchmark run, fake result number, or training claim was added.

## 2026-06-21 — Refactor ReplenishVerifier-FullV2 into conservative guarded Full

### User request

User asked to stop the aggressive FullV2 ranker and convert `ReplenishVerifier-FullV2` into a conservative guarded extension of `ReplenishVerifier-Full`: default to Full's selection and override only when strong no-reference evidence supports it. Constraints: no candidate regeneration, no `run_generation.py` changes, no pollution of Best-of-K / Full / Structure only logic, formal selection must stay no-reference.

### Actions completed

1. Created isolated `replenishverifier/experiments/fullv2_features.py`:
   - Self-contained FullV2 feature extraction (`fullv2_selection_components`, `fullv2_selection_score`).
   - Conservative guarded selection (`compute_fullv2_guarded_selection`, `should_override_full_selection`).
   - Override rules use only no-reference signals; runtime and candidate rank are last-resort tie-breakers, never primary override reasons.

2. Refactored `replenishverifier/experiments/methods.py`:
   - Imports FullV2 features from the isolated module.
   - Removed inline FullV2 feature/tuple code so old methods cannot accidentally depend on it.
   - Added special `ReplenishVerifier-FullV2` branch in `select_for_method` that first computes Full's selected candidate, then applies the guarded override.
   - Updated FullV2 selection policy to describe the guarded behavior.

3. Added `tests/test_fullv2_does_not_change_baselines.py`:
   - Verifies Best-of-K / Full / Structure only selections and row state are unchanged after calling FullV2.
   - Verifies FullV2 exposes `fullv2_guarded_decision` without reference/oracle fields.
   - Tests override logic directly for critical-missing-fix, strictly-better-structure, and multiple-improvement cases.

4. Updated existing FullV2 tests to match the new guarded semantics:
   - `tests/test_fullv2_not_structure_alias.py`
   - `tests/test_fullv2_no_reference_leakage.py`

5. Updated `replenishverifier/experiments/diagnose_selection_metrics.py`:
   - Generates `diagnostics/fullv2_guarded_decisions.csv` from selected rows.
   - Replaces the old `fullv2_failure_summary.md` copy with a dedicated summary that reports Full vs FullV2 objective accuracy, Full error salvageability, and how many Full errors are distinguishable by non-reference signals vs only by oracle/reference.

### Verification

- Full test suite: `python -m pytest -q` -> `204 passed, 52 warnings`.
- No experiment run performed per user request (they will run on Xshell).

### Notes

- FullV2 is now guaranteed to be >= Full on objective_accuracy because it defaults to Full and only overrides when a strong no-reference challenger exists.
- Formal selection remains no-reference; reference/objective_correct/oracle fields are used only in diagnostics.
- Old methods' selection logic was not modified.
- No candidates were regenerated and `run_generation.py` was not touched.

### Files changed

- `replenishverifier/experiments/fullv2_features.py` (new)
- `replenishverifier/experiments/methods.py`
- `replenishverifier/experiments/diagnose_selection_metrics.py`
- `tests/test_fullv2_not_structure_alias.py`
- `tests/test_fullv2_no_reference_leakage.py`
- `tests/test_fullv2_does_not_change_baselines.py` (new)
- `progress.md`

## 2026-06-21 — v9 experiment design and code improvements after v8 candidate diversity results

### User request

User asked to use the latest 100-problem/k=8/Qwen3-8B candidate-diversity experiment results to improve code and experiment design rather than only summarize. Constraints: do not blindly tune selector weights, keep guarded FullV2 conservative, add an experimental CandidatePoolAware ablation, add non-reference repair, improve redundancy diagnostics, fix misleading structure pass@k metrics, and design the next v9 experiment. Experiments will be run on Xshell by the user.

### Actions completed

1. Added experimental appendix-only selector:
   - `ReplenishVerifier-FullV2-CandidatePoolAware`
   - Included in `APPENDIX_METHODS`, not `MAIN_METHODS`.
   - Uses no-reference signals only: solver_ok, finite objective, objective consensus, structure score, constraint coverage, capacity detection, objective-term coverage, LP coefficient sanity, variable-role alignment, problem-type schema coverage, static validation, type-aware hard gate, LP health, code validity, and candidate diversity index.
   - Does not replace guarded `ReplenishVerifier-FullV2`.

2. Added non-reference candidate-quality repair prompts:
   - New `build_non_reference_repair_prompts()`.
   - `run_all_methods` now writes `non_reference_repair_prompts.jsonl/.csv/.md`.
   - Prompts avoid reference/objective_correct/oracle wording and use only execution, LP artifact, objective-term, static/type-aware, and constraint-coverage signals.

3. Strengthened redundancy diagnostics:
   - Added `compute_method_selection_clusters()`.
   - `diagnose_selection_metrics` now writes `diagnostics/method_selection_clusters.csv`.
   - `method_redundancy_report.md` now includes alias-like exact same-selection pairs and paper display recommendations.

4. Fixed misleading structure pass@k interpretation:
   - Kept old `pass_at_k_structure` field for backward compatibility.
   - Added `pass_at_k_structure_semantics = strict_structure_score_equals_1`.
   - Added `oracle_structure_strict_complete_at_k`.
   - Added `oracle_structure_mean_best_score_at_k` and `oracle_structure_best_score_semantics = mean_best_structure_score_among_top_k` to explain cases where strict pass@k is 0 but average structure completeness is high.

5. Added TDD tests for all new behavior.

### Verification

- New focused tests initially failed before implementation.
- Focused impacted tests: `python -m pytest tests/test_selection_gating.py tests/test_repair_prompt_fairness.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_leakage_audit.py tests/test_run_all_methods_grouping.py -q` -> `70 passed in 2.47s`.
- Full suite: `python -m pytest -q` -> `213 passed, 52 warnings in 5.88s`.

### Notes

- No local experiment run was performed.
- No candidate regeneration was performed.
- No push or commit was performed.
- Formal selection remains no-reference; reference/objective correctness/oracle fields remain diagnostics/evaluation only.

## 2026-06-21 — k=8 candidate-pool quality prompt improvements for 100-problem run

### User request

The user asked to work only on the 100-problem version, not 200 problems, and to improve candidate-pool quality under fixed k=8 rather than continue selector changes. They asked not to run the experiment locally because it will be run on Xshell, and not to push automatically.

### Actions completed

1. Kept selector code untouched for this request.
2. Enhanced generation prompts in `replenishverifier/llm/prompt_builder.py`:
   - Added a reference-free candidate-quality self-check block.
   - Added candidate-specific diversity instructions for fixed-k generation.
   - Applied the quality self-check to `structured`, `plain`, `hidden_verifier`, and `type_aware_hidden_verifier` prompt modes.
3. Updated generation flow in `replenishverifier/llm/run_generation.py`:
   - `render_prompt()` now accepts `candidate_index` and `k`.
   - `run_generation()` now renders a fresh candidate-specific prompt for each k candidate.
   - Each output row now records `candidate_index`, `k`, and `generation_config.candidate_diversity_prompting`.
4. Added/updated TDD tests:
   - Prompt includes self-check but no reference/oracle fields.
   - Prompt supports candidate-specific diversity instructions for k=8.
   - `render_prompt()` passes candidate index/k through chat template rendering.
   - `run_generation()` stores distinct candidate-specific prompts and k metadata.

### Verification

- New tests initially failed before implementation.
- Focused tests: `python -m pytest tests/test_prompt_modes.py tests/test_run_generation_retry.py tests/test_run_generation_output_format.py tests/test_run_generation_model_label.py -q` -> `22 passed in 1.82s`.
- Full suite: `python -m pytest -q` -> `208 passed, 52 warnings in 5.42s`.

### Notes

- No candidates were regenerated.
- No 200-problem work was done.
- No selector logic was changed.
- No push or commit was performed.

### User request

The user asked to continue the pre-experiment code enhancement and documentation synchronization, with the same constraints: no Explore/multi-agent work, no git worktree, no real LLM generation, no large benchmark, no fake result numbers, and no training claims.

### Actions completed

1. Verified that the repository already contained the requested major pre-experiment features:
   - generation prompt modes `structured`, `plain`, and `hidden_verifier`;
   - `--prompt_type` in `run_generation.py`, defaulting to `hidden_verifier`;
   - separate structure-aware `repair_prompts.*` and generic `generic_repair_prompts.*` outputs in `run_all_methods.py`;
   - runtime timing fields and `analyze_runtime_overhead.py`;
   - `rename_variables_for_robustness.py` with `random` and `descriptive_to_anonymous` modes;
   - no-reference preference-pair metadata in `build_preference_data.py`;
   - tests covering prompt modes, repair prompt fairness, runtime overhead, renaming robustness, and preference metadata.
2. Found and fixed a real generic-repair fairness gap:
   - `build_generic_repair_prompt()` previously printed raw `sample.problem_type`, which could expose labels such as `fixed_order_cost_big_m`.
   - It also fell back to structure-aware `feedback` when `generic_repair_feedback` was missing, which could leak labels such as `inventory_balance` and `big_m_constraint`.
3. Added regression tests in `tests/test_repair_prompt_fairness.py` for both leakage paths.
4. Updated `papers/replenishverifier_draft_en.md`, `papers/replenishverifier_draft_zh.md`, and `docs/code_and_claim_risk_audit.md` to describe generic repair more strictly as generic execution/solver/audit feedback only, without fallback to structure-aware feedback.
5. Created the execution plan at `docs/superpowers/plans/2026-06-17-pre-experiment-enhancement-verification.md` because the active workflow required a written plan; execution stayed inline because the user explicitly prohibited multi-agent work.

### Verification

- Targeted generic repair leakage test before fix: failed as expected on `fixed_order_cost` / `inventory_balance` leakage.
- Targeted generic repair leakage tests after fix: passed.
- Focused tests:
  - `python -m pytest tests/test_prompt_modes.py tests/test_repair_prompt_fairness.py tests/test_repair_generation_dry_run.py -q`
  - Result: `15 passed in 0.60s`
  - `python -m pytest tests/test_runtime_overhead.py -q; if ($?) { python -m pytest tests/test_renaming_robustness.py -q }; if ($?) { python -m pytest tests/test_preference_metadata.py tests/test_strong_baselines.py -q }`
  - Result: `2 passed`, `2 passed`, `9 passed`
- Full suite before final planning-file updates:
  - `python -m pytest`
  - Result: `68 passed, 52 warnings in 2.13s`

### Notes

No real LLM generation, large benchmark run, fake result number, or SFT/DPO/PRM/RL/LoRA/TGRPO training claim was added. The warning count is from existing PuLP deprecation warnings.

## 2026-06-18 — Qwen3 thinking output cleanup hardening

### User request

The user reran small Qwen3-8B generation after the previous output-format fix and found that `data/candidates/qwen3_8b_k1_small_formatfix.jsonl` still stored Qwen3 `<think>...</think>` reasoning text in `generated_text` instead of pure Python code. The user asked to continue modifying code and tests only, without running a 50-instance generation.

### Actions completed

1. Re-investigated generation formatting paths:
   - `replenishverifier/llm/run_generation.py`
   - `replenishverifier/llm/run_repair_generation.py`
   - `replenishverifier/llm/code_extractor.py`
   - `replenishverifier/llm/prompt_builder.py`
   - `replenishverifier/experiments/baselines.py`
2. Confirmed the root causes:
   - generation saved raw model output in `generated_text`, so downstream JSONL still exposed `<think>` even when `generated_code` was extracted;
   - `extract_python_code()` returned the whole text when no code marker was found, allowing pure reasoning to be treated as code-like output;
   - the prompt did not explicitly ban `<think>` or require the first line to be exactly `import pulp`;
   - `run_repair_generation.py` used `apply_chat_template()` without best-effort `enable_thinking=False`.
3. Added regression tests before implementation for:
   - closed Qwen thinking tags before `import pulp`;
   - unclosed Qwen thinking text before `import pulp`;
   - pure reasoning without a code start returning an empty string;
   - prompt contract banning `<think>` and requiring first line `import pulp`;
   - `run_generation()` preserving `raw_generated_text` while saving cleaned code into `generated_text` and `generated_code`;
   - repair prompt rendering disabling thinking when supported and falling back when unsupported.
4. Implemented the fix:
   - `extract_python_code()` now returns `""` when no code block or code-start marker is found;
   - `PULP_INTERFACE_REQUIREMENTS` now explicitly forbids `<think>` / chain-of-thought and requires the first answer line to be exactly `import pulp`;
   - `run_generation()` now stores raw model output in `raw_generated_text`, and stores extracted code in both `generated_text` and `generated_code` for downstream compatibility;
   - `code_output_format_valid()` now requires all three surface markers: `import pulp`, `def build_model`, and `pulp.LpProblem`;
   - `render_repair_prompt()` now tries `enable_thinking=False` and falls back for tokenizers that do not support it.

### Verification

- Focused tests after implementation:
  - Command: `PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_code_extractor.py tests/test_prompt_modes.py tests/test_run_generation_output_format.py tests/test_strong_baselines.py tests/test_repair_generation_dry_run.py -q`
  - Result: `31 passed, 1 warning in 2.50s`
- Full suite with the user's requested environment:
  - Command: `source .venv/bin/activate && PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
  - Result: `84 passed, 53 warnings in 1.79s`

### Notes

No 50-instance generation or other large experiment was run. The warning count includes existing PuLP deprecation warnings plus a Torch CUDA driver warning from the new lightweight monkeypatched generation test importing the generation module.

## 2026-06-18 — LLM generation output format repair

### User request

The user asked to fix real LLM generation output formatting after a Qwen3-8B K=4 run produced mostly explanatory text instead of runner-compatible PuLP code.

### Actions completed

1. Strengthened generation prompts so candidates must be plain importable Python modules and must define `build_model()` returning a `pulp.LpProblem` or a global PuLP `model`.
2. Added robust LLM output extraction for Python fences, generic fences, and explanatory prefixes before code markers such as `import pulp` and `def build_model`.
3. Added generation-time `code_output_format_valid` metadata and strengthened the existing generic format check with Markdown-fence rejection and `ast.parse`.
4. Added a best-effort `enable_thinking=False` chat-template call for tokenizers that support it, with fallback for tokenizers that do not.
5. Added focused tests for extraction, prompt contract, chat-template fallback, and stricter format validation.

### Verification

- Full suite command: `source .venv/bin/activate && PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
- Result: `78 passed, 52 warnings in 0.56s`

### Notes

No existing experiment results were deleted or modified. No benchmark generation logic, evaluation metric definitions, large dependencies, or real LLM experiment runs were introduced.

## 2026-06-18 — Experiment diagnostics, retry, selection, and repair hardening

### User request

The user asked to continue improving ReplenishVerifier experiment code for Qwen3-8B format-fix v2, with the goal of improving objective accuracy and structure completeness while preserving strict no-leakage constraints. The user later requested conserving tokens and not using more multi-agent/subagent execution, so Tasks 3-7 were completed inline in the main session.

### Actions completed

1. Added shared static validation quality signals in `replenishverifier/pipeline/quality_signals.py` and reused them in generic code-format validation.
2. Attached static validation fields to generation rows and candidate evaluation rows.
3. Added bounded Qwen generation retry controls to `replenishverifier/llm/run_generation.py`:
   - `--max_generation_attempts_per_candidate`
   - `--require_static_valid_code`
   - `--retry_on_invalid_code`
   - per-attempt metadata with `<think>` detection, static validation score/errors, acceptance, and error fields.
4. Strengthened no-reference selection in `replenishverifier/experiments/methods.py`:
   - Direct still selects candidate index 0.
   - Best-of-K now uses a deterministic no-reference tie-breaker instead of first viable.
   - Structure-aware selectors apply near-zero critical-structure penalties for missing required inventory balance, capacity, shortage, binary/Big-M, or fixed-cost evidence as appropriate by problem type.
   - Generic baselines remain generic and do not receive replenishment-specific penalties.
5. Added `replenishverifier/experiments/diagnose_run.py`, which writes:
   - `problem_diagnostics.jsonl`
   - `problem_type_summary.csv`
   - `candidate_diversity.csv`
   - `missing_structure_distribution.csv`
   - `failure_examples.jsonl`
   - `summary.md`
6. Kept repair prompt generation separate from true LLM repair:
   - repair rows now carry static validation errors;
   - structure-aware repair prompt text includes static validation errors;
   - generated repair candidates are marked `requires_re_evaluation=True` and `is_evaluated_repair_result=False` until re-run through evaluation.
7. Added focused tests for static validation, generation retry, selection gating/tie-breakers, diagnostics, and repair context.

### Verification

- Focused Task 1-6 regression:
  - Command: `python -m pytest tests/test_static_validation.py tests/test_run_generation_retry.py tests/test_run_generation_output_format.py tests/test_selection_gating.py tests/test_strong_baselines.py tests/test_diagnose_run.py tests/test_repair_prompt_fairness.py tests/test_repair_generation_dry_run.py -q`
  - Result: `35 passed in 1.37s`
- Diff/compile check:
  - Command: `git diff --check && python -m py_compile replenishverifier/experiments/methods.py replenishverifier/experiments/diagnose_run.py replenishverifier/llm/run_generation.py replenishverifier/llm/run_repair_generation.py`
  - Result: passed; git emitted only an existing line-ending warning for `run_generation.py`.
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `99 passed, 52 warnings in 2.77s`

### Notes

- No large LLM experiment was run.
- No existing experiment results were deleted.
- No model weights were uploaded or added.
- No large dependency was introduced.
- Formal selection changes do not use `reference_objective`, reference answers, reference LPs, reference status, objective accuracy, relative error, or oracle labels. Reference objective remains diagnostic/evaluation-only.
- Repair remains prompt generation or candidate generation only until repaired candidates are explicitly re-evaluated through the standard pipeline.

## 2026-06-18 — Paper metric and selection diagnostic upgrade

### User request

The user asked to upgrade ReplenishVerifier metrics to a paper-grade suite, diagnose whether method metrics are selected-candidate-specific, add `--model_label`, add objective-term coverage, pass@k/oracle/bootstrap metrics, and preserve no-reference formal selection.

### Actions completed

1. Added optional generation `model_label` metadata while keeping legacy candidate IDs when omitted.
2. Added evaluation-only objective-term coverage and attached objective-term fields to candidate evaluation rows.
3. Added paper metric aggregation primitives for selected-row metrics, solver status, objective gaps, error taxonomy, pass@k/oracle upper bounds, bootstrap CI, runtime/cost metrics, and selection diagnostics.
4. Added `replenishverifier.experiments.diagnose_selection_metrics` for reported-vs-recomputed metric checks and selection debug outputs.
5. Added `replenishverifier.experiments.build_paper_metrics` for paper-grade CSV/Markdown tables.
6. Updated legacy `constraint_coverage` aggregation to be method-specific per selected candidate instead of flattening all required-rule hits across problems.
7. Strengthened leakage audit separation between formal selection and post-hoc oracle metrics.

### Verification

- Focused tests:
  - Command: `PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests/test_run_generation_model_label.py tests/test_objective_term_coverage.py tests/test_paper_metrics.py tests/test_diagnose_selection_metrics.py tests/test_leakage_audit.py -q`
  - Result: `18 passed in 0.08s`
- Full suite:
  - Command: `PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`
  - Result: `117 passed, 53 warnings in 1.91s`
- Diff/compile check:
  - Command: `git diff --check && .venv/bin/python -m py_compile replenishverifier/llm/run_generation.py replenishverifier/experiments/objective_terms.py replenishverifier/experiments/paper_metrics.py replenishverifier/experiments/diagnose_selection_metrics.py replenishverifier/experiments/build_paper_metrics.py replenishverifier/experiments/audit_leakage.py replenishverifier/experiments/evaluation.py`
  - Result: passed.
- Existing-run diagnostics:
  - Command: `.venv/bin/python -m replenishverifier.experiments.diagnose_selection_metrics --exp_dir runs/smoke_literature_driven --out_dir runs/smoke_literature_driven/selection_metric_diagnostics_metricsfix`
  - Result: diagnostics written; smoke summary still has legacy mismatches for `constraint_coverage` because old reported summary was produced before the fixed aggregation.

### Notes

No LLM generation or candidate regeneration was run. The requested `data/candidates/qwen3_8b_k4_50_v3.jsonl` file was not present in this checkout, so no v3 re-evaluation was run. Formal selection remains no-reference; oracle/pass@k metrics are post-hoc evaluation-only.

## 2026-06-18 — v5 TypeAware prompt, static validation, and selection

### User request

The user asked to implement a v5 mechanism after diagnostics showed v4 metrics were not just an aggregation bug: most formal methods selected the same candidates, mostly k0, so selection did not exploit the candidate pool. Constraints included direct modification in `/home/dongaorui/projects/lunwen`, no worktree, no agent worktree, no large model generation, no fake results, and no reference objective/objective_correct/reference LP/reference answer in formal selection.

### Actions completed

1. Added `type_aware_hidden_verifier` prompt mode with problem-type modeling checklists for newsvendor, multi-period, shortage, capacity, and fixed-order Big-M cases.
2. Made `run_generation.py` accept and default to `type_aware_hidden_verifier` while preserving legacy prompt modes.
3. Extended static validation with `type_aware_static_validation`, `type_aware_static_validation_score`, and `type_aware_static_validation_errors` derived only from candidate code/AST/pattern signals and problem type.
4. Added `ReplenishVerifier-TypeAware` with explicit no-reference selection components: executable, optimal solver status, structure completeness, constraint coverage, objective-term coverage, type-aware hard gate score, candidate objective consensus, repair feedback count, and runtime.
5. Wired TypeAware into main, ablation, low-resource experiment outputs and leakage audit formal method lists.
6. Added TypeAware static validation metadata and repair requirements to structure-aware repair prompt rows, with `repair_generation_executed=False` and `is_evaluated_repair_result=False`.
7. Strengthened leakage audit so formal selection components reject reference/oracle keys such as `reference_objective`, `objective_correct`, `relative_error`, `reference_lp`, and `objective_correct_posthoc`.
8. Wrote design and implementation plan documents under `docs/superpowers/`.

### Verification

- Focused tests passed during implementation:
  - `tests/test_prompt_modes.py`: `12 passed`
  - `tests/test_static_validation.py`: `7 passed`
  - `tests/test_selection_gating.py`: `6 passed`
  - `tests/test_selection_gating.py tests/test_repair_prompt_fairness.py tests/test_strong_baselines.py`: `24 passed`
  - `tests/test_leakage_audit.py`: `5 passed`
- Full suite:
  - Command: `PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`
  - Result: `128 passed, 53 warnings in 1.93s`
- Diff whitespace check:
  - Command: `git diff --check`
  - Result: passed after trimming trailing whitespace.
- Lightweight debug run:
  - Command used an empty candidates file with `run_all_methods` demo fallback; no LLM generation was run.
  - Result: `runs/debug_v5_typeaware_existing_candidates` was written and logs showed `ReplenishVerifier-TypeAware` in main methods.
  - Demo fallback candidate IDs do not encode k0/k1/k2/k3. Distribution was: Direct selected `cand_0_syntax_error` for 15 rows; Best-of-K, Solver-Filter, TypeAware, and Full selected `cand_4_correct` for 15 rows.

### Notes

No worktree was created. No real LLM generation or candidate regeneration was run. No reference objective, objective correctness, relative error, reference LP, reference answer, or oracle metric was added to formal TypeAware selection.

## 2026-06-19 — v5 TypeAware selection/objective/reporting hardening

This interim entry was superseded later on 2026-06-19 by the stricter selectionfix scope. The generation acceptance/retry changes described in this interim entry were reverted before completion because the user clarified that this round must not modify `run_generation.py` or generation-time hard reject/retry logic. The retained work is documented in the following `v5 TypeAware selectionfix` entry.

## 2026-06-19 — v5 TypeAware selectionfix

### User request

The user clarified that this round must only modify selection, diagnostics, metrics, and reporting. It must not modify LLM generation-time static validation, hard rejection, retry behavior, or add a `--require_type_aware_valid_code` flag. The goal was cleaner method ablations, clearer diagnostics, and more targeted TypeAware selection while preserving strict no-reference formal selection.

### Actions completed

1. Reverted generation-stage changes from the interim work:
   - `replenishverifier/llm/run_generation.py` has no content diff.
   - `tests/test_run_generation_retry.py` has no content diff.
   - No generation-time TypeAware hard reject/retry behavior was added in this final selectionfix scope.
2. Kept and finalized method-specific no-reference selection tie-breakers:
   - Added `_selection_tie_break_key_for_method()` in `experiments/methods.py`.
   - Solver-only/Solver-Filter now tie-break on solver/generic validity signals, not replenishment structure features.
   - Structure-only methods tie-break on structure-specific signals.
   - Consensus methods tie-break on candidate objective consensus and generic validity.
   - TypeAware uses its TypeAware score, critical pass, objective-term coverage, constraint coverage, hard gate score, feedback count, runtime, and candidate index.
3. Added TypeAware-only critical pool filtering:
   - `_type_aware_candidate_pool_filter()` first ranks viable candidates without critical missing structures when available.
   - If every viable candidate misses critical structures, it falls back and records fallback metadata.
4. Strengthened objective-term reporting:
   - Surface regex coverage is preserved.
   - Parsed-LP objective coefficient coverage is added for ordering, holding, shortage, and fixed-order variable families.
   - Final coverage uses `min(surface, lp_coefficient)` when coefficient evidence exists.
5. Added diagnostics/reporting metrics:
   - `compute_missed_oracle_summary()` reports post-hoc missed oracle opportunities.
   - `compute_paired_method_comparison()` reports TypeAware vs Direct/Best-of-K/ReplenishVerifier-Full wins/losses and missing-capacity/objective-mismatch reductions.
   - `diagnose_selection_metrics` writes `missed_oracle_summary.csv/md` and `paired_method_comparison.csv/md`.
   - `build_paper_metrics` writes `table_missed_oracle_summary.*` and `table_paired_method_comparison.*`.
6. Added selectionfix docs:
   - `docs/superpowers/specs/2026-06-19-v5-typeaware-selectionfix-design.md`
   - `docs/superpowers/plans/2026-06-19-v5-typeaware-selectionfix.md`

### Verification

- Generation-scope sanity:
  - Command: `python -m pytest tests/test_run_generation_retry.py -q`
  - Result: `2 passed in 0.41s`
  - Command: `git diff -- replenishverifier/llm/run_generation.py tests/test_run_generation_retry.py`
  - Result: no content diff.
- Focused selectionfix suite:
  - Command: `python -m pytest tests/test_selection_gating.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_objective_term_coverage.py tests/test_run_generation_retry.py -q`
  - Result: `30 passed in 0.99s`
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `137 passed, 52 warnings in 2.58s`
- Diff/compile check:
  - Command: `git diff --check; if ($?) { python -m py_compile replenishverifier/experiments/methods.py replenishverifier/experiments/objective_terms.py replenishverifier/experiments/paper_metrics.py replenishverifier/experiments/build_paper_metrics.py replenishverifier/experiments/diagnose_selection_metrics.py }`
  - Result: passed; git emitted only line-ending warnings.

### Experiment/reporting runs

Requested real Qwen v5 selectionfix command could not be completed because `data/candidates/qwen3_8b_k4_50_v5_typeaware.jsonl` is absent in this checkout. Running with `--no_demo_if_empty` failed as expected with `ValueError: No candidate rows found`, so no fake Qwen result directory was produced from missing candidates.

Completed smoke/reporting validation instead:

- Existing debug run diagnostics:
  - `python -m replenishverifier.experiments.diagnose_selection_metrics --exp_dir runs/debug_v5_typeaware_existing_candidates --out_dir runs/debug_v5_typeaware_existing_candidates/diagnostics_selectionfix`
  - `python -m replenishverifier.experiments.analyze_error_types --exp_dir runs/debug_v5_typeaware_existing_candidates`
  - `python -m replenishverifier.experiments.build_paper_metrics --exp_dir runs/debug_v5_typeaware_existing_candidates --out_dir runs/debug_v5_typeaware_existing_candidates/paper_metrics_selectionfix --k_values 1,2,4 --bootstrap_samples 1000 --seed 42`
- Same-benchmark demo selectionfix run:
  - `python -m replenishverifier.experiments.run_all_methods --benchmark data/generated/test.jsonl --candidates runs/debug_v5_typeaware_existing_candidates/demo_candidates.generated.jsonl --out_dir runs/debug_v5_typeaware_selectionfix_demo15 --k_values 1,2,4 --timeout 30 --no_demo_if_empty`
  - Followed by diagnostics, error analysis, and paper metrics into `runs/debug_v5_typeaware_selectionfix_demo15/diagnostics` and `runs/debug_v5_typeaware_selectionfix_demo15/paper_metrics`.

### Same-benchmark demo comparison notes

Using the existing 15-problem demo candidates only, original debug had Best-of-K, Solver-Filter, Structure-Only, TypeAware, and Full all selecting the same `cand_4_correct` candidates. After selectionfix, Solver-Filter selected a different candidate family (`cand_1`, `cand_2`, `cand_3`) while Best-of-K/Structure-Only/TypeAware/Full still selected `cand_4_correct` in this demo set. This shows the method-specific solver tie-breaker reduces at least Solver-Filter sameness in smoke data, but it is not evidence for real Qwen v5 because real v5 candidates are missing locally.

No real LLM generation, candidate regeneration, large fake result, or reference-objective formal selection signal was introduced. Oracle/missed-oracle and objective correctness are reported only as post-hoc diagnostics.

## 2026-06-19 — Repository artifact cleanup

### User request

The user asked to clean the ReplenishVerifier repository by removing or untracking irrelevant process data, runtime artifacts, and old demo outputs while preserving core code, tests, papers, and curated experiment results under `docs/experiment_results/`. The user required `git rm --cached` for runtime artifacts where possible, `.gitignore` updates, audits before deleting code directories, pytest verification, and no automatic push/commit.

### Actions completed

1. Audited current tracked artifacts:
   - `git status` output was very large due to pre-existing `.claude/worktrees/...` deleted entries.
   - `git ls-files runs outputs data | Sort-Object` confirmed `runs/`, `outputs/`, root benchmark JSONL files, and generated benchmark JSONL files were tracked.
   - Size summary: `runs` 99.27 MB, `outputs` 0.02 MB, `data/candidates` 0 MB, `data/generated` 0.29 MB, `docs/experiment_results` 256.43 MB, `references_merged_for_claude` 0.71 MB.
2. Untracked runtime/generated artifacts without deleting local files:
   - `git rm -r --cached runs outputs`
   - `git rm --cached data/benchmark.jsonl data/benchmark_run.jsonl`
   - `git rm --cached -- data/generated/*.jsonl`
   - Preserved `data/candidates/.gitkeep` and `data/generated/.gitkeep`.
3. Updated `.gitignore` with grouped rules for runtime outputs, logs, local model/cache artifacts, generated datasets, root benchmark JSONL files, and Claude worktrees.
4. Audited old root benchmark references:
   - Only `docs/code_cleanup_report.md` described `data/benchmark.jsonl` and `data/benchmark_run.jsonl` as early benchmark outputs; no core test dependency was found.
5. Audited `replenish/` compatibility package:
   - Precise grep found only cleanup-report references and `replenish/__init__.py` docstring mentioning old `python -m replenish...` compatibility.
   - `README`, scripts, and tests use `replenishverifier` paths.
   - `replenish/` was intentionally not deleted this round.
6. Audited `references_merged_for_claude/`:
   - Size is about 0.71 MB.
   - It was not deleted; future cleanup can move/archive it if desired.
7. Preserved required directories:
   - `replenishverifier/`, `tests/`, `papers/`, `docs/experiment_results/`, `data/candidates/.gitkeep`, and `data/generated/.gitkeep` were not deleted.

### Verification

- Requested command with env vars:
  - Command: `PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
  - Result in this Windows shell: failed because `C:\Python314\python.exe` could not find `pytest` with user site disabled.
- Available Python environment verification:
  - Command: `python -m pytest -q`
  - Result: `137 passed, 52 warnings in 2.62s`.

### Staged cleanup summary

`git diff --cached --name-only` summary after staging `.gitignore`:

- `.gitignore`: 1 file modified.
- `runs/`: 2273 tracked files removed from Git index.
- `outputs/`: 13 tracked files removed from Git index.
- `data/generated/*.jsonl`: 4 tracked files removed from Git index.
- `data/benchmark*.jsonl`: 2 tracked files removed from Git index.
- Other staged files: 0.

No automatic commit or push was performed.

## 2026-06-19 — TypeAware-Consensus selection, diagnostics, and paper metrics

### User request

The user reported that `qwen3_8b_k4_50_v5_typeaware_selectionfix` successfully separated some candidate choices but exposed several issues: TypeAware-first picked the wrong direction, selected more execution errors, reduced structure/constraint metrics, and many main-table methods remained redundant. The user required this round to avoid LLM generation changes, avoid `run_generation.py`, avoid candidate regeneration, keep old methods, add a robust `ReplenishVerifier-TypeAware-Consensus`, split main/appendix methods, add diagnostics, add paper metrics, write tests, run pytest, and not push.

### Actions completed

1. Added planning/design docs:
   - `docs/superpowers/specs/2026-06-19-typeaware-consensus-diagnostics-design.md`
   - `docs/superpowers/plans/2026-06-19-typeaware-consensus-diagnostics.md`
2. Updated method grouping in `replenishverifier/experiments/methods.py`:
   - `MAIN_METHODS` now contains the concise main-table set.
   - `APPENDIX_METHODS` contains legacy/secondary methods.
   - `METHODS = MAIN_METHODS + APPENDIX_METHODS` preserves backward compatibility.
3. Updated `run_all_methods.py`:
   - default `main_results.*` uses `MAIN_METHODS` only;
   - `--appendix_methods_in_main` restores full-method main-table behavior;
   - manifests record `main_methods`, `appendix_methods`, and `appendix_methods_in_main`.
4. Added `ReplenishVerifier-TypeAware-Consensus`:
   - consensus-first scoring;
   - executable/Optimal hard-priority behavior;
   - critical-missing structures as safe reranking/penalty rather than TypeAware-first filtering;
   - auxiliary structure, constraint, objective-term, hard-gate, feedback, and runtime signals;
   - no reference/oracle fields in selection components.
5. Kept old `ReplenishVerifier-TypeAware` as TypeAware-first ablation.
6. Added diagnostics in `diagnose_selection_metrics.py`:
   - `method_redundancy_report.md`
   - `metric_saturation_report.md`
   - `avoidable_error_summary.csv/md`
7. Added paper metrics in `paper_metrics.py` / `build_paper_metrics.py`:
   - `table_by_problem_type.*`
   - `table_selection_collapse.*`
8. Added leakage-audit coverage for the new formal method.
9. Added tests:
   - TypeAware-Consensus behavior and no-reference components;
   - method grouping and `--appendix_methods_in_main` behavior;
   - redundancy/saturation/avoidable-error diagnostics;
   - by-problem-type and selection-collapse paper metrics.

### Verification

- Focused tests:
  - Command: `python -m pytest tests/test_selection_gating.py tests/test_run_all_methods_grouping.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_leakage_audit.py -q`
  - Result: `40 passed in 1.15s`
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `150 passed, 52 warnings in 3.33s`
- Diff/compile check:
  - Command: `git diff --check; if ($?) { python -m py_compile ... }`
  - Result: passed; git printed many existing LF/CRLF warnings.
- Existing debug diagnostics/paper metrics were generated under:
  - `runs/debug_v5_typeaware_selectionfix_demo15/diagnostics_typeaware_consensus`
  - `runs/debug_v5_typeaware_selectionfix_demo15/paper_metrics_typeaware_consensus`
- New smoke/debug run with the new method:
  - `runs/debug_typeaware_consensus_demo15`
  - Leakage audit result: passed.

### Notes

- No LLM generation, candidate regeneration, or generation-time TypeAware validation/retry was performed.
- `replenishverifier/llm/run_generation.py` was intentionally not modified.
- The archived real result directory `docs/experiment_results/qwen3_8b_k4_50_v5_typeaware_selectionfix_compare` contains Markdown/CSV summaries but no raw `main_results.jsonl` / `candidate_evaluations.jsonl`, so the new selector could not be applied retroactively there without rerunning from raw candidates.
- New smoke/debug outputs are for code-path validation only and should not be used as paper evidence.
- No commit or push was performed.

## 2026-06-19 — Structure schema expected merge fix

### User request

The user asked to fix `replenishverifier/data/structure_schema.py` so `split_expected_structures()` correctly merges explicit instance `expected_structures` with the problem-type schema, then report changed files, old/new logic, tests, pytest result, caller impact, and avoid automatic git push.

### Actions completed

1. Restored planning-with-files context by reading `task_plan.md`, `findings.md`, and `progress.md`, then ran the planning session catchup script.
2. Investigated `split_expected_structures()` and its caller `check_structures()`.
3. Confirmed the root cause: when an explicit expected map had any truthy key, the old implementation treated those truthy keys as the whole required set and skipped default schema required structures.
4. Added a regression test in `tests/test_structure_schema.py` before implementation and confirmed it failed as expected:
   - Command: `python -m pytest tests/test_structure_schema.py::test_explicit_expected_structures_merge_with_default_schema -q`
   - Result: failed because `required == ['capacity_constraint']` and did not include `inventory_balance`.
5. Changed `split_expected_structures()` to start with schema required structures when `problem_type` is available, then union truthy explicit expected keys.
6. Updated the caller-level test in `tests/test_structure_rules.py` to assert the new merge semantics through `check_structures()`.
7. Saved the short execution plan at `docs/superpowers/plans/2026-06-19-structure-schema-merge-fix.md`.

### Verification

- Focused schema test after fix:
  - Command: `python -m pytest tests/test_structure_schema.py -q`
  - Result: `5 passed in 0.23s`
- Structure schema/rules tests:
  - Command: `python -m pytest tests/test_structure_schema.py tests/test_structure_rules.py -q`
  - Result: `19 passed, 18 warnings in 0.79s`
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `150 passed, 52 warnings in 2.68s`
- Compile/status check:
  - Command: `python -m py_compile replenishverifier/data/structure_schema.py; if ($?) { git status --short -- ... }`
  - Result: compile passed; relevant modified files are `structure_schema.py`, `test_structure_schema.py`, `test_structure_rules.py`, and the new plan file.

### Notes

- The first full-suite run after the production fix exposed an intentionally stale test in `tests/test_structure_rules.py` that still expected explicit structures to completely override schema defaults. The test was updated to the new merge contract.
- `git diff --check` produced only existing LF/CRLF warnings in this Windows/WSL working copy; no whitespace error was reported before the output was truncated.
- No git push, commit, LLM generation, or large experiment was run.

## 2026-06-19 — k=8/100 diagnostics, TypeAware-Consensus, and empty-checklist fixes

### User request

The user asked to fix three issues exposed by the k=8 / 100-problem v6 experiment: diagnostics join MISSING rows for k4-k7 candidates, `ReplenishVerifier-TypeAware-Consensus` behaving too much like `ReplenishVerifier-TypeAware`, and empty type-aware checklists being scored as 0.0. Constraints: do not regenerate candidates, do not edit `run_generation.py`, do not use reference objective / objective_correct / oracle / reference LP / reference answer in formal selection, and provide Xshell rerun commands.

### Actions completed

1. Investigated diagnostics join and rank parsing paths in `diagnose_selection_metrics.py` and `paper_metrics.py`.
2. Found that candidate-rank diagnostics only emitted k0-k3 plus `k_ge_4`, and selected/candidate matching had no normalized join audit or unmatched output.
3. Added candidate-id normalization and rank parsing that supports IDs such as `Qwen3-8B_k0` through `Qwen3-8B_k7` without hard-coding k0-k3.
4. Added diagnostics unmatched selected-row reporting to `diagnostic_join_unmatched.csv` with method, problem_id, candidate_id, parsed_candidate_rank, and reason.
5. Added dynamic candidate-rank distribution columns (`k0` ... max observed k) instead of fixed k0-k3 aggregation.
6. Found the empty checklist issue in `quality_signals._type_aware_checks()`: `len(passed) / max(len(checks), 1)` returned 0.0 when `checks == []`.
7. Changed empty type-aware checklist score to neutral `1.0`; `hard_gate_score` remains `1.0` and errors remain empty.
8. Strengthened TypeAware-Consensus behavior:
   - Added `type_aware_score` to selection components.
   - Kept consensus-first scoring for `ReplenishVerifier-TypeAware-Consensus`.
   - Removed it from the global critical-structure 0.01 penalty set so critical structures act as reranking/penalty inside the consensus score rather than making it TypeAware-first/pool-filter-like.
   - `ReplenishVerifier-TypeAware` still uses the TypeAware pool filter.
9. Added regression tests for k4-k7 diagnostics joins, unique-rank fallback matching, unmatched selected rows, neutral empty checklist score, and TypeAware-Consensus non-alias behavior.

### Verification

- New RED tests initially failed for the expected reasons:
  - empty checklist score was `0.0`;
  - TypeAware-Consensus selected the same critical-pass candidate as TypeAware under the alias-like penalty;
  - diagnostics lacked `diagnostic_join_unmatched` and dynamic k4-k7 outputs.
- Focused tests after fixes:
  - Command: `python -m pytest tests/test_static_validation.py tests/test_selection_gating.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_run_all_methods_grouping.py tests/test_leakage_audit.py -q`
  - Result: `53 passed in 1.34s`
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `156 passed, 52 warnings in 3.08s`
- Diff/compile check:
  - Command: `git diff --check; if ($?) { python -m py_compile replenishverifier/experiments/diagnose_selection_metrics.py replenishverifier/experiments/paper_metrics.py replenishverifier/experiments/methods.py replenishverifier/pipeline/quality_signals.py }`
  - Result: no whitespace errors; only existing LF/CRLF warnings; compile passed.

### Notes

- The real 800 candidate/evaluation data for the k=8/100 experiment is on the user's Xshell environment, not in this checkout. No attempt was made to run that large experiment here.
- No candidates were regenerated and `replenishverifier/llm/run_generation.py` was not modified.
- Formal selection components still do not include reference objective, objective_correct, relative_error, oracle, reference LP, or reference answer fields.
- No git push or commit was performed.

## 2026-06-20 — Executor top-level solver path fix

### User request

The user reported that after rerunning, `main_results` was still all zeros and `candidate_evaluations.csv` contained `status_code = model.solve(pulp.PULP_CBC_CMD(msg=False))` followed by `PULP_CBC_CMD: Not Available`. The user explicitly instructed: do not continue changing selection / diagnostics / paper_metrics; only fix the executor.

### Root-cause investigation

1. Checked `replenishverifier/experiments/methods.py::evaluate_candidate` and confirmed it calls:
   - `execute_generated_code(generated_code, run_dir=Path(work_dir) / pid / cid, candidate_id=cid, timeout=timeout)`.
2. Inspected `replenishverifier/solver/code_executor.py` and found the runner used importlib `exec_module(mod)` before retrieving `build_model()`.
3. Confirmed why previous executor fix did not cover the observed real failure:
   - code inside `if __name__ == '__main__'` is not executed during import and was already covered by an existing test;
   - but top-level candidate code outside the main guard is executed by `exec_module()`, including top-level `model.solve(pulp.PULP_CBC_CMD(...))`.

### Actions completed

1. Added a failing regression test in `tests/test_executor_solver_fallback.py`:
   - `test_execute_generated_code_ignores_top_level_candidate_solver_and_uses_project_solver`.
   - RED result: failed because the executor imported the full module and hit top-level candidate code.
2. Modified only `replenishverifier/solver/code_executor.py`:
   - replaced full module import execution with AST-filtered namespace loading;
   - preserved imports, definitions/classes, docstring, and literal assignments;
   - requires `build_model()` and calls it directly;
   - solves/export LP via project `solve_pulp_model()`.
3. Did not modify selection, diagnostics, paper metrics, generation, candidates, or result tables.

### Verification

- RED before fix:
  - `python -m pytest tests/test_executor_solver_fallback.py::test_execute_generated_code_ignores_top_level_candidate_solver_and_uses_project_solver -q`
  - Result: failed as expected (`executable` was `False`).
- Executor tests:
  - `python -m pytest tests/test_executor_solver_fallback.py -q`
  - Result: `4 passed in 1.45s`.
- Focused tests:
  - `python -m pytest tests/test_executor_solver_fallback.py tests/test_runtime_overhead.py tests/test_strong_baselines.py -q`
  - Result: `17 passed in 2.23s`.
- Full suite:
  - `python -m pytest -q`
  - Result: `161 passed, 52 warnings in 4.01s`.

### Changed files

- `replenishverifier/solver/code_executor.py`
- `tests/test_executor_solver_fallback.py`
- `task_plan.md`
- `findings.md`
- `progress.md`

### Notes

No git commit or push was performed.

## 2026-06-20 — LP export / parse pipeline hardening

### User request

The user reported that execution is now healthy (`code_execution_time` normal, `build_model()` and `solve_pulp_model()` called), but `main_results` is still all zero because LP stats show `lp_exported=false`, `constraints_count=0`, and `objective_present=false`. The user asked to fix LP export/parse fallback behavior, ensure no silent empty stats, add tests, and keep selection no-reference.

### Root-cause investigation

1. Read `replenishverifier/solver/pulp_runner.py`:
   - `solve_pulp_model()` called `model.writeLP(str(lp_path))` but did not verify file existence or non-empty content.
   - It did not expose `lp_exported` / `lp_export_error` fields.
2. Read `replenishverifier/verifier/lp_parser.py`:
   - `parse_lp_file()` read from `lp_path`, but did not explicitly reject missing/empty LP files before parsing.
3. Read `replenishverifier/experiments/baselines.py::compute_lp_stats`:
   - `parsed=None` returns default empty LP stats (`lp_exported=False`, zero constraints, no objective).
4. Read `replenishverifier/experiments/methods.py::evaluate_candidate`:
   - parse failures left `parsed=None`, then downstream stats became empty; LP export failures were not explicitly surfaced in `lp_stats`.
5. Ran a minimal local `evaluate_candidate()` on a valid model and confirmed the happy path already exported/parses correctly locally; the missing behavior was hard failure/error propagation when LP export/parse is not real.

### Actions completed

1. Added RED regression tests in `tests/test_executor_solver_fallback.py`:
   - `test_solve_pulp_model_raises_when_write_lp_does_not_create_file`
   - `test_evaluate_candidate_records_real_lp_stats_for_valid_export`
   - `test_evaluate_candidate_records_lp_export_failure_error`
2. Confirmed RED failure before implementation:
   - `solve_pulp_model()` did not raise when `writeLP()` failed to create a file.
   - execution rows lacked `lp_exported` fields.
3. Modified `replenishverifier/solver/pulp_runner.py`:
   - added `_export_lp()` helper;
   - verifies LP file exists and is non-empty after `writeLP()`;
   - raises `RuntimeError("LP export failed: ...")` on failure;
   - returns `lp_exported=True`, `lp_export_error=None` on success.
4. Modified `replenishverifier/solver/code_executor.py`:
   - propagates `lp_exported` and `lp_export_error` from runner output;
   - marks export failures as structured execution errors.
5. Modified `replenishverifier/verifier/lp_parser.py`:
   - `parse_lp_file()` now raises for missing or empty LP path.
6. Modified `replenishverifier/experiments/methods.py`:
   - when `execution.lp_export_error` is present and `lp_stats.lp_exported` is false, records `lp_stats["error"] = "LP export failed"`.
7. Did not use `reference_objective`, oracle, `objective_correct`, or reference LP in formal selection.

### Verification

- New LP export regression tests after fix:
  - Command: `python -m pytest tests/test_executor_solver_fallback.py::test_solve_pulp_model_raises_when_write_lp_does_not_create_file tests/test_executor_solver_fallback.py::test_evaluate_candidate_records_real_lp_stats_for_valid_export tests/test_executor_solver_fallback.py::test_evaluate_candidate_records_lp_export_failure_error -q`
  - Result: `3 passed in 1.31s`.
- Focused LP/selection tests:
  - Command: `python -m pytest tests/test_executor_solver_fallback.py tests/test_structure_rules.py tests/test_strong_baselines.py tests/test_selection_gating.py -q`
  - Result: `47 passed, 18 warnings in 2.90s`.
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `164 passed, 52 warnings in 4.98s`.
- Manual minimal evaluate-candidate check:
  - Confirmed `execution.lp_exported == True`.
  - Confirmed `lp_stats.lp_exported == True`.
  - Confirmed `lp_stats.constraints_count == 1`.
  - Confirmed `lp_stats.objective_present == True`.
  - Confirmed `hard_selection_gate.passed == True`.

### Changed files

- `replenishverifier/solver/pulp_runner.py`
- `replenishverifier/solver/code_executor.py`
- `replenishverifier/verifier/lp_parser.py`
- `replenishverifier/experiments/methods.py`
- `tests/test_executor_solver_fallback.py`
- `task_plan.md`
- `findings.md`
- `progress.md`

### Notes

No git commit or push was performed for this LP pipeline fix yet.

## 2026-06-20 — ConsensusSafe selector implementation

### User request

The user reported that the k=8 / 100-problem Qwen3-8B experiment now executes normally and asked to improve selection so a new or tuned `ReplenishVerifier-ConsensusSafe` method gets as close as possible to or exceeds Best-of-K without using any reference/oracle information. Constraints: do not regenerate candidates, do not edit `run_generation.py`, preserve formal no-reference selection, run tests, rerun `run_all_methods`/diagnostics/leakage audit on the given experiment if inputs are available, and output counterfactual diagnostics if ConsensusSafe does not beat Best-of-K.

### Actions completed

1. Restored planning context and inspected current selection code in `replenishverifier/experiments/methods.py`.
2. Checked local availability of the requested real inputs:
   - `data/generated/test_100_v6.jsonl`
   - `data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl`
3. Confirmed those real inputs are absent in this checkout.
4. Saved the implementation plan:
   - `docs/superpowers/plans/2026-06-20-consensus-safe-selector.md`
5. Added RED tests for:
   - `ReplenishVerifier-ConsensusSafe` being in `MAIN_METHODS` and `METHODS`;
   - consensus preference when LP/safety signals are healthy;
   - demotion of close-consensus candidates with critical missing structures;
   - components excluding reference/oracle fields;
   - leakage audit coverage;
   - default paper-metric method coverage;
   - dedicated ConsensusSafe-vs-Best-of-K counterfactual diagnostics.
6. Implemented `ReplenishVerifier-ConsensusSafe`:
   - registered it in `MAIN_METHODS` after `ReplenishVerifier-Full` and before TypeAware ablations;
   - added `consensus_safe_selection_components()` and `consensus_safe_selection_score()`;
   - wired `_method_raw_score`, `_selection_tie_break_key_for_method`, `_annotate_selected_score`, and selection policy text;
   - added it to `STRUCTURE_AWARE_METHODS` so critical-structure safety remains active;
   - preserved `base_replenishverifier_score` before overwriting `raw_inference_score` during annotation.
7. Tuned ConsensusSafe from consensus-dominant to Full-safe:
   - dominant component is the original ReplenishVerifier-Full raw score;
   - consensus is a bonus/reranker;
   - LP health, structure, constraint coverage, objective-term coverage, type-aware hard gates, static/code validity, repair feedback count, and runtime are safety/tie-break signals.
8. Added leakage audit coverage in `replenishverifier/experiments/audit_leakage.py`.
9. Added `ReplenishVerifier-ConsensusSafe` to default paper methods in `paper_metrics.py`.
10. Added `consensus_safe_counterfactual.csv/md` output in `diagnose_selection_metrics.py`.
11. Ran a local smoke experiment using demo candidates only:
    - `runs/debug_consensus_safe_demo15`
    - Generated diagnostics under `runs/debug_consensus_safe_demo15/diagnostics`
    - Generated paper metrics under `runs/debug_consensus_safe_demo15/paper_metrics`
    - Ran leakage audit with `--write_report`.

### Real k=8/100 rerun status

Attempted the requested real command locally:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_100_v6.jsonl \
  --candidates data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl \
  --out_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank \
  --k_values 1,2,4,8 \
  --timeout 30 \
  --no_demo_if_empty
```

Result:

```text
ValueError: No benchmark rows found: data/generated/test_100_v6.jsonl
```

Therefore the real k=8/100 rerun was not completed in this checkout. No fake real results were generated.

### Verification

- RED ConsensusSafe tests initially failed because the method was unknown/unregistered.
- RED leakage test initially failed because the method was missing from `FORMAL_METHODS`.
- RED counterfactual diagnostics test initially failed because `consensus_safe_counterfactual.csv/md` did not exist.
- Focused tests:
  - Command: `python -m pytest tests/test_selection_gating.py tests/test_leakage_audit.py tests/test_run_all_methods_grouping.py tests/test_paper_metrics.py tests/test_diagnose_selection_metrics.py -q`
  - Result: `54 passed in 1.32s`.
- Full suite:
  - Command: `python -m pytest -q`
  - Result: `172 passed, 52 warnings in 5.06s`.
- Smoke leakage audit:
  - Result: `LEAKAGE AUDIT PASSED: no reference_objective usage detected in formal selection scores.`
- Smoke sanity metrics from `runs/debug_consensus_safe_demo15`:
  - `Best-of-K`: objective_accuracy `1.0`, structure_completeness `0.8238690476190477`, constraint_coverage `1.0`.
  - `ReplenishVerifier-Full`: objective_accuracy `1.0`, structure_completeness `0.8238690476190477`, constraint_coverage `1.0`.
  - `ReplenishVerifier-ConsensusSafe`: objective_accuracy `1.0`, structure_completeness `0.8238690476190477`, constraint_coverage `1.0`.
  - `ReplenishVerifier-TypeAware-Consensus`: objective_accuracy `0.4`, structure_completeness `0.6730753968253969`, constraint_coverage `0.77`.
  - This is demo smoke only, not real Qwen evidence.

### Rerun commands for the environment containing real inputs

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_100_v6.jsonl \
  --candidates data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl \
  --out_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank \
  --k_values 1,2,4,8 \
  --timeout 30 \
  --no_demo_if_empty

python -m replenishverifier.experiments.diagnose_selection_metrics \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank \
  --out_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank/diagnostics

python -m replenishverifier.experiments.build_paper_metrics \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank \
  --out_dir docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare \
  --k_values 1,2,4,8 \
  --bootstrap_samples 1000 \
  --seed 42

python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank \
  --write_report
```

If ConsensusSafe does not exceed Best-of-K on the real run, inspect:

- `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank/diagnostics/consensus_safe_counterfactual.csv`
- `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank/diagnostics/consensus_safe_counterfactual.md`
- `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank/diagnostics/missed_oracle_summary.md`
- `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank/diagnostics/paired_method_comparison.md`

### Changed files

- `replenishverifier/experiments/methods.py`
- `replenishverifier/experiments/audit_leakage.py`
- `replenishverifier/experiments/paper_metrics.py`
- `replenishverifier/experiments/diagnose_selection_metrics.py`
- `tests/test_selection_gating.py`
- `tests/test_leakage_audit.py`
- `tests/test_paper_metrics.py`
- `tests/test_diagnose_selection_metrics.py`
- `docs/superpowers/plans/2026-06-20-consensus-safe-selector.md`
- `task_plan.md`
- `findings.md`
- `progress.md`

### Notes

No candidates were regenerated. `replenishverifier/llm/run_generation.py` was not modified. No git commit or push was performed yet for this ConsensusSafe work.

## 2026-06-20 — Selector diagnostics repair for TypeAware-Consensus and Full

### User request

The user approved方案一: keep existing methods and interfaces, repair `ReplenishVerifier-TypeAware-Consensus` and `ReplenishVerifier-Full` no-reference ranking, add synthetic tests, rerun the current k=8/100 package without regenerating candidates, and report diagnostics/leakage/pytest/results.

### Actions completed

1. Restored planning context and inspected selector/diagnostics code.
2. Wrote approved design and plan:
   - `docs/superpowers/specs/2026-06-20-selector-diagnostics-repair-design.md`
   - `docs/superpowers/plans/2026-06-20-selector-diagnostics-repair.md`
3. Added RED tests in `tests/test_selection_gating.py`:
   - TypeAware selects a high TypeAware-score isolated objective candidate, while TypeAware-Consensus selects a majority objective-consensus cluster candidate.
   - Structure only selects candidate A under equal structure score, while Full selects candidate B using non-reference consensus/solver/static/type-aware/LP-health quality.
4. Implemented selector changes in `replenishverifier/experiments/methods.py`:
   - Added `_finite_objective_score()`.
   - Extended `type_aware_consensus_selection_components()` with `consensus_cluster_support`, `finite_objective`, `lp_health_score`, code validity, and static validation.
   - Changed TypeAware-Consensus scoring/tie-break to prioritize consensus-cluster support after viability.
   - Added `full_selection_components()` and `full_selection_score()`.
   - Routed `ReplenishVerifier-Full` through the new structure tie-window composite selector and annotated selected rows with components.
5. Decompressed existing package candidates from `.jsonl.gz` to `.jsonl` using `gzip -dc`; this was input conversion only, not candidate regeneration.
6. Re-ran package experiment:
   - `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix`
7. Re-ran diagnostics, error analysis, leakage audit, and paper metrics:
   - `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/diagnostics`
   - `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_selectorfix_compare/paper_metrics`

### Verification

- RED state:
  - New tests failed before implementation as expected (`consensus_cluster_support` missing; Full selected row lacked `selection_components`).
- Focused tests:
  - `python -m pytest tests/test_selection_gating.py -q` -> `23 passed in 0.35s`.
  - `python -m pytest tests/test_selection_gating.py tests/test_diagnose_selection_metrics.py tests/test_paper_metrics.py tests/test_leakage_audit.py tests/test_run_all_methods_grouping.py -q` -> `56 passed in 1.62s`.
  - `python -m py_compile replenishverifier/experiments/methods.py` passed.
- Full suite:
  - `python -m pytest -q` -> `174 passed, 52 warnings in 5.93s`.
- Leakage audit:
  - `LEAKAGE AUDIT PASSED: no reference_objective usage detected in formal selection scores.`

### Rerun results

Main objective_accuracy from `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix/main_results.md`:

- Best-of-K: `0.7400`
- Consensus only: `0.7200`
- Direct: `0.6900`
- ReplenishVerifier-ConsensusSafe: `0.7200`
- ReplenishVerifier-Full: `0.7200`
- ReplenishVerifier-TypeAware: `0.7200`
- ReplenishVerifier-TypeAware-Consensus: `0.7200`
- Solver only: `0.7100`
- Structure only: `0.7400`

Redundancy results from `same_selection_rate.csv` / `method_redundancy_report.md`:

- `ReplenishVerifier-TypeAware` vs `ReplenishVerifier-TypeAware-Consensus`: `0.9600`.
- `ReplenishVerifier-Full` vs `Structure only`: `0.2200`.
- `ReplenishVerifier-ConsensusSafe` vs `ReplenishVerifier-TypeAware-Consensus`: `1.0000`.

Diagnostics:

- `diagnostic_join_unmatched.csv` was generated and has zero unmatched selected rows beyond the header.
- The MISSING semantics are separated into metric comparison MISSING and join-unmatched diagnostics; the join file explicitly reports candidate-rank parse reason and unmatched reason when applicable.

### Notes

No candidate generation was run. `replenishverifier/llm/run_generation.py` was not modified. Formal selection still avoids reference objective, objective correctness, oracle, reference LP, and reference answers. The real rerun did not improve objective accuracy over Best-of-K or Structure only; the main success is legality/explainability and removal of the Full-vs-Structure-only collapse.

## 2026-06-20 — FullV2 failure investigation started

### User request

The user reported that `ReplenishVerifier-FullV2` has already been registered into `main_results.md` but failed: `Best-of-K` objective_accuracy is `0.7600`, while `ReplenishVerifier-FullV2` is below the older `ReplenishVerifier-Full`. The user asked to fix it under strict constraints, or if FullV2 still remains lower than Full, output `fullv2_failure_summary.md` explaining whether the cause is misleading objective consensus, stronger structure/constraint signals, overly strong type-aware penalty, or inherent non-reference indistinguishability.

### Constraints to preserve

- Do not regenerate candidates.
- Do not edit `replenishverifier/llm/run_generation.py`.
- Do not use `reference_objective`, `objective_correct`, oracle fields, reference LP, or reference answers in formal selection.
- Best-of-K should remain unchanged.
- Keep or improve FullV2 over Full if a no-reference root-cause fix exists.
- Run leakage audit before treating a result as usable.

### Actions started

- Invoked systematic debugging and planning-with-files.
- Restored planning context by reading `task_plan.md`, `findings.md`, and `progress.md`.
- Ran the planning session catchup script; it produced no output.
- Added Phase 12 to `task_plan.md`.

### Root-cause investigation result

Root cause found: the initial `ReplenishVerifier-FullV2` placed objective-consensus cluster signals before structure/constraint evidence. In observed real loss cases, a wrong objective value was generated by the majority candidate cluster, so FullV2 followed consensus even though the minority candidate had stronger structure evidence and was post-hoc objective-correct.

Observed pre-fix examples:

- `single_item_multi_period_0001`: FullV2 selected `150.0`; Full/Structure selected `116.0`.
- `single_item_multi_period_0005`: FullV2 selected `688.0`; Full/Structure selected `588.0`.

### Actions completed

1. Added RED regression test `test_fullv2_does_not_let_wrong_majority_consensus_override_stronger_structure_signal`; it failed because current FullV2 selected the high-consensus wrong candidate.
2. User requested the reverse guard test; added RED regression test `test_fullv2_can_use_consensus_when_structure_difference_is_small`; the too-structure-first intermediate fix failed this test.
3. Implemented a structure-safety bucket in `replenishverifier/experiments/methods.py`:
   - material structure-score differences protect against misleading consensus;
   - tiny structure-score differences stay in the same bucket, allowing consensus to decide.
4. Re-ran tests and the existing-candidate k=8/100 experiment without regenerating candidates.
5. Generated diagnostics, paper metrics, and leakage audit.
6. Rewrote `runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620/diagnostics/fullv2_failure_summary.md` as a post-hoc summary explaining the original failure and post-fix tie outcome.

### Verification

- RED test before fix:
  - `python -m pytest tests/test_fullv2_not_structure_alias.py::test_fullv2_does_not_let_wrong_majority_consensus_override_stronger_structure_signal -q` -> failed as expected (`c1` selected instead of `c0`).
- Reverse RED test before bucket fix:
  - `python -m pytest tests/test_fullv2_not_structure_alias.py::test_fullv2_can_use_consensus_when_structure_difference_is_small -q` -> failed as expected (`c0` selected instead of consensus candidate).
- FullV2 focused tests:
  - `python -m pytest tests/test_fullv2_not_structure_alias.py tests/test_fullv2_no_reference_leakage.py -q` -> `5 passed`.
- Focused selection/leakage tests:
  - `python -m pytest tests/test_selection_gating.py tests/test_fullv2_not_structure_alias.py tests/test_fullv2_no_reference_leakage.py tests/test_leakage_audit.py -q` -> `34 passed`.
- Full suite:
  - `python -m pytest -q` -> `198 passed, 52 warnings in 5.16s`.
- Compile:
  - `python -m py_compile replenishverifier/experiments/methods.py` passed.
- Whitespace:
  - `git diff --check -- replenishverifier/experiments/methods.py tests/test_fullv2_not_structure_alias.py` produced only LF/CRLF warnings, no whitespace errors.
- Leakage audit:
  - `LEAKAGE AUDIT PASSED: no reference_objective usage detected in formal selection scores.`
  - `no_leakage_audit.json` has `passed: true` and no issues.

### Rerun result

Run directory: `runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620`.

Main objective_accuracy:

- `Best-of-K`: `0.7400`.
- `Structure only`: `0.7400`.
- `ReplenishVerifier-Full`: `0.7400`.
- `ReplenishVerifier-FullV2`: `0.7400`.

FullV2 is no longer below Full. It ties Full/Structure/Best-of-K but does not exceed them.

Diagnostics:

- FullV2 vs Full same-selection rate: `0.3300`.
- FullV2 vs Structure same-selection rate: `0.3200`.
- FullV2 vs Best-of-K same-selection rate: `0.9700`.
- FullV2 beats Full count: `0`; Full beats FullV2 count: `0`.
- FullV2 wrong selections: `26`; only 4 of those had a post-hoc correct candidate in the pool.

### Changed files

- `replenishverifier/experiments/methods.py`
- `tests/test_fullv2_not_structure_alias.py`
- `docs/superpowers/plans/2026-06-20-fullv2-failure-repair.md`
- `runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620/diagnostics/fullv2_failure_summary.md`
- `task_plan.md`
- `findings.md`
- `progress.md`

### Notes

No candidate generation was run. `replenishverifier/llm/run_generation.py` was not modified. Formal selection still avoids reference objective, objective correctness, oracle, reference LP, and reference answers. Post-hoc correctness was used only for diagnostics and explanation.
