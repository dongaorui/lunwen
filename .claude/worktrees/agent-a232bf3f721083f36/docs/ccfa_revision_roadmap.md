# CCF-A Revision Roadmap for ReplenishVerifier

## Target positioning

**English title:** ReplenishVerifier: Constraint-Level LP-Structure Verification for LLM-Based Supply Chain Replenishment Optimization Modeling

**Chinese title:** ReplenishVerifier：面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证方法

The current thesis should be stated as:

> LLM-generated replenishment optimization code may be executable, solver-optimal, or supported by objective consensus while still missing required supply-chain replenishment structures. ReplenishVerifier verifies constraint-level LP structure from solver-exported artifacts and uses the evidence for no-reference candidate selection, feedback, repair prompting, and future verifier-guided preference data.

All unfinished empirical results must remain `[TO FILL AFTER REAL LLM EXPERIMENT]`.

## Current repository strengths

- **Constraint-level verification path exists.** The code executes generated PuLP candidates, exports LP artifacts, parses objective/constraints/binaries/bounds, and applies replenishment-specific structure rules.
- **Problem-type-aware schema exists.** `EXPECTED_STRUCTURES_BY_TYPE` separates required, optional, and forbidden structures across newsvendor, multi-period inventory, shortage/backlog, capacity, and fixed-order-cost Big-M families.
- **Rule-level certificates exist.** Structure verification produces per-rule evidence, missing structures, and repair hints rather than only a scalar score.
- **No-reference selection discipline is encoded.** Formal selection policies mark `uses_reference_objective_for_selection=false`, and leakage audit checks selected rows.
- **Signal-isolation baselines exist.** Solver-only, objective-consensus, generic LP statistics, generic audit, and generic repair-prompt baselines are implemented as lightweight `*-like` comparisons.
- **Benchmark metadata now reflects replenishment semantics.** Generated rows include `semantic_frame`, `replenishment_entities`, and labeled `replenishment_modeling_steps`.
- **Repair and preference-data hooks exist.** The repository can generate separate structure-aware and generic repair prompt artifacts and build verifier-guided preference pairs, but these are not yet evidence of successful repair or training.
- **Prompt leakage controls exist.** Main experiments can use `hidden_verifier` or `plain` prompts that hide `expected_structures`; `structured` is reserved for guided/appendix ablation.
- **Runtime and robustness hooks exist.** Candidate evaluation records runtime fields for overhead analysis, and variable-renaming robustness can be probed with lightweight text-level perturbations.

## Why the repository is not directly CCF-A-ready yet

- **Main empirical results are not completed.** Real LLM candidates, real repaired candidates, and audited result tables must be produced before performance claims can be made.
- **Current smoke runs are not paper evidence.** Demo/synthetic candidates validate the pipeline only; they cannot support main claims.
- **Verifier is heuristic.** LP parsing and structure rules do not prove mathematical equivalence, coefficient correctness, index correctness, or boundary-condition correctness.
- **Benchmark scope is limited.** The current benchmark covers five replenishment families and does not yet include richer supply-chain settings such as lost sales, stochastic service levels, multi-echelon networks, supplier constraints, transportation links, or rolling horizon.
- **Weights are hand-designed.** Current selection weights are interpretable but not learned or tuned from a held-out validation protocol.
- **`*-like` baselines are not faithful reproductions.** They are valid signal-isolation baselines, but the paper must not imply full reproduction of SIRL, OR-R1, OptArgus, or OptiRepair.
- **Repair and preference learning are not complete experimental claims.** Repair prompts and preference pairs are available, but real second-round repair and DPO/PRM training are future or optional experiments until actually run.

## Code items to complete before a stronger submission

| Item | Status | Notes |
|---|---|---|
| Maintain no-reference selection audit | done | Existing audit checks selected rows and policy text. Keep it mandatory after every run. |
| Add stricter parser tests for unnamed PuLP constraints | TODO | Verify `_C1/_C2` constraints are preserved but not treated as semantic-name evidence. |
| Add more coefficient/index diagnostics | TODO | Needed to reduce false positives when high-level structures exist but coefficients or time indices are wrong. |
| Add lead-time benchmark family | TODO | `lead_time` is in schema but not yet a full benchmark family. |
| Add lost-sales / service-level families | TODO | Important for supply-chain replenishment breadth. |
| Add sandbox option for untrusted code | TODO | Current executor runs generated Python; external untrusted code should be sandboxed. |
| Calibrate or learn scoring weights | TODO | Current weights are hand-designed; learning should be clearly separated from current verifier-only claims. |
| Keep legacy imports stable | done | Current changes preserve existing imports and method names. |

## Experiment items to complete before main-paper claims

