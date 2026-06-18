# ReplenishVerifier Experiment Improvements Design

## Goal

Improve the ReplenishVerifier experimental code for Qwen3-8B candidate generation, diagnosis, no-reference selection, and optional repair while preserving the project's no-leakage invariant.

Target outcomes:

- diagnose why Qwen3-8B format-fix v2 still has limited objective accuracy and structure completeness;
- make candidate quality signals explicit and reusable;
- reduce invalid Qwen generations through bounded retry;
- prevent consensus or solver-only signals from selecting candidates with critical missing replenishment structures;
- support real second-round LLM repair as an off-by-default experimental path;
- keep Direct unchanged and keep formal selection free of reference answers, reference LPs, reference status, and `reference_objective`.

## Non-goals

- Do not delete or overwrite existing experiment results.
- Do not introduce large dependencies.
- Do not upload, download, or bundle model weights.
- Do not run large real LLM experiments as part of implementation verification.
- Do not claim repair improvement unless repaired candidates are actually generated and re-evaluated.
- Do not use `reference_objective` or reference artifacts in formal selection.

## Architecture

Use a modular quality-signal layer shared by generation retry, evaluation rows, diagnostics, and selection tie-breakers.

New or changed modules:

- `replenishverifier/pipeline/quality_signals.py`
  - Computes static candidate-observable code and pattern features.
  - Computes a bounded `static_validation_score` and `static_validation_errors`.
  - Does not read reference objectives, reference code, reference LPs, or reference solver status.

- `replenishverifier/experiments/diagnose_run.py`
  - Reads benchmark rows, candidate evaluation rows, and selected main results.
  - Produces diagnostic JSONL, CSV, and Markdown outputs.
  - May use `reference_objective` only for evaluation/oracle analysis, never for selection.

- `replenishverifier/llm/run_generation.py`
  - Adds bounded retry options for invalid code output.
  - Stores attempt metadata for each final candidate.

- `replenishverifier/pipeline/scoring.py` and `replenishverifier/experiments/methods.py`
  - Add critical structure penalties and deterministic tie-breakers for ReplenishVerifier/structure-aware selection methods.
  - Preserve Direct behavior.
  - Keep generic baselines generic.

- `replenishverifier/llm/run_repair_generation.py` and optionally `replenishverifier/experiments/run_all_methods.py`
  - Keep real LLM repair off by default.
  - Reuse the existing repair generation path for actual repaired candidates.
  - Only call it when explicitly enabled.

## Quality signals

`compute_static_validation(generated_code, problem_type=None)` returns fields such as:

```python
{
    "has_build_model": bool,
    "has_pulp_problem": bool,
    "has_objective": bool,
    "has_constraints": bool,
    "has_inventory_balance_pattern": bool,
    "has_capacity_pattern": bool,
    "has_shortage_pattern": bool,
    "has_binary_order_pattern": bool,
    "has_big_m_pattern": bool,
    "has_fixed_order_cost_pattern": bool,
    "static_validation_errors": list[str],
    "static_validation_score": float,
}
```

Allowed inputs:

- generated code text;
- candidate execution result;
- parsed candidate LP artifact;
- candidate structure verification result;
- problem type and expected-structure schema.

Forbidden inputs for formal selection:

- `reference_objective`;
- objective distance to the reference;
- reference code;
- reference LP;
- reference solver status;
- oracle-best candidate labels.

The same static validation result should be attached to candidate generation rows and candidate evaluation rows so diagnostics and selectors see consistent fields.

## Diagnostic script

Add CLI:

```bash
python -m replenishverifier.experiments.diagnose_run \
  --benchmark data/generated/test_50.jsonl \
  --candidate_evaluations runs/qwen3_8b_k4_50_formatfix_v2/candidate_evaluations.jsonl \
  --main_results runs/qwen3_8b_k4_50_formatfix_v2/main_results.jsonl \
  --out_dir runs/qwen3_8b_k4_50_formatfix_v2/diagnostics
```

Outputs:

- `problem_diagnostics.jsonl`
- `problem_type_summary.csv`
- `candidate_diversity.csv`
- `missing_structure_distribution.csv`
- `failure_examples.jsonl`
- `summary.md`

Per-problem diagnostics include:

- whether Direct is objective-correct;
- whether any K candidate is objective-correct;
- whether any K candidate is structurally complete;
- whether the selected candidate is objective-correct;
- whether the selector missed an oracle-best candidate;
- selected candidate missing structures;
- selected candidate static validation errors;
- unique objective-value count;
- unique structure-signature count;
- selected candidate index.

Problem-type summaries include:

- `n`;
- `executable_rate`;
- `optimal_rate`;
- `objective_accuracy`;
- `structure_completeness`;
- `main_error_type_distribution`.

Missing-structure distribution includes counts for:

- `missing_capacity_constraint`;
- `missing_inventory_balance`;
- `missing_shortage_variable`;
- `missing_big_m_constraint`;
- `missing_fixed_order_cost`.

