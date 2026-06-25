# Table: Paired Method Comparison

| target_method | baseline_method | n_common | objective_win_count | objective_loss_count | objective_tie_count | structure_win_count | structure_loss_count | structure_tie_count | missing_capacity_reduction_count | missing_capacity_increase_count | objective_mismatch_reduction_count | objective_mismatch_increase_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ReplenishVerifier-TypeAware-Consensus | Direct | 100 | 16 | 2 | 82 | 44 | 0 | 56 | 12 | 1 | 16 | 2 |
| ReplenishVerifier-TypeAware-Consensus | Best-of-K | 100 | 2 | 2 | 96 | 5 | 1 | 94 | 5 | 0 | 2 | 2 |
| ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-Full | 100 | 2 | 2 | 96 | 0 | 1 | 99 | 0 | 0 | 2 | 2 |