| Item | Status | Notes |
|---|---|---|
| Generate real LLM candidates | TODO | Do not use synthetic demo candidates for main claims. |
| Run all methods on real candidates | TODO | Include Direct, Best-of-K, Solver-Filter, OR-R1-like Voting, SIRL-like LP-Stats, OptArgus-like Audit, Structure-Grounded Consistency, and ReplenishVerifier-Full. |
| Run leakage audit | blocked_by_experiment | Must pass before paper use. |
| Build paper tables | blocked_by_experiment | All cells remain `[TO FILL AFTER REAL LLM EXPERIMENT]` until real runs finish. |
| Extract real case studies | blocked_by_experiment | Cases should come from real LLM outputs, not demo candidates. |
| Run second-round repair generation | TODO | Required before claiming ReplenishVerifier-Repair effectiveness. |
| Evaluate repaired candidates | blocked_by_experiment | Required after repair generation. |
| Build preference data | optional | Can be reported as future training data, not as completed DPO/PRM training. |
| Run DPO/PRM/reranker training | future | Only claim if actually implemented, trained, and evaluated. |

## Claims currently safe to write

- ReplenishVerifier is a prototype for constraint-level LP-structure verification in LLM-generated supply-chain replenishment optimization models.
- It extracts evidence from solver-exported LP artifacts rather than checking only prompt text or code surface form.
- It supports problem-type-aware required/optional structure scoring through `EXPECTED_STRUCTURES_BY_TYPE`.
- It provides rule-level certificates, missing-structure feedback, repair prompts, and preference-pair construction utilities.
- Formal selection is designed not to use `reference_objective`; reference objectives are evaluation-only.
- `*-like` baselines are lightweight signal-isolation baselines, not faithful reproductions.
- Synthetic smoke tests show that the pipeline runs end to end, but do not establish performance.

## Claims that must wait for real LLM experiments

- ReplenishVerifier improves objective accuracy, structure completeness, or constraint coverage over baselines.
- ReplenishVerifier outperforms OR-R1-like, SIRL-like, OptArgus-like, or OptiRepair-like baselines on real LLM outputs.
- Objective consensus fails in a measured proportion of real replenishment cases.
- Structure-aware repair improves real candidate quality.
- Preference data improves DPO, PRM, reranker, or RL training.
- Any quantitative claim in the main, ablation, low-resource, difficulty, repair, robustness, or case-study tables.

All such claims should remain `[TO FILL AFTER REAL LLM EXPERIMENT]` until experiments are actually run and audited.

## What two A40 GPUs are suitable for

- Running local open-weight LLM candidate generation for moderate-size replenishment benchmarks.
- Running K-candidate generation and second-round repair generation for models that fit on available VRAM with appropriate precision and batching.
- Running small-to-medium ablation studies over prompts, K values, and repair settings.
- Generating enough real cases for qualitative case studies and error analysis.
- Potentially training lightweight rerankers or small adapters if memory permits and the training protocol is modest.

## What two A40 GPUs are not suitable for

- Full reproduction of large-scale OR-R1-style test-time RL or large reinforcement-learning pipelines.
- Full-scale pretraining or large DPO/PRM training for frontier-scale models.
- Claims requiring broad multi-model, multi-dataset industrial benchmarking unless compute/time budget is expanded.
- Exhaustive hyperparameter sweeps over many models, prompts, repair rounds, and large benchmark sizes.
- Any experiment that cannot be reproduced or audited within the repository's logging and leakage-audit protocol.

## Three submission-risk levels

### 1. Verifier-only

**Scope:** Candidate generation, LP artifact parsing, structure certificates, no-reference candidate selection, and signal-isolation baselines.

**Risk:** Medium to high for CCF-A unless real LLM experiments are strong and case studies clearly show failures of solver-only/objective-consensus baselines.

**Safe claim:** Replenishment-specific constraint-level LP verification provides an interpretable signal beyond generic execution and LP statistics, if real experiments support it.

### 2. Verifier + Repair

**Scope:** Verifier-only plus real second-round LLM repair candidates generated from structure-aware feedback and re-evaluated.

**Risk:** Medium if repair genuinely improves missing-structure cases; high if repair is only prompt generation.

**Safe claim only after experiments:** Structure-aware repair feedback can improve candidate structure completeness and/or reduce missing replenishment constraints.

### 3. Verifier + Repair + Preference Learning

**Scope:** Verifier-only plus repair plus actual DPO/PRM/reranker training using verifier-guided preference data.

**Risk:** Potentially stronger novelty but higher implementation and experimental risk. Requires careful separation from existing process-supervision and preference-learning work.

**Safe claim only after experiments:** Verifier-generated preference data improves a trained model/reranker on held-out replenishment modeling tasks without reference-objective leakage.

## Recommended next milestone

Run a real, audited verifier-only experiment first. Keep every results table cell as `[TO FILL AFTER REAL LLM EXPERIMENT]` until the following are complete:

1. real candidate generation;
2. all-method evaluation;
3. leakage audit;
4. error analysis;
5. case-study extraction;
6. paper table construction.