Failure examples output top cases by error type, including:

- `problem_id`;
- `problem_type`;
- selected method;
- selected candidate ID;
- candidate objective;
- reference objective for evaluation display only;
- missing structures;
- static validation errors;
- generated code excerpt;
- repair feedback.

## Generation retry

Add CLI options to `run_generation.py`:

```bash
--max_generation_attempts_per_candidate 3
--require_static_valid_code
--retry_on_invalid_code
```

Defaults preserve existing behavior:

- `max_generation_attempts_per_candidate=1`;
- `require_static_valid_code=False`;
- `retry_on_invalid_code=False`.

When retry is enabled, each candidate is generated at most N times. Retry triggers include:

- raw output contains `<think>`;
- extraction returns empty code;
- code has syntax errors;
- code lacks `def build_model`;
- code lacks `pulp.LpProblem`;
- when `--require_static_valid_code` is set, static validation fails required surface checks.

The final row must still be saved even if all attempts fail. Store attempt metadata:

```python
{
    "attempt_count": int,
    "attempts": [
        {
            "attempt_index": int,
            "raw_contains_think": bool,
            "extracted_code_chars": int,
            "code_output_format_valid": bool,
            "static_validation_score": float,
            "static_validation_errors": list[str],
            "accepted": bool,
            "error": str | None,
        }
    ],
}
```

## Selection scoring

Direct remains unchanged and continues to select candidate index 0.

For structure-aware selectors, add critical-structure penalties based on candidate-observable structure verification:

- missing `inventory_balance` is a hard penalty;
- `multi_item_capacity` missing `capacity_constraint` is a hard penalty;
- shortage problems missing `shortage_variable` or `shortage_cost` receive hard penalties;
- `fixed_order_cost_big_m` missing `binary_order_variable`, `big_m_constraint`, or `fixed_order_cost` receives hard penalties.

Apply these penalties to structure-aware methods such as:

- `Structure-Only`;
- `Solver + Structure`;
- `Structure + Consensus`;
- `Solver + Structure + Consensus`;
- `Structure-Grounded Consistency`;
- `ReplenishVerifier-Full`;
- `ReplenishVerifier-Repair` if it is used as a selector over evaluated rows.

Do not apply replenishment-specific penalties to generic baselines such as `Solver-Filter`, `OR-R1-like Voting`, `SIRL-like LP-Stats`, `OptArgus-like Audit`, or `OptiRepair-like Repair-Prompt`.

Consensus must not override critical structure failure. A candidate with high objective consensus but missing a critical required structure should receive a near-zero structure-aware score.

## Tie-breaking

Use a deterministic no-reference tie-break key for non-Direct selectors:

```python
(
    gated_score,
    structure_score,
    inventory_balance_score,
    constraint_coverage,
    -repair_feedback_count,
    static_validation_score,
    -candidate_index,
)
```

Best-of-K should select the best viable candidate under this tie-breaker rather than simply the first viable candidate. Candidate order remains the final fallback only.

## Optional repair loop

Current `run_all_methods.py` should continue to generate repair prompt artifacts by default. Real LLM repair remains opt-in.

Expose optional controls through either `run_all_methods.py` or a thin wrapper around `run_repair_generation.py`:

```bash
--enable_llm_repair
--repair_rounds 1
--repair_model Qwen/Qwen3-8B
--repair_only_failed_or_low_structure
```

Repair prompt inputs include:

- original problem text and parameters;
- original candidate code;
- verifier feedback;
- static validation errors;
- problem-type template requirements.

A repaired candidate becomes a repair result only after it is generated and re-evaluated through the same execution, LP parsing, structure verification, and evaluation path as first-round candidates.

## Testing

Add focused tests for:

- static validation features and scores;
- generation retry and attempt metadata using monkeypatched generation;
- diagnostic output fields and oracle-analysis separation;
- selection penalties ensuring critical missing structures beat consensus;
- Direct still selecting candidate index 0;
- Best-of-K using tie-breakers;
- optional repair remaining disabled by default.

Expected verification commands:

```bash
python -m pytest tests/test_static_validation.py tests/test_run_generation_retry.py tests/test_diagnose_run.py tests/test_selection_gating.py -q
python -m pytest -q
```

## Leakage controls

Formal selection must not use:

- `reference_objective`;
- objective accuracy;
- relative error;
- reference code;
- reference LP;
- reference solver status;
- oracle-best labels from diagnostics.

Diagnostics may compute oracle upper bounds and missed-oracle indicators because they are post-selection analysis artifacts. These values must not be written back into selection score fields.

After implementation, run the existing leakage audit on any real experiment before using results for paper claims.

## Documentation updates

Update `progress.md` after implementation with:

- files changed;
- tests run;
- confirmation that no large LLM experiment was run;
- confirmation that no existing experiment results were deleted;
- confirmation that repair remains prompt-only unless opt-in repair generation and re-evaluation are executed.

Update `findings.md` only if a durable invariant or project-level fact changes.
