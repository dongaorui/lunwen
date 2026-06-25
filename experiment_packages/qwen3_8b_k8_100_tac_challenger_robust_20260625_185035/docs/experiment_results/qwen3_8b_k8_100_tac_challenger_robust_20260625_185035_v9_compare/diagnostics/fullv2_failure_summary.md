# FullV2 Failure Summary

Post-hoc diagnostics only; do not use this file for formal selection.

## Outcome

`ReplenishVerifier-FullV2` is now a conservative guarded extension of `ReplenishVerifier-Full`. It keeps Full's selected candidate unless a strong no-reference challenger justifies an override. Therefore FullV2 objective_accuracy is at least Full's objective_accuracy on every run, and it never regresses because of runtime or candidate-rank tie-breaks.

| method | objective_accuracy |
| --- | ---: |
| ReplenishVerifier-Full | 0.8100 |
| ReplenishVerifier-FullV2 | 0.8100 |

## Full error analysis

| category | count |
| --- | ---: |
| Total Full selections | 100 |
| Full objective errors | 19 |
| Full errors with an objective-correct candidate in pool | 4 |
| ... distinguishable by non-reference signals | 0 |
| ... only distinguishable by oracle/reference | 4 |
| Full errors with no objective-correct candidate in pool (pool-limited) | 15 |

## Interpretation

- **objective consensus misleading:** possible whenever a wrong objective cluster is larger than the correct one; FullV2 no longer overrides Full based on consensus alone.
- **structure/constraint still stronger:** the override rules require the challenger to be at least as strong on structure, so structural regressions cannot be introduced by consensus or runtime signals.
- **type-aware penalty too strong:** no direct evidence in observed loss cases; critical missing counts and type-aware hard-gate scores are part of the safety check but do not override a clean Full base on their own.
- **non-reference signals unable to distinguish:** when all viable candidates tie on execution, structure, constraints, objective terms, LP health, and code/static validity, only post-hoc objective correctness can tell which candidate is right.

## Leakage status

Formal selection remains no-reference: `reference_objective`, `objective_correct`, oracle fields, reference LP, and reference answers are not used by FullV2 selection.
