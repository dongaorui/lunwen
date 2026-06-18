# ReplenishVerifier: Constraint-Level LP-Structure Verification for LLM-Based Supply Chain Replenishment Optimization Modeling

## Abstract

Large language models (LLMs) can translate natural-language operations problems into executable solver code, but executable code and `Optimal` solver status are not equivalent to modeling correctness. In supply chain replenishment, a generated PuLP model may solve successfully while omitting the very constraints that define the problem: inventory balance, capacity limits, shortage or backlog variables, fixed ordering costs, binary setup variables, or Big-M linking constraints. Candidate objective consensus is also insufficient, because several candidates can agree on the same wrong formulation.

We present **ReplenishVerifier**, a constraint-level LP-structure verification prototype for LLM-based supply chain replenishment optimization modeling. Given LLM-generated PuLP code, ReplenishVerifier executes the candidate, exports the induced LP artifact, parses variables, objectives, constraints, binary declarations, and bounds, and checks problem-type-aware replenishment structures. Its schema distinguishes required, optional, and forbidden structures for single-period newsvendor, multi-period inventory, shortage/backlog, capacity-constrained multi-item replenishment, and fixed-order-cost Big-M models. The verifier produces rule-level structure certificates, required-structure coverage, missing-structure feedback, and no-reference selection signals.

The method is designed as a replenishment-specific supervision layer, not as a general LLM-for-OR agent or a faithful reproduction of prior systems. We use lightweight signal-isolation baselines inspired by solver filtering, OR-R1-style voting, SIRL-style LP statistics, OptArgus-style generic auditing, and OptiRepair-style generic repair prompting to separate generic execution and artifact signals from replenishment-specific structure evidence. Formal candidate selection does not use `reference_objective`; reference objectives are reserved for final evaluation metrics after selection. All empirical results in this draft remain `[TO FILL AFTER REAL LLM EXPERIMENT]`.

**Keywords:** LLM for optimization modeling; supply chain replenishment; LP artifact; constraint-level verification; inventory balance; Big-M linking; candidate selection

---

## 1. Introduction

LLMs increasingly generate optimization formulations and solver code from natural-language problem statements. For operations research modeling, this ability is promising but fragile. A correct solver program must define the right decision variables, encode the correct objective, and include all constraints that characterize the intended decision problem. A generated Python/PuLP program can be syntactically valid, executable, and solved to optimality while still representing a different mathematical model.

Supply chain replenishment is a useful setting for studying this problem because replenishment models are strongly structured. A single-period newsvendor model requires demand satisfaction with order, leftover inventory, and shortage variables. A multi-period inventory model requires inventory-balance constraints across time. A shortage/backlog model must include backlog variables and penalties. A multi-item warehouse model must include capacity constraints. A fixed-order-cost model must include binary setup variables and Big-M linking constraints. Missing any of these structures can make a solver-optimal answer operationally meaningless.

Generic execution signals do not reliably catch such errors. Solver status checks whether the generated mathematical program is solvable, not whether it is the intended program. Objective-value consensus among candidates can fail when many candidates share the same missing constraint. Generic LP statistics or audit signals can identify empty or malformed models, but they do not know that a replenishment problem requires inventory balance, capacity, shortage, setup, or Big-M structure.

ReplenishVerifier addresses this gap by verifying the LP artifact induced by generated code. The system executes a candidate PuLP program, exports the resulting `.lp` file, parses LP sections, and checks whether replenishment-specific structures appear with sufficient evidence. The resulting certificates can be used for candidate selection, error analysis, structure-aware repair prompts, and future verifier-guided preference data. The core idea is not to replace solvers or objective evaluation, but to add a constraint-level semantic signal between code generation and final evaluation.

The contributions are:

