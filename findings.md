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
