# Findings

## 2026-06-15 — Initial planning-with-files summary

### Source files inspected

- `README.md`
- `docs/paper_experiment_revision_plan.md`
- `docs/code_and_claim_risk_audit.md`
- `docs/real_llm_experiment_checklist.md`
- `runs/smoke_literature_driven/summary.md`
- Project file listing across `replenishverifier/`, `scripts/`, `data/`, `outputs/`, `runs/`, and `docs/`

### Project identity

The project is **ReplenishVerifier**, a Python research-code framework for the paper idea:

> ReplenishVerifier: LP-Structure-Grounded Verification for LLM-Based Replenishment Optimization Modeling

Chinese title in README:

> ReplenishVerifier：面向库存补货优化的大语言模型 LP 结构验证增强方法

The project focuses on **inventory replenishment optimization** and checks LP structures extracted from LLM-generated PuLP code.

### Claimed contribution boundary

The intended contribution is not a general optimization-modeling agent, not a complete hallucination detector, not a full repair system, and not a reproduction of SIRL / OptArgus / OptiRepair / OR-R1 / StepORLM.

The contribution to defend is:

> replenishment-specific LP structure supervision extracted from the model induced by generated solver code.

The paper should show this signal provides value beyond generic solver feedback, LP artifact statistics, objective consensus, generic hallucination audit, and generic repair prompts.

### No-reference selection rule

A central invariant appears across the repository docs:

- Formal candidate selection must not use `reference_objective`.
- `reference_objective` is allowed only after selection for evaluation metrics such as objective accuracy and relative error.
- Leakage audit should be run after experiments before results are used in the paper.

Allowed selection signals include executable status, solver optimality, objective presence, candidate objective consensus, generic LP artifact statistics, generic audit issues, and replenishment-specific expected structure labels for ReplenishVerifier variants.

Forbidden selection signals include objective distance to reference objective or selecting the candidate closest to reference objective.

### Existing pipeline from README

The method pipeline is documented as:

1. LLM generates PuLP candidates.
2. `solver/code_executor.py` executes candidate code and records solver status/objective.
3. Candidate model exports a `.lp` file.
4. `verifier/lp_parser.py` parses variables, constraints, objective, binaries, and bounds.
5. `verifier/lp_graph.py` builds weak LP-structure evidence.
6. `verifier/structure_rules.py` emits structure certificates and structure scores.
7. `experiments/run_all_methods.py` selects candidates with no-reference policies.
8. `experiments/build_preference_data.py` can build chosen/rejected pairs for future DPO/PRM work.

### Key modules noted in README/docs

- `replenishverifier/data/structure_schema.py` — central expected-structure schema.
- `replenishverifier/verifier/lp_parser.py` — lightweight PuLP LP parser.
- `replenishverifier/verifier/lp_graph.py` — weak LP graph evidence detectors.
- `replenishverifier/verifier/structure_rules.py` — structure detection and certificates.
- `replenishverifier/verifier/feedback.py` — natural-language structure feedback.
- `replenishverifier/experiments/audit_leakage.py` — no-reference selection audit.
- `replenishverifier/experiments/build_preference_data.py` — preference-pair construction.
- `replenishverifier/llm/code_extractor.py` — LLM code extraction.
- `replenishverifier/llm/run_generation.py` — candidate generation.
- `replenishverifier/llm/run_repair_generation.py` — second-round repair generation path.

### Problem types

Supported benchmark problem types in README:

- `single_period_newsvendor`
- `single_item_multi_period`
- `single_item_multi_period_shortage`
- `multi_item_capacity`
- `fixed_order_cost_big_m`

### Baselines and methods

Current method list documented in README includes:

- `Direct`
- `Best-of-K`
- `Solver-Filter`
- `OR-R1-like Voting`
- `SIRL-like LP-Stats`
- `OptArgus-like Audit`
- `OptiRepair-like Repair-Prompt`
- `Structure-Only`
- `ReplenishVerifier-Full`
- `ReplenishVerifier-Repair`

Important claim boundary:

