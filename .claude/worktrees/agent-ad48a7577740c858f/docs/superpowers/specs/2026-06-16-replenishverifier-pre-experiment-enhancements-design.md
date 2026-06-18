# ReplenishVerifier Pre-Experiment Enhancements Design

Date: 2026-06-16

## Scope

This design covers the current pre-experiment engineering stage for ReplenishVerifier. The goal is to make the repository ready for later CCF-A-level empirical work without running real LLM generation, without running large benchmarks, and without filling paper result numbers.

The implementation must preserve the central no-leakage invariant: formal candidate selection must not use `reference_objective`; reference objectives are allowed only for final evaluation metrics.

## Confirmed Current State

The current codebase has these relevant entry points:

- `replenishverifier/llm/prompt_builder.py` builds generation and repair prompts. `build_prompt(sample)` currently exposes `expected_structures`.
- `replenishverifier/llm/run_generation.py` generates candidates but has no `--prompt_type` or seed metadata in output rows.
- `replenishverifier/llm/run_repair_generation.py` already accepts `--repair_type structure_aware/generic`, but the generic path still includes a constraint-naming block containing replenishment-specific labels.
- `replenishverifier/experiments/run_all_methods.py` writes only `repair_prompts.*`, not a parallel generic repair prompt file.
- `replenishverifier/experiments/methods.py` evaluates candidates, records `runtime_sec`, builds structure-aware repair prompt rows, and uses no-reference selection policies.
- `replenishverifier/solver/code_executor.py` executes generated code in a subprocess and exports LP files, but does not currently expose solver/export timing.
- `replenishverifier/experiments/rename_variables_for_robustness.py` already exists with `random`, `semantic`, and `adversarial` modes, but not the requested `descriptive_to_anonymous` mode.
- `replenishverifier/experiments/build_preference_data.py` builds chosen/rejected pairs from executable/optimal/structure signals without using `reference_objective`, but its metadata is incomplete for future DPO/PRM/LoRA use.

## Design: Lightweight Unified Schema Refactor

This is a bounded refactor. It introduces consistent prompt, repair, runtime, renaming, and preference metadata shapes without replacing the whole repository with new dataclass-heavy infrastructure.

### 1. Prompt Modes

`prompt_builder.py` will support three prompt types:

- `structured`: preserves the current behavior, including visible `expected_structures` and replenishment-specific naming hints. This mode is guided generation / appendix ablation only and must not be the main experiment default.
- `plain`: hides `expected_structures` and provides the natural language problem, parameters, and generic PuLP solve/export requirements. Parameters may be shown because the generated model needs instance data to build executable PuLP code; documentation will state this explicitly.
- `hidden_verifier`: hides `expected_structures`, preserves PuLP solve/export requirements, and asks for clear variable and constraint names without listing required replenishment structure labels. This will be the recommended default for main experiments.

`run_generation.py` will add:

- `--prompt_type {hidden_verifier,plain,structured}`, default `hidden_verifier`.
- `--seed`, optional.

Each candidate row will record:

- `prompt_type`
- `generation_config` containing max tokens, temperature, top-p, chat-template flag, trust-remote-code flag, and seed
- `model_name_or_path`
- a reproducibility note explaining that seeds improve reproducibility but GPU sampling, Transformers backend behavior, CUDA kernels, and hardware can still prevent exact determinism.

No real LLM generation will be run in this implementation stage.

### 2. Repair Prompt Fairness

Repair prompt construction will be split into two schema-compatible builders:

- `build_structure_aware_repair_prompts(rows)`
- `build_generic_repair_prompts(rows)`

`build_repair_prompts(rows)` may remain as a backward-compatible alias for the structure-aware builder.

Both prompt row types will use the same outer fields where possible:

- `problem_id`
- `candidate_id`
- `method_name`
- `candidate_method`
- `repair_type`
- `repair_feedback_count`
- `missing_structures`
- `low_score_required`
- `structure_certificates`
- `evidence_strength_by_rule`
- `execution`
- `generic_repair_feedback`
- `feedback`
- `repair_prompt`
- `original_candidate_text`
- `original_candidate_code`
- `prompt_type`
- `uses_reference_objective_for_repair`

Structure-aware rows may include replenishment-specific labels and repair hints such as `inventory_balance`, `capacity_constraint`, `shortage_variable`, `binary_order_variable`, `big_m_constraint`, and `fixed_order_cost`.

Generic rows must use only generic execution, solver, LP-artifact, and audit feedback. They must not expose replenishment-specific missing labels or hints. The generic repair prompt text must not include the current replenishment-specific `CONSTRAINT_NAMING_REGULATION` block.

`run_all_methods.py` will output both:

- `repair_prompts.jsonl`, `.csv`, `.md`
- `generic_repair_prompts.jsonl`, `.csv`, `.md`

`run_repair_generation.py --repair_type generic` will consume the generic prompt file and preserve method/candidate prefixes.

### 3. Runtime Overhead Metadata

Candidate evaluation will expose a unified runtime object and backward-compatible flat fields.

Preferred object:

```json
"runtime": {
  "code_execution_time": 0.0,
  "solver_lp_export_time": 0.0,
  "solver_time": 0.0,
  "lp_parse_time": 0.0,
  "structure_check_time": 0.0,
  "total_candidate_evaluation_time": 0.0
}
```