1. **Constraint-level replenishment LP-structure verification.** We operationalize inventory balance, demand satisfaction, shortage/backlog, capacity, fixed ordering cost, binary setup/order trigger, Big-M linking, nonnegative bounds, and objective minimization as problem-type-aware LP artifact checks.
2. **LP artifact certificates for candidate selection and feedback.** ReplenishVerifier exports and parses the LP induced by generated PuLP code, then emits rule-level certificates, required-structure coverage, missing reasons, and repair hints.
3. **Problem-type-aware benchmark schema.** The benchmark generator now includes replenishment-specific `semantic_frame`, `replenishment_entities`, and labeled `replenishment_modeling_steps`, while preserving unlabeled prompt exports and fixed-seed reproducibility.
4. **Structure-enhanced consistency candidate selection.** The implemented selectors combine code executability, solver status, LP artifact structure coverage, required replenishment structure coverage, and optional candidate objective consensus without using `reference_objective`.
5. **Leakage-aware experimental protocol with signal-isolation baselines.** Direct, Solver-Filter, OR-R1-like Voting, SIRL-like LP-Stats, OptArgus-like Audit, and OptiRepair-like Repair-Prompt are included as lightweight signal-isolation baselines, not faithful reproductions.

Benchmark expansion, real repair effectiveness, and DPO/PRM training are not claimed as completed contributions in this draft. They are future or optional experiments unless explicitly run and audited.

---

## 2. Related Work

### 2.1 LLMs for Optimization Modeling

Recent LLM-for-OR systems study how language models can formulate mathematical programs, write solver code, debug failures, and interact with optimization solvers. OptiMUS, Chain-of-Experts, ORLM, and LLMOPT are representative of this broader direction. They emphasize general optimization modeling, agentic decomposition, solver feedback, or instruction-tuned modeling ability across OR tasks.

ReplenishVerifier differs in scope. It does not attempt to be a general optimization-modeling agent. Instead, it focuses on a narrower but practically important verification problem: given LLM-generated solver code for supply chain replenishment, can we check whether the induced LP contains the constraint-level structures that the replenishment problem requires? This vertical focus allows the verifier to look for domain structures such as inventory balance, capacity, backlog, setup variables, and Big-M links rather than only generic solver success.

### 2.2 Solver-Informed Verification and Test-Time Learning

Solver-informed learning and verification methods use execution results, feasibility, solution quality, LP artifacts, or verifiable rewards to guide LLM optimization modeling. SIRL-style methods motivate the use of solver execution and LP artifacts as observable signals. OR-R1-style work emphasizes valid-code rewards, executable rewards, objective or answer voting, and test-time reinforcement learning.

ReplenishVerifier shares the principle that generated optimization code should be checked through the induced solver artifact, but it separates generic solver/artifact signals from replenishment-specific structure evidence. The repository therefore implements `SIRL-like LP-Stats` as a generic LP statistics baseline and `OR-R1-like Voting` as an executable / valid-code / objective-consensus baseline. These are lightweight signal-isolation baselines, not faithful reproductions of the original systems.

### 2.3 Data Synthesis and Validation for Optimization Modeling

Step-Opt, OptMATH, ORLM, and related benchmark-building work show the importance of structured data synthesis, rejection checks, and validated optimization instances. These lines motivate careful benchmark construction and validation.

ReplenishVerifier uses deterministic replenishment templates and validation checks, but the current benchmark should not be presented as a complete general OR benchmark. Its purpose is to support constraint-level replenishment verification. The generator creates problem-type-aware semantic frames and entity fields, validates labeled and unlabeled rows, and preserves the separation between parameter sampling and language-template selection. Larger and more diverse benchmark construction remains future work.

### 2.4 Audit and Repair of Generated Optimization Models

Generic audit and repair systems study hallucinations, malformed formulations, and repair feedback for generated optimization models. OptArgus-like auditing motivates checking objective, variable, constraint, and implementation consistency. OptiRepair-like repair motivates feedback-driven correction of generated models.

The repository distinguishes generic and replenishment-specific signals. `OptArgus-like Audit` checks generic objective/variable/constraint properties and placeholder names, but intentionally does not check inventory balance or Big-M structure. `OptiRepair-like Repair-Prompt` gives generic repair feedback about execution, objectives, variables, constraints, and bounds. ReplenishVerifier-specific repair prompts additionally mention missing required replenishment structures. Actual repair effectiveness must wait for real repaired candidates and re-evaluation.

