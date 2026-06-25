# FullV2 vs Structure Summary

Posthoc-only diagnostics; do not use for formal selection.

- Full vs Structure same_selection_rate: 0.9200
- FullV2 vs Structure same_selection_rate: 0.9200
- FullV2 vs Full same_selection_rate: 1.0000
- FullV2 vs Best-of-K same_selection_rate: 0.4000
- Full objective_accuracy: 0.8100
- Structure objective_accuracy: 0.8100
- FullV2 objective_accuracy: 0.8100
- Best-of-K objective_accuracy: 0.7900
- FullV2 beats Structure count: 2
- Structure beats FullV2 count: 2
- Both correct count: 79
- Both wrong count: 17
- FullV2 wrong but Best-of-K correct count: 2
- FullV2 correct but Best-of-K wrong count: 4

## Failure modes

- only_reference_can_distinguish_posthoc: reported when non-reference signals are tied or inconclusive.
- objective_consensus_misled_selection: inspect fullv2_score_debug.csv objective columns.
- critical_structure_penalty_too_strong: inspect fullv2_critical_structure_debug.csv.
- objective_terms_not_discriminative: inspect objective-term coverage columns.
- candidate_pool_limited: compare against pass@k oracle table.