- `*-like` baselines are lightweight signal-isolation baselines, not full reproductions.
- `ReplenishVerifier-Repair` should only be called real repair if repaired candidates are generated and evaluated; otherwise it is repair prompt generation.

### Risk audit findings already recorded in repo

`docs/code_and_claim_risk_audit.md` reports:

- No leakage found in current scoring code regarding `reference_objective` for selection.
- `Solver-Filter` uses executable, optimal status, and objective presence only.
- `ReplenishVerifier-Full` formula is documented as no-reference: `0.25 executable + 0.25 optimal + 0.35 structure + 0.15 semantic`.
- OR-R1-like Voting baseline was added using candidate-observable consensus/code/LP-validity signals.
- OptiRepair-like generic feedback intentionally avoids inventory-specific concepts such as inventory balance, Big-M, fixed cost, and shortage.
- LP structure role aliases were added for descriptive variable names, but the parser/rules remain heuristic.

Remaining limitations from the audit:

1. `*-like` baselines are not faithful reproductions.
2. Repair is prompt-generation unless repaired candidates are actually generated and evaluated.
3. Structure detection is heuristic and does not prove exact coefficients/indexing/boundary conditions.
4. Synthetic demo candidates are smoke tests only.
5. Objective consensus can still converge on shared wrong objectives.

### Paper experiment plan findings

`docs/paper_experiment_revision_plan.md` recommends the main table include:

1. `Direct`
2. `Best-of-K`
3. `Solver-Filter`
4. `OR-R1-like Voting`
5. `SIRL-like LP-Stats`
6. `OptArgus-like Audit`
7. `ReplenishVerifier-Full`

`ReplenishVerifier-Repair` should be main-table only if real second-round repair is run.

Appendix/secondary candidates include:

- `Structure-Only`
- `OptiRepair-like Repair-Prompt`
- `ReplenishVerifier-Full + objective consensus`
- synthetic/demo smoke results

### Real LLM experiment checklist findings

`docs/real_llm_experiment_checklist.md` gives the expected workflow:

1. Generate benchmark split, e.g. 50 instances with seed 42.
2. Generate K real LLM candidates, e.g. Qwen3-8B with K=4.
3. Run all selection methods via `replenishverifier.experiments.run_all_methods`.
4. Analyze error types, extract case studies, build paper tables, run leakage audit.
5. Generate and evaluate second-round repair candidates only if making repair claims.

The checklist says to report model name/path/version, hardware, K, generation parameters, prompt template, whether expected structures are visible to the generator, code extraction strategy, timeout, solver backend, leakage audit result, and limitations.

### Smoke result observed

`runs/smoke_literature_driven/summary.md` contains a 15-row/method summary table over 15 evaluations. Observed highlights:

- `ReplenishVerifier-Full`, `ReplenishVerifier-Repair`, and `Structure-Only` show structure completeness of `1.0000` and constraint coverage of `1.0000` in that smoke run.
- `SIRL-like LP-Stats` has objective accuracy `0.8667` and structure completeness `0.9410` in that smoke run.
- `OptArgus-like Audit` and `OptiRepair-like Repair-Prompt` show objective accuracy `0.8000` and structure completeness `0.9314`.
- `Direct` is all zeros in this smoke summary.
- README/docs warn these smoke/synthetic outputs are sanity checks only and should not become main paper claims.

### Existing artifacts found by project scan

The repository contains, among other files:

- benchmark data such as `data/benchmark.jsonl`, `data/benchmark_run.jsonl`, `data/generated/test.jsonl`;
- LP outputs under `outputs/reference_lp/` and `outputs/run_reference_lp/`;
- structure check outputs such as `outputs/structure_check.jsonl` and `outputs/structure_check_run.jsonl`;
- multiple experiment result directories under `runs/`, including `exp_demo`, `smoke`, `smoke_no_leakage`, `smoke_strong_baselines`, `smoke_literature_driven`, and paper-table directories;
- docs including literature audit, code/claim risk audit, paper experiment revision plan, real LLM experiment checklist, README sync report.