### 2.5 Inventory Replenishment and Predict-Then-Optimize

Inventory and replenishment optimization includes classic newsvendor models, multi-period inventory control, capacity-constrained ordering, lead times, fixed ordering costs, service-level constraints, lost sales, and multi-echelon supply chains. Predict-then-optimize and end-to-end inventory-control studies highlight that downstream decisions can be sensitive to structural modeling assumptions.

This paper uses replenishment optimization not as a policy-learning benchmark but as a high-structure modeling domain. The goal is to verify whether an LLM-generated optimization formulation contains the domain constraints that make replenishment decisions meaningful.

---

## 3. Problem Setting

Input is a natural-language replenishment problem description, optionally accompanied by structured parameters such as demand, periods, items, initial inventory, costs, item volumes, capacity, and Big-M values. An LLM generates one or more candidate PuLP/Python programs for the same problem. Let candidate set for instance \(i\) be \(C_i=\{c_{i1},\ldots,c_{iK}\}\).

Executing a candidate induces:

- executable status;
- solver status;
- candidate objective value if available;
- an exported LP artifact if the model is built successfully;
- runtime and error information.

The formal selection goal is to choose a structurally reliable candidate using only candidate-observable signals. `reference_objective` must not be used during formal selection. It is allowed only after selection for evaluation metrics such as objective accuracy and relative error.

---

## 4. Method

### 4.1 Benchmark Schema

The code centralizes replenishment structure expectations in `EXPECTED_STRUCTURES_BY_TYPE`. Each problem type defines three sets:

- **required:** structures that must be present and contribute to the main `structure_score`;
- **optional:** structures reported for diagnostics but excluded from the score denominator;
- **forbidden:** explicit metadata reserved for future diagnostics.

Required/optional separation is crucial. A single-period newsvendor instance should not be penalized for lacking a Big-M linking constraint, while a fixed-order-cost Big-M instance must be penalized if the binary trigger or Big-M link is missing.

The benchmark generator also emits three replenishment-specific metadata fields:

- `semantic_frame`: domain-specific sets, parameters, decision variables, objective terms, constraints, solver type, replenishment structures, required structures, and optional structures;
- `replenishment_entities`: extracted replenishment entities such as demand, periods, items, order quantity, inventory level, shortage/backlog, costs, storage capacity, item volume, and Big-M;
- `replenishment_modeling_steps`: deterministic LP-structure-grounded modeling steps for labeled rows. Unlabeled rows omit these steps by default.

The validation function checks natural-language text, legal problem types, required semantic fields, label presence/absence for labeled/unlabeled modes, core entities, and required-structure coverage.

### 4.2 Candidate Execution and LP Artifact Export

Candidate code is executed through the generated-code executor. A valid candidate is expected to define a PuLP model, solve it, print status/objective, and export the LP when `OUTPUT_LP_PATH` is provided. Execution records whether code ran, solver status, objective value, LP path, runtime, and errors.

This step verifies only that the candidate induces a solvable mathematical program. It does not by itself prove that the program matches the intended replenishment model.

### 4.3 LP Parser and LP Structure Graph

The LP parser is a lightweight parser for PuLP-exported LP files. It extracts:

- optimization sense;
- objective expression;
- constraint names and expressions;
- bounds;
- binary variables;
- variable names.

The LP structure graph provides weak incidence-based evidence between variables and constraints. It helps detect Big-M-like linking, inventory recurrence candidates, and fixed-cost binary terms. This graph is auxiliary evidence, not a complete algebraic graph-matching proof.

The parser depends on PuLP LP formatting. Anonymous PuLP constraints may appear as `_C1`, `_C2`, and similar names; these constraints can still be parsed, but autogenerated names should not be treated as semantic evidence. Therefore prompts ask generated code to name constraints explicitly.

### 4.4 Structure Rules and Certificates