Flat aliases will also be written:

- `code_execution_time`
- `solver_lp_export_time`
- `solver_time`
- `lp_parse_time`
- `structure_check_time`
- `total_candidate_evaluation_time`
- `runtime_sec` remains for compatibility and mirrors total evaluation time.

`code_executor.py` will time the subprocess execution in the parent process and, where possible, time LP export and solver calls inside the runner. If a field cannot be measured for an error path, it will be `None` rather than fabricated.

A new CLI module will be added:

```bash
python -m replenishverifier.experiments.analyze_runtime_overhead --exp_dir <exp_dir>
```

It reads `<exp_dir>/candidate_evaluations.jsonl` and writes:

- `<exp_dir>/runtime_overhead.jsonl`
- `<exp_dir>/runtime_overhead.csv`
- `<exp_dir>/runtime_overhead.md`

The Markdown report will include candidate count, average and median total evaluation time, average LP parse time, average structure check time, and missing-field summaries. Missing values will be rendered as `NA`, never guessed.

### 4. Variable Renaming Robustness

The existing `rename_variables_for_robustness.py` will be extended, not replaced.

Required modes:

- `random`
- `descriptive_to_anonymous`

Existing `semantic` and `adversarial` modes may remain as legacy/compatibility aliases.

The script will explicitly describe itself as a lightweight text-level perturbation. It will not claim AST-safe renaming. Documentation will require sample-level manual inspection before formal experiments.

Output rows will preserve evaluation/reference labels including `reference_objective` if present, and will add:

- `source_candidate_id`
- `renaming_mode`
- `renaming_map`
- `renaming_warning`

### 5. Preference Data Metadata

`build_preference_data.py` will keep preference construction no-reference. `_preference_score()` must not read `reference_objective`.

Each preference pair will include richer metadata:

- chosen missing structures
- rejected missing structures
- chosen execution status
- rejected execution status
- chosen structure certificate summary
- rejected structure certificate summary
- `uses_reference_objective_for_preference=False`
- `preference_source="replenishment_structure_verifier"`
- `preference_construction_version`
- `problem_type`
- `difficulty`
- `prompt_type` if available
- `candidate_ids`

The output should keep top-level compatibility fields such as `chosen_candidate_id`, `rejected_candidate_id`, `chosen`, and `rejected`, while adding a nested metadata object for future training pipelines.

Documentation and paper text must state that this preference data is a future learning signal for DPO/PRM/LoRA-style work. It does not imply that DPO, PRM, LoRA, RL, or SFT training has been completed.

### 6. Documentation and Paper Synchronization

The following files will be updated:

- `README.md`
- `docs/experiment_operation_guide.md`
- `docs/real_llm_experiment_checklist.md`
- `docs/code_and_claim_risk_audit.md`
- `docs/ccfa_revision_roadmap.md`
- `docs/submit_readiness_checklist.md`
- `papers/replenishverifier_draft_zh.md`
- `papers/replenishverifier_draft_en.md`

They will explain:

1. why `prompt_type` exists;
2. why `structured` prompt is not valid as the main experiment default;
3. how generic repair differs from structure-aware repair;
4. why runtime overhead is a necessary experiment metric;
5. why variable renaming robustness is only a lightweight text-level perturbation;
6. why preference data is a future learning signal;
7. why formal selection never uses `reference_objective`;
8. why ReplenishVerifier's core innovation is LP-artifact-grounded replenishment structure supervision rather than generic solver debugging.

No experimental numbers will be inserted. Existing placeholders should remain `[TO FILL AFTER REAL LLM EXPERIMENT]`.

### 7. Tests

New or updated tests will cover:

- prompt modes and leakage behavior;
- generic repair prompts not containing replenishment-specific missing labels;
- structure-aware repair prompts containing missing-structure feedback;
- both repair prompt types containing original candidate/problem information and compatible schemas;
- runtime overhead analyzer with a minimal fake experiment directory;
- runtime overhead analyzer behavior when fields are missing;
- renaming robustness producing changed code while preserving reference/evaluation labels;
- preference metadata completeness;
- preference pair construction not changing when `reference_objective` values are changed;
- no-reference leakage audit still passing for formal selection rows.

Final verification command:

```bash
python -m pytest
```

If full tests fail, the implementation must report the concrete failure and fix it where possible. It must not bypass tests.

## Explicit Non-Goals

This stage will not:

- run real LLM candidate generation;
- run large-scale benchmark experiments;
- fill any result number or `[TO FILL AFTER REAL LLM EXPERIMENT]` placeholder;
- claim completed SFT, DPO, PRM, RL, LoRA, TGRPO, or repair-training results;
- use `reference_objective` for formal candidate selection or preference construction;
- create a git worktree;
- use Explore subagents.

## Self-Review

- Placeholder scan: the design intentionally contains no implementation placeholders except the paper placeholder string that must remain unchanged in result sections.
- Consistency: prompt, repair, runtime, renaming, preference, and documentation changes all preserve the no-reference selection invariant.
- Scope: the design is bounded to pre-experiment code and documentation readiness. It does not include real experimental runs or training.
- Ambiguity: `hidden_verifier` is the default main-experiment prompt type; `structured` is guided/appendix-only; missing runtime values are `None`/`NA`, not invented.
