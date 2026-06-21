# FullV2 vs Structure Summary

Posthoc-only diagnostics; do not use for formal selection.

- Full vs Structure same_selection_rate: 0.9600
- FullV2 vs Structure same_selection_rate: 0.9600
- FullV2 vs Full same_selection_rate: 1.0000
- FullV2 vs Best-of-K same_selection_rate: 0.4200
- Full objective_accuracy: 0.8200
- Structure objective_accuracy: 0.8200
- FullV2 objective_accuracy: 0.8200
- Best-of-K objective_accuracy: 0.7900
- FullV2 beats Structure count: 0
- Structure beats FullV2 count: 0
- Both correct count: 82
- Both wrong count: 18
- FullV2 wrong but Best-of-K correct count: 2
- FullV2 correct but Best-of-K wrong count: 5

## Failure modes

- only_reference_can_distinguish_posthoc: reported when non-reference signals are tied or inconclusive.
- objective_consensus_misled_selection: inspect fullv2_score_debug.csv objective columns.
- critical_structure_penalty_too_strong: inspect fullv2_critical_structure_debug.csv.
- objective_terms_not_discriminative: inspect objective-term coverage columns.
- candidate_pool_limited: compare against pass@k oracle table.
