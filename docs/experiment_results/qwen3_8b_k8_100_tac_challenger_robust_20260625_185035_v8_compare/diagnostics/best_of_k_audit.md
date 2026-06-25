# Best-of-K Fairness Audit

This audit checks whether formal `Best-of-K` selection uses reference/oracle fields.

- formal_best_of_k_is_no_reference: True
- n_selected_rows: 100
- uses_reference_objective_for_selection: False
- uses_objective_correct_for_selection: False
- uses_oracle_for_selection: False
- uses_reference_lp_for_selection: False
- uses_reference_answer_for_selection: False
- forbidden_component_keys: []

## Notes

Formal Best-of-K uses executable/optimal/objective-present and no-reference quality tie-breakers; objective_correct/reference fields may appear on rows only as evaluation metrics.