### Practical next-step finding

The repository appears ready for a real LLM candidate run workflow, but paper claims should wait for:

- real LLM candidates rather than synthetic/demo candidates;
- successful no-reference leakage audit;
- case studies from real LLM outputs;
- actual second-round repair generation/evaluation if repair improvements are claimed.

## 2026-06-15 — Data generation now carries replenishment-specific semantic metadata

Benchmark rows generated after this enhancement include deterministic, replenishment-specific `semantic_frame` and `replenishment_entities` fields. Labeled rows also include `replenishment_modeling_steps` by default for LP-structure-grounded process supervision, while unlabeled rows omit those steps by default to avoid leaking the modeling process.

Important invariants preserved:

- Parameter sampling and language-template selection remain driven by separate RNG objects.
- The new semantic fields are derived from already-sampled `params` and `problem_type`, so they do not change parameter sequences or reference objectives.
- `include_labels=False` still omits `expected_structures`, `reference_code`, and `reference_objective`.
- Formal candidate selection continues to mark no reference-objective usage; the new `Structure-Grounded Consistency` selector uses candidate-only execution, solver status, LP structure coverage, LP artifact structure evidence, and objective consensus.

Risk note: `semantic_frame.required_structures` intentionally exposes required/optional schema metadata because the user requested problem-type-aware structural framing; if a future experiment needs fully prompt-only unlabeled data, decide whether to strip this field or use a separate export mode.

## 2026-06-16 — Code-paper consistency audit findings

The current repository can honestly support the following submission-line claims:

- ReplenishVerifier is a constraint-level LP-structure verification prototype for LLM-generated supply-chain replenishment optimization models.
- It verifies LP artifacts induced by PuLP code and checks problem-type-aware replenishment structures.
- It supports rule-level certificates, missing-structure feedback, repair prompt generation, and verifier-guided preference-pair construction.
- Formal selection is designed to be no-reference-objective; `reference_objective` is evaluation-only.
- `OR-R1-like`, `SIRL-like`, `OptArgus-like`, and `OptiRepair-like` are lightweight signal-isolation baselines, not faithful reproductions.

The repository does not yet support these claims without future experiments:

- Any quantitative improvement over baselines on real LLM outputs.
- Actual effectiveness of second-round repair.
- DPO/PRM/reranker/RL gains from preference data.
- Robustness under naming perturbations on real candidates.
- CCF-A-level empirical strength.

All result-bearing paper sections should remain `[TO FILL AFTER REAL LLM EXPERIMENT]` until real LLM generation, evaluation, leakage audit, and case-study extraction are complete.

## 2026-06-17 — Generic repair prompt fairness tightened

The repository already had most requested pre-experiment enhancement features when re-checked: prompt modes, split repair prompts, runtime overhead analyzer, renaming robustness utility, preference metadata, docs, and tests.

A remaining fairness issue was found in the LLM repair prompt builder:

- `build_generic_repair_prompt()` printed raw `sample.problem_type`, which can reveal replenishment-specific labels such as `fixed_order_cost_big_m`.
- When `generic_repair_feedback` was absent, it fell back to structure-aware `feedback`, which can reveal labels such as `inventory_balance` or `big_m_constraint`.

This was fixed by making the generic repair prompt use a neutral problem category and by allowing only `generic_repair_feedback` or a generic fallback message. Structure-aware repair prompts still intentionally preserve replenishment-specific feedback.

The fair-control interpretation is now stricter:

- `generic` repair = generic execution / solver / LP-artifact audit feedback only;
- `structure_aware` repair = may use missing required structures, certificates, repair hints, and labels such as inventory balance, Big-M, fixed order cost, capacity, shortage, or binary order variables.

No reference objective is used for repair prompt construction or preference construction; `reference_objective` remains evaluation-only.

## 2026-06-19 — TypeAware-Consensus selection and diagnostics

The project now separates concise main methods from appendix methods while preserving legacy compatibility:

- Default `main_results.*` uses `MAIN_METHODS`: `Direct`, `Best-of-K`, `Solver only`, `Structure only`, `Consensus only`, `ReplenishVerifier-Full`, `ReplenishVerifier-TypeAware`, and `ReplenishVerifier-TypeAware-Consensus`.
- `METHODS` still contains all legacy/appendix methods, and `run_all_methods --appendix_methods_in_main` restores the old full-method main table behavior.

`ReplenishVerifier-TypeAware-Consensus` is the new formal TypeAware direction:

- executable + Optimal remain hard-priority signals;
- objective consensus is the dominant ranking signal;
- critical TypeAware missing structures are safe reranking/penalty signals rather than a TypeAware-first pool filter;
- structure completeness, constraint coverage, objective-term coverage, hard gate score, feedback count, and runtime are auxiliary;
- selection components exclude `reference_objective`, `objective_correct`, `relative_error`, reference LP, and oracle fields.

The old `ReplenishVerifier-TypeAware` remains available as a TypeAware-first ablation so the paper can explain why structure-gate-first selection is less stable.

New diagnostics are explicitly separated from formal selection:

- `method_redundancy_report.md` is diagnostic-only and reports high same-selection-rate pairs, metric-identical groups, objective-accuracy duplicate groups, and recommended display families.
- `metric_saturation_report.md` is diagnostic-only and reports low-unique-value metrics plus high-overlap method pairs.
- `avoidable_error_summary.md` is post-hoc-only and counts avoidable objective mismatch, missing capacity, non-optimal solver status, and execution errors for TypeAware, TypeAware-Consensus, and Consensus only.

New paper metric helpers add `table_by_problem_type.*` and `table_selection_collapse.*`. These can explain which problem types improve and why methods collapse to the same selected candidates.

Verification completed with `python -m pytest -q`: `150 passed, 52 warnings in 3.33s`. The warning count is existing PuLP deprecation warnings. No LLM generation code or candidate generation path was modified.

## 2026-06-21 — ReplenishVerifier-FullV2 is now a conservative guarded extension of ReplenishVerifier-Full

### Architecture change

`ReplenishVerifier-FullV2` no longer acts as an independent aggressive ranker. It now:

1. Computes the candidate that `ReplenishVerifier-Full` would select.
2. Looks for a "challenger" candidate that is executable, solver-optimal, has a finite objective, and has no critical missing replenishment structures.
3. Overrides Full's choice only if the challenger is strictly better on structure (with no regression on constraint/objective-term coverage), or if structure is equal and the challenger improves on at least two other no-reference safety signals.

This guarantees `FullV2 objective_accuracy >= Full objective_accuracy` on every run and prevents runtime/candidate-rank from destabilizing the Full base.

### Isolation

- FullV2 feature extraction and selection logic live in `replenishverifier/experiments/fullv2_features.py`.
- `Best-of-K`, `ReplenishVerifier-Full`, `Structure only`, and other baselines are untouched.
- A dedicated regression test (`tests/test_fullv2_does_not_change_baselines.py`) verifies that calling FullV2 does not change baseline outputs or mutate candidate rows in place.

### Diagnostics

- `diagnostics/fullv2_guarded_decisions.csv` records every FullV2 override decision.
- `diagnostics/fullv2_failure_summary.md` reports:
  - Full vs FullV2 objective accuracy.
  - How many Full errors have an objective-correct candidate in the pool.
  - How many of those are distinguishable by non-reference signals.
  - How many can only be resolved by oracle/reference.

### No-reference invariant

Formal FullV2 selection still does not use `reference_objective`, `objective_correct`, oracle fields, reference LP, or reference answers. These fields appear only in post-hoc diagnostics.

### Implication for the paper

If FullV2 equals Full in the upcoming Xshell run, the paper can honestly present FullV2-Guarded as a "safe improvement attempt" with detailed diagnostics, rather than claiming a new aggressive ranker. If FullV2 finds any strong overrides, the diagnostics will show exactly which non-reference signal justified each override.

`split_expected_structures(expected, problem_type)` now treats the problem-type schema as the base required set whenever `problem_type` is known, then unions truthy explicit `expected_structures` keys into that required set. Previously, any non-empty explicit expected map replaced the schema required set entirely.