ReplenishVerifier checks structures through layered evidence:

1. variable-name hints such as `Q`, `I`, `B`, `Y`, `order_qty`, `inventory`, `backlog`, and `setup`;
2. constraint-name hints such as `inventory_balance`, `flow`, `capacity`, `big_m`, and `link`;
3. expression-supported evidence showing that relevant variables participate in the expected constraint pattern;
4. index and incidence evidence for repeated or adjacent inventory states;
5. magnitude hints for Big-M-like coefficients.

Each rule produces a certificate containing the rule name, whether it is required, pass/fail status, score, evidence, missing reason, repair hint, and additional diagnostics when available. The aggregate `structure_score` averages scores over required structures only.

This certificate design supports both selection and explanation. For example, a candidate can be executable and optimal but still receive a missing `inventory_balance` or `big_m_constraint` certificate.

### 4.5 No-Reference Candidate Selection

`ReplenishVerifier-Full` uses the ground-truth-free score:

\[
S(c)=0.25E(c)+0.25Z(c)+0.35SC(c)+0.15Sem(c),
\]

where \(E\) is executability, \(Z\) is optimal solver status, \(SC\) is required-structure score, and \(Sem\) is semantic consistency based on missing required structures. The hard selection gate gives non-zero formal selection score only to executable + `Optimal` candidates by default.

The repository also includes `Structure-Grounded Consistency`, which combines executable code, solver status, required-structure coverage, LP artifact structure coverage, and candidate objective consensus. It is distinct from `OR-R1-like Voting`: OR-R1-like Voting is a generic executable / valid-code / objective-consensus baseline and does not use replenishment structures.

`reference_objective` is not used by formal ranking helpers. It is recorded only for final evaluation metrics.

### 4.6 Feedback, Repair Prompts, and Preference Data

Missing required structures are converted into natural-language feedback and repair prompts. ReplenishVerifier-specific repair prompts may mention inventory balance, capacity, shortage/backlog, fixed cost, binary setup, or Big-M links. Generic OptiRepair-like prompts intentionally use only generic execution, solver, and LP-artifact audit feedback and do not include missing replenishment-structure labels.

The preference-data builder can create chosen/rejected pairs using executable status, optimal status, structure completeness, and repair-feedback counts. These pairs are future training data for DPO, PRM, reranking, or similar approaches. They do not imply that any preference-learning experiment has already been completed.

### 4.7 Prompt Leakage Controls and Practical Diagnostics

To avoid prompt-side leakage, main experiments use `hidden_verifier` or `plain` prompts that do not reveal `expected_structures`. The `structured` prompt exposes expected structures and is reserved for guided-generation or appendix ablations. We separately report generic repair prompts, which use execution/solver/audit feedback only, and structure-aware repair prompts, which may use missing replenishment structures and rule-level certificates. Preference pairs are exported only as future DPO/PRM/LoRA-style learning signals; no training benefit is claimed unless such training is actually performed and evaluated. Runtime overhead and naming-variation robustness are treated as required follow-up metrics, with naming perturbation implemented only as lightweight text-level rewriting.

---

## 5. Experimental Protocol

### 5.1 Research Questions

- **RQ1:** Do replenishment-specific LP-structure certificates detect errors that executable status and solver status miss?
- **RQ2:** Does structure-grounded candidate selection improve real LLM candidate selection compared with solver filtering, objective consensus, generic LP statistics, and generic audit baselines?
- **RQ3:** Which missing structures are most common in real LLM-generated replenishment models?
- **RQ4:** How does performance change under low candidate budgets such as \(K=1,2,4\)?
- **RQ5:** If real second-round repair is run, do structure-aware repair prompts improve candidate structure completeness?

### 5.2 Methods to Compare

