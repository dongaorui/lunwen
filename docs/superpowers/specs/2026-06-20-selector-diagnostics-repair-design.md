# Selector / Diagnostics Repair Design

## Context

The latest k=8/100 Qwen3-8B experiment package shows two selection-collapse symptoms:

- `ReplenishVerifier-TypeAware` and `ReplenishVerifier-TypeAware-Consensus` select the same candidates too often.
- `ReplenishVerifier-Full` is nearly identical to `Structure only`, indicating Full is still dominated by structure signals.

The repair must preserve the project invariant: formal selection is no-reference. Reference objective, objective correctness, oracle labels, reference LPs, and reference answers are evaluation/diagnostic-only signals.

## Scope

In scope:

- Repair existing selector ranking logic for `ReplenishVerifier-TypeAware-Consensus`.
- Repair existing selector ranking logic for `ReplenishVerifier-Full`.
- Add synthetic regression tests that prove these methods can select different candidates from their ablation counterparts.
- Re-run the provided experiment package inputs without regenerating candidates.
- Rebuild diagnostics, paper metrics, and leakage audit.

Out of scope:

- No candidate regeneration.
- No changes to `replenishverifier/llm/run_generation.py`.
- No deletion of existing methods.
- No problem-id or candidate-id hard-coding.
- No tuning against objective correctness or reference objective.

## Design: TypeAware-Consensus

`ReplenishVerifier-TypeAware-Consensus` will become explicitly consensus-cluster-first:

1. Prefer candidates that pass the normal executable + Optimal hard gate and have finite candidate objective values.
2. If no candidate passes that viability filter, fall back to the existing rows so the method remains total and backward compatible.
3. Rank first by objective-consensus support / cluster support computed from candidate objectives only.
4. Within the best-supported cluster, use no-reference tie-breakers:
   - solver optimality and finite objective;
   - LP artifact health;
   - structure completeness;
   - constraint coverage;
   - objective-term coverage;
   - type-aware score and hard-gate score;
   - critical missing structures as a penalty/tie-breaker, not as a pool filter;
   - static validation / code validity;
   - repair feedback count and runtime.
5. Empty type-aware checklists remain neutral and must not penalize candidates.

Expected test: construct three candidates where TypeAware chooses a high TypeAware-score isolated objective, while TypeAware-Consensus chooses one of two candidates in the majority objective-consensus cluster.

## Design: ReplenishVerifier-Full

`ReplenishVerifier-Full` will remain structure-aware but stop being structure-only:

1. Keep executable / Optimal / finite objective as strong quality signals.
2. Keep structure completeness important.
3. Add a structure tie-window: if candidates are within a small structure window, use consensus, solver/objective presence, LP health, constraint coverage, type-aware/static validation, objective-term coverage, and critical-missing penalties to break ties.
4. If structure scores are exactly equal, Full must be able to choose a different candidate from Structure only based on the non-reference signals.
5. Continue to expose no-reference selection components and policy text.

Expected test: construct two candidates with equal structure score. Structure only selects candidate A by order/tie behavior, while Full selects candidate B because B has stronger solver/consensus/static/type-aware/LP quality.

## Diagnostics and rerun

After tests and implementation:

- Run focused selector/diagnostic/leakage tests.
- Run the full pytest suite.
- Re-run `run_all_methods` using the package-local benchmark and candidates, decompressing the existing `.jsonl.gz` candidate file only as an input conversion step. This is not candidate regeneration.
- Re-run `diagnose_selection_metrics`, `analyze_error_types`, `audit_leakage --write_report`, and `build_paper_metrics`.
- Confirm `diagnostic_join_unmatched.csv` exists and summarize unmatched reasons.
- Report main objective accuracies and redundancy rates for:
  - TypeAware vs TypeAware-Consensus;
  - Full vs Structure only.

## Safety / leakage controls

The selector code may read only candidate-observable fields:

- execution status, objective existence/value for candidate-consensus clustering, LP artifact health;
- structure completeness and required-structure coverage;
- constraint coverage;
- objective-term coverage;
- type-aware static validation and hard gate;
- generic static/code validity;
- runtime and repair feedback counts.

The selector code must not read:

- `reference_objective`;
- `objective_correct` / `objective_accuracy` as correctness labels;
- relative error to reference;
- oracle/pass@k labels;
- reference LP or reference answer.

Post-hoc diagnostics may report correctness deltas, but those outputs must remain clearly diagnostic and must not feed back into ranking.