Practical effect:

- `expected=None` or `{}` with `problem_type` still uses schema fallback.
- Partial explicit maps such as `{"capacity_constraint": True}` now add capacity to the default required structures instead of dropping default required structures like `inventory_balance`, `order_variable`, and `inventory_variable`.
- Optional and forbidden metadata still come from the schema when available, with any required keys removed from those metadata lists.

Caller impact: `check_structures()` receives the merged required list automatically through `split_expected_structures()`. Its regression test was updated to assert the new merge contract.

Verification: `python -m pytest tests/test_structure_schema.py tests/test_structure_rules.py -q` passed with `19 passed, 18 warnings`; full `python -m pytest -q` passed with `150 passed, 52 warnings`.

## 2026-06-19 — k=8 diagnostics and TypeAware fixes

Three k=8/100 experiment issues were fixed at the code/test level without regenerating candidates or changing `run_generation.py`:

1. Diagnostics candidate join/rank handling:
   - Candidate IDs such as `Qwen3-8B_k4` through `Qwen3-8B_k7` are now parsed with a general `_kN` rank parser instead of being collapsed into `k_ge_4` for diagnostics.
   - `compute_selection_diagnostics()` now uses stable selected/candidate matching by `problem_id` + normalized `candidate_id`, with unique parsed-rank fallback for compatible ID-format differences.
   - Diagnostics now return and write `diagnostic_join_unmatched.csv` with method, problem_id, candidate_id, parsed_candidate_rank, and reason.

2. TypeAware-Consensus is no longer forced through the same TypeAware-first critical penalty behavior:
   - `ReplenishVerifier-TypeAware` keeps its critical-pass pool filter.
   - `ReplenishVerifier-TypeAware-Consensus` remains consensus-first and applies critical missing structures inside its own score/tie-breaker rather than via the global 0.01 critical-structure multiplier.
   - Selection components now expose `type_aware_score`, `hard_gate_score`, consensus, structure, constraint, objective-term, and critical-missing fields, without reference/oracle fields.

3. Empty type-aware checklists are neutral:
   - For problem types with no applicable type-aware checklist, such as `single_period_newsvendor`, the type-aware score is now `1.0` rather than `0.0`.
   - `hard_gate_score` remains `1.0`, `hard_gate_failures` remains empty, and `type_aware_static_validation_errors` remains empty.

Verification: focused diagnostics/selection/static-validation/leakage tests passed with `53 passed`; full `python -m pytest -q` passed with `156 passed, 52 warnings`.

## 2026-06-20 — Executor now avoids top-level candidate solver code

## 2026-06-20 — LP export/parse pipeline now fails loudly instead of returning silent empty stats

After the executor top-level solver fix, the next all-zero result symptom pointed to the LP artifact layer. Local minimal reproduction with a valid PuLP model showed the happy path can export and parse LP correctly, so the risk was the failure path: failed or missing LP exports could fall through as `parsed=None`, which `compute_lp_stats(None)` represents as an empty artifact.

The hardened contract is now:

- `solve_pulp_model()` must call `model.writeLP(str(lp_path))` when `lp_path` is provided.
- After `writeLP`, the LP path must exist and be non-empty, otherwise `solve_pulp_model()` raises `RuntimeError("LP export failed: ...")`.
- Successful execution records `lp_exported=True` and `lp_export_error=None` in the execution result.
- `execute_generated_code()` propagates `lp_exported` and `lp_export_error`; export failures become `executable=False`, `status="Error"`, and an error traceback containing `LP export failed`.
- `parse_lp_file()` now reads from the on-disk `lp_path` and raises if the file is missing or empty.
- `evaluate_candidate()` annotates empty `lp_stats` with `error="LP export failed"` when the executor reports an export failure, rather than leaving only default zeros.

Verification:

- New regression tests cover missing LP file after `writeLP`, valid export stats through `evaluate_candidate`, and explicit LP export failure errors.
- Focused LP/selection tests passed with `47 passed, 18 warnings`.
- Full test suite passed with `164 passed, 52 warnings`.
- A manual minimal `evaluate_candidate()` check confirmed `lp_exported=True`, `constraints_count=1`, `objective_present=True`, and `hard_selection_gate.passed=True`.

No reference objective, oracle, or objective-correctness signal was added to formal selection.

## 2026-06-20 — ConsensusSafe selector design and diagnostics

`ReplenishVerifier-ConsensusSafe` is now a main-table no-reference selector intended to be safer than the earlier consensus-dominant TypeAware-Consensus variant.

Selection contract:

- Hard gate still requires executable + Optimal candidates.
- The dominant base signal is the candidate's existing ReplenishVerifier-Full raw score (`base_replenishverifier_score` / pre-overwrite `raw_inference_score`).
- Candidate objective consensus is a bonus/reranking signal, not an oracle signal and not dominant enough to override materially weaker safety signals.
- LP artifact health (`lp_exported`, objective present, constraints count, variables count), constraint coverage, objective-term coverage, type-aware hard gate score, type-aware score, code validity, static validation, critical missing count, repair feedback count, and runtime are candidate-observable tie-break/safety signals.
- `selection_components` intentionally excludes `reference_objective`, `objective_correct`, `relative_error`, oracle fields, `reference_lp`, and `reference_answer`; leakage audit covers the new method.

Diagnostics:

- `diagnose_selection_metrics` now writes `consensus_safe_counterfactual.csv` and `.md`.
- These files compare `ReplenishVerifier-ConsensusSafe` vs `Best-of-K` when they choose different candidates.
- The diagnostic table includes post-hoc objective correctness deltas plus non-reference signal columns explaining what ConsensusSafe saw: consensus, LP health, critical missing count, constraint coverage, objective-term coverage, and structure.
- The report explicitly states it is post-hoc diagnostics only and must not be used for formal selection.

Local validation:

- Focused tests passed with `54 passed`.
- Full suite passed with `172 passed, 52 warnings`.
- Demo smoke run `runs/debug_consensus_safe_demo15` confirmed the method appears in main results, diagnostics, paper metrics, and leakage audit.
- In the demo smoke run, `ConsensusSafe` tied `ReplenishVerifier-Full` and `Best-of-K`; this is only code-path validation, not real Qwen evidence.

Real k=8/100 status:

- This checkout does not contain `data/generated/test_100_v6.jsonl` or `data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl`.
- The exact requested run command failed locally with `ValueError: No benchmark rows found: data/generated/test_100_v6.jsonl`.
- No fake real-result directory or fake paper table was generated.
- The real rerun must be executed in the environment where those files exist.

No candidates were regenerated and `replenishverifier/llm/run_generation.py` was not modified.

## 2026-06-20 — Selector diagnostics repair findings

Root cause:

- `ReplenishVerifier-TypeAware-Consensus` had consensus in the score, but did not expose or explicitly prioritize consensus-cluster support as the first formal ranking concept after viability; TypeAware/structure/hard-gate signals could still keep it close to `ReplenishVerifier-TypeAware`.
- `ReplenishVerifier-Full` used a structure-heavy raw score and structure-heavy tie-breakers, so it could collapse to `Structure only` even though it was intended to combine multiple non-reference signals.

Fix contract:

- `ReplenishVerifier-TypeAware-Consensus` now records `consensus_cluster_support`, `finite_objective`, `lp_health_score`, code/static validity, critical-missing counts, and existing structure/type-aware coverage in `selection_components`.
- `ReplenishVerifier-Full` now records `selection_components` and uses a structure tie-window before candidate objective consensus, solver/finite objective, LP health, constraint coverage, objective-term coverage, type-aware/static validation, and critical-structure safety.
- Both selectors still avoid `reference_objective`, `objective_correct`, oracle, reference LP, and reference answers in formal ranking.

Rerun observations on `runs/qwen3_8b_k8_100_v6_typeaware_selectorfix`:

- `Full` no longer degenerates into `Structure only`: same_selection_rate is `0.2200`.
- `TypeAware-Consensus` no longer exactly aliases `TypeAware`: same_selection_rate is `0.9600`, still high but not forced to 1.0.
- `TypeAware-Consensus` and `ConsensusSafe` are identical in this run (`1.0000`), so method redundancy remains for that pair.
- `diagnostic_join_unmatched.csv` exists and is empty apart from the header, so selected/candidate joins matched cleanly.
- Leakage audit passed.

`evaluate_candidate()` in `replenishverifier/experiments/methods.py` calls `execute_generated_code()`; it does not have a separate execution path. The execution bug was inside `replenishverifier/solver/code_executor.py`.

Root cause:

- The old executor runner used `importlib.util.spec_from_file_location()` plus `spec.loader.exec_module(mod)` to load candidate code.
- `exec_module()` executes the entire candidate module top level before the runner can call `build_model()`.
- Candidates with top-level `model = build_model()` followed by `model.solve(pulp.PULP_CBC_CMD(msg=False))` therefore still ran candidate-owned solver code and could fail with `PULP_CBC_CMD: Not Available` before reaching the project-owned `solve_pulp_model()` path.
- Existing tests only covered solver calls inside `if __name__ == '__main__'`, which importlib does not execute as main; they did not cover top-level solver calls.

Fix:

- `execute_generated_code()` still writes and runs an isolated runner subprocess.
- The runner now parses the candidate source with `ast`, keeps safe top-level imports, definitions, docstring, and literal assignments, requires `build_model()`, executes that filtered module namespace, calls `build_model()`, then solves/export LP through `solve_pulp_model()`.
- This keeps executor ownership of solver selection and LP export while avoiding candidate top-level solver/export code.
- No selection, diagnostics, paper metrics, generation, candidate data, or experiment result code was changed.

Verification:

- New regression test failed before the fix, then passed after it.
- `python -m pytest tests/test_executor_solver_fallback.py -q` -> `4 passed`.
- `python -m pytest tests/test_executor_solver_fallback.py tests/test_runtime_overhead.py tests/test_strong_baselines.py -q` -> `17 passed`.
- `python -m pytest -q` -> `161 passed, 52 warnings`.

## 2026-06-20 — FullV2 consensus failure and structure-safety fix

Root cause:

- The initial `ReplenishVerifier-FullV2` ranking put objective-consensus cluster features before structure/constraint evidence.
- In real k=8/100 loss cases, a majority of candidates shared the same wrong objective, so consensus chose the wrong cluster even though the minority candidate had slightly stronger structure evidence.
- The key observed failures were `single_item_multi_period_0001` and `single_item_multi_period_0005`: FullV2 chose high-consensus wrong objectives, while Full/Structure chose the post-hoc correct minority candidate.

Fix:

- FullV2 now uses a no-reference structure-safety bucket before objective-consensus cluster features.
- Material structure-score differences can protect against a misleading wrong consensus majority.
- Very small structure-score differences remain in the same bucket, so FullV2 can still use consensus and does not collapse into pure Structure-only selection.
- Added paired directional tests: one for structure protection against misleading consensus, and one for consensus use when structure differences are small.

Rerun result on `runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620`:

- `Best-of-K`: objective_accuracy `0.7400`.
- `Structure only`: objective_accuracy `0.7400`.
- `ReplenishVerifier-Full`: objective_accuracy `0.7400`.
- `ReplenishVerifier-FullV2`: objective_accuracy `0.7400`.
- FullV2 is no longer below Full, but it does not exceed Full/Structure/Best-of-K.
- Leakage audit passed; FullV2 formal selection remains no-reference.

Remaining interpretation:

- Objective consensus can still be misleading.
- Structure/constraint evidence remains the safer signal in the observed pre-fix losses.
- There is no direct evidence that type-aware penalty was too strong in those losses; critical missing counts and type-aware hard-gate scores were tied.
- Remaining wrong selections are mostly candidate-pool-limited or non-reference indistinguishable; post-hoc correctness is diagnostic-only.
