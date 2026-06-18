# Paper experiment revision plan

## Target title and thesis

**English title:** ReplenishVerifier: Constraint-Level LP-Structure Verification for LLM-Based Supply Chain Replenishment Optimization Modeling

**Chinese title:** ReplenishVerifier：面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证方法

ReplenishVerifier's increment is not generic solver execution, objective matching, majority voting, LP artifact existence, hallucination auditing, or repair prompting. The increment is **constraint-level, replenishment-specific LP structure verification** extracted from the model induced by generated solver code.

Therefore, the paper should show that the gain remains after comparing against strong generic signal-isolation baselines. All unfinished empirical results must remain `[TO FILL AFTER REAL LLM EXPERIMENT]`.

## Main experiment table

Recommended main-table methods:

1. `Direct`
   - First candidate only.
   - Shows single-shot generation quality.
2. `Best-of-K`
   - First executable candidate among K.
   - Shows coarse execution filtering.
3. `Solver-Filter`
   - Candidate-observable executable/optimal/objective-present signals.
   - No `reference_objective`.
4. `OR-R1-like Voting`
   - Executable + optimal + code/LP validity + objective consensus among K candidates.
   - No `reference_objective`; no replenishment structures.
5. `SIRL-like LP-Stats`
   - Generic solver + LP artifact statistics.
   - No replenishment structures.
6. `OptArgus-like Audit`
   - Generic objective/variable/constraint/implementation audit.
   - No inventory balance/Big-M/shortage-specific checks.
7. `Structure-Grounded Consistency`
   - Solver execution + required replenishment structure coverage + LP artifact key-structure evidence + candidate objective consensus.
   - No `reference_objective`.
8. `ReplenishVerifier-Full`
   - Solver execution + replenishment LP structure completeness + semantic consistency.
   - No `reference_objective`.

Optional in the main table only if real second-round repair is run:

9. `ReplenishVerifier-Repair`
   - Include only when repaired candidates are generated and evaluated by an LLM repair run.
   - Otherwise keep it as a prompt-generation analysis/appendix item.

## Appendix / secondary methods

- `Structure-Only`: important ablation, but not necessarily a main-table baseline.
- `OptiRepair-like Repair-Prompt`: include in appendix or strong-baseline table; it is not full OptiRepair.
- `ReplenishVerifier-Full + objective consensus`: optional appendix ablation using `--use_objective_consensus`.
- Synthetic demo candidate results: appendix/smoke only.
- External subset experiments on IndustryOR/MAMO: appendix unless large and clean enough.

## Ablation variants

Recommended ablations:

1. Full score: executable + optimal + replenishment structure + semantic consistency.
2. `Solver-Filter`: remove all LP structure.
3. `SIRL-like LP-Stats`: replace replenishment structure with generic LP artifact statistics.
4. `OptArgus-like Audit`: replace replenishment structure with generic audit.
5. `OR-R1-like Voting`: replace replenishment structure with test-time consensus/voting.
6. `Structure-Only`: remove solver-status component.
7. `Structure-Grounded Consistency`: combine required structure coverage and LP artifact evidence with candidate objective consensus.
8. Optional `Full + objective consensus`: test whether generic consensus is complementary or redundant.
9. Optional name-robustness stress test: renamed variables vs instructed `Q/I/B/Y` variables.

## Case study design

Pick real LLM cases where:

- Solver-only or OR-R1-like selects an executable optimal candidate but it misses `inventory_balance`.
- OptArgus-like Audit accepts a generic well-formed LP that lacks replenishment semantics.
- SIRL-like LP-Stats prefers a model with many variables/constraints but missing `big_m_constraint`.
- ReplenishVerifier-Full selects a structurally complete candidate.

The case study should show:

1. natural language problem;
2. selected baseline candidate summary;
3. missing replenishment structures;
4. ReplenishVerifier selected candidate;
5. why solver/objective/generic audit was insufficient;
6. verifier feedback that could guide repair.

Avoid using only synthetic demo candidates in the main case study. Synthetic cases are acceptable for appendix smoke-test illustration.

## Real LLM experiment settings to report

For each model:

- model name/path and version;
- inference hardware;
- prompt template version;
- whether expected structures are included in the candidate-generation prompt;
- K candidates per problem;
- temperature, top-p, max_new_tokens;
- decoding seed if available;
- code extraction strategy;
- timeout per candidate;
- solver version/backend;
- whether `--use_objective_consensus` is enabled;
- whether repair is prompt-only or actual second-round LLM generation;
- exact data split and random seed.

Critical: If expected structures are included in generation prompts, say so. It is acceptable, but then the method is verifying adherence to a structured generation instruction. A stricter setting can hide expected structures from the generator and use them only for verification.

## Results that should not be main-paper claims

- CPU-only demo candidates generated from reference templates.
- Case studies where Direct is artificially bad because candidate order starts with syntax errors.
- Repair results if only prompts are generated and no repaired candidate is run.
- Claims about DPO/RL improvement unless preference training is actually run.
- Claims about full OptArgus/OptiRepair/SIRL/OR-R1 reproduction.

## How to describe `*-like` baselines safely

Use language such as:

- “We implement lightweight baselines inspired by the observable signals emphasized in prior work.”
- “These are not full reproductions of the original systems, which involve different training data, agents, and optimization procedures.”
- “The purpose is to isolate whether generic solver execution, LP artifact statistics, hallucination auditing, repair-readiness, or objective consensus explain the gains.”

Specific wording:

- `SIRL-like LP-Stats`: “a generic solver/LP-artifact statistics baseline inspired by solver-informed reward signals.”
- `OptArgus-like Audit`: “a generic optimization-model audit baseline inspired by hallucination/structural-consistency checks.”
- `OptiRepair-like Repair-Prompt`: “a generic repair-readiness and repair-feedback baseline inspired by optimization model repair, without inventory-semantic feedback.”
- `OR-R1-like Voting`: “a test-time executable/valid-code/objective-consensus voting baseline inspired by OR-R1-style reward/voting signals.”

## Reference objective rule

Formal candidate selection must never use `reference_objective`. It can be used only after selection for:

- objective accuracy;
- relative error;
- final reporting/evaluation tables.

Allowed selection signals:

- candidate code format validity;
- executable / timeout / error;
- solver status;
- candidate objective presence;
- objective consensus among candidates for the same problem;
- generic LP artifact statistics;
- generic audit issues;
- replenishment-specific expected structure labels for ReplenishVerifier variants.

Forbidden in formal selection:

- absolute or relative distance to `reference_objective`;
- choosing the candidate with objective closest to the reference;
- using reference objective inside Solver-Filter or OR-R1-like Voting.
