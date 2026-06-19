# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | Consensus only | Solver only | Consensus only; Solver only | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | Structure only | ReplenishVerifier-Full; Structure only | 100 | 0.9900 | 99 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-TypeAware | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-TypeAware; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | ReplenishVerifier-Full; Structure only |  |  | 2 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-TypeAware; ReplenishVerifier-TypeAware-Consensus |  |  | 2 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=23, k1=15, k2=13, k3=12, k_ge_4=37 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=9, k1=18, k2=14, k3=12, k_ge_4=47 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100, k1=0, k2=0, k3=0, k_ge_4=0 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=80, k1=8, k2=5, k3=4, k_ge_4=3 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=7, k1=18, k2=18, k3=13, k_ge_4=44 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=7, k1=18, k2=18, k3=13, k_ge_4=44 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=9, k1=18, k2=14, k3=13, k_ge_4=46 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=81, k1=7, k2=5, k3=4, k_ge_4=3 |