| Method | Purpose | Selection uses reference objective? |
|---|---|---|
| Direct | first candidate | No |
| Best-of-K | first viable candidate among K | No |
| Solver-Filter | executable / Optimal / objective-present signal | No |
| OR-R1-like Voting | lightweight executable / valid-code / objective-consensus signal-isolation baseline | No |
| SIRL-like LP-Stats | lightweight generic LP artifact statistics baseline | No |
| OptArgus-like Audit | lightweight generic optimization-model audit baseline | No |
| OptiRepair-like Repair-Prompt | lightweight generic repair-readiness baseline | No |
| Structure-Grounded Consistency | execution + solver + required structure + LP artifact structure + candidate consensus | No |
| ReplenishVerifier-Full | execution + solver + replenishment structure + semantic consistency | No |
| ReplenishVerifier-Repair | only after real repaired candidates are generated and evaluated | No |

All `*-like` entries are lightweight signal-isolation baselines, not faithful reproductions.

### 5.3 Main Experiment Table

| Method | Executable Rate | Optimal Rate | Objective Accuracy | Relative Error | Structure Completeness | Constraint Coverage | Avg. Runtime |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Solver-Filter | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| OR-R1-like Voting | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| SIRL-like LP-Stats | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| OptArgus-like Audit | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| ReplenishVerifier-Full | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |

### 5.4 Ablations

| Variant | Purpose | Objective Accuracy | Structure Completeness | Constraint Coverage |
|---|---|---:|---:|---:|
| Structure-Only | remove solver-status weighting | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Structure-Grounded Consistency | add candidate objective consensus to structure evidence | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Full + objective consensus | optional appendix ablation | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Generic LP stats only | replace replenishment structures with LP statistics | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |

### 5.5 Repair and Preference Data

| Experiment | Status | Result |
|---|---|---|
| Structure-aware repair prompt generation | available in code | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Real second-round repair generation | not yet claimed | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Re-evaluation of repaired candidates | not yet claimed | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Verifier-guided preference data | available as future training data | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| DPO / PRM / reranker training | future work unless implemented | `[TO FILL AFTER REAL LLM EXPERIMENT]` |

---

## 6. Results

All quantitative results are reserved for real LLM experiments. Synthetic smoke-test outputs must not be used as main empirical evidence.

`[TO FILL AFTER REAL LLM EXPERIMENT]`

---

## 7. Case Studies

Real case studies should be selected only after real LLM candidate generation and no-leakage evaluation. Recommended cases include:

1. an executable/optimal candidate missing inventory balance;
2. objective-consensus candidates that share a missing capacity or Big-M constraint;
3. a generic LP-statistics baseline selecting a structurally incomplete candidate;
4. generic repair feedback failing to identify a replenishment-specific missing structure;
5. ReplenishVerifier selecting a candidate with stronger required-structure coverage.

`[TO FILL AFTER REAL LLM EXPERIMENT]`

---

## 8. Limitations

- The LP parser depends on PuLP LP format and is not a complete solver-independent LP/MPS parser.
- Structure verification is heuristic and is not full mathematical-equivalence verification.
- The current verifier can miss wrong coefficients, wrong time indices, wrong initial or terminal boundary conditions, and unsuitable Big-M magnitudes.
- The current benchmark covers a limited set of replenishment families.
- Selection weights are hand-designed and require later calibration or learning.
- Repair effectiveness requires real LLM repaired candidates and re-evaluation.
- Preference data does not mean DPO, PRM, reranker, or RL training has already been completed.
- All `*-like` baselines are lightweight signal-isolation baselines, not faithful reproductions of prior systems.
- Running generated code is a security risk; untrusted candidates should be executed in a sandbox.

---

## 9. Conclusion

ReplenishVerifier reframes LLM-based replenishment modeling evaluation around constraint-level LP structure. Executable code, solver optimality, and objective consensus are useful but incomplete signals. By exporting and parsing the LP artifact induced by generated PuLP code, the verifier checks whether problem-type-required replenishment structures are present and produces interpretable certificates for selection, feedback, repair prompting, and future preference-data construction.

The current paper draft deliberately avoids quantitative claims until real LLM experiments are completed and audited. The final empirical conclusion remains `[TO FILL AFTER REAL LLM EXPERIMENT]`.
