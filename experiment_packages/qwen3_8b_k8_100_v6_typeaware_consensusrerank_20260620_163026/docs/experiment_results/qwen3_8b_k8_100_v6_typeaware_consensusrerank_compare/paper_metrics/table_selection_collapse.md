# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | Consensus only | Solver only | Consensus only; Solver only | 100 | 0.9600 | 96 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | Structure only | ReplenishVerifier-Full; Structure only | 100 | 0.9900 | 99 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-TypeAware | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-TypeAware; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | ReplenishVerifier-Full; Structure only |  |  | 2 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-TypeAware; ReplenishVerifier-TypeAware-Consensus |  |  | 2 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=25, k1=8, k2=14, k3=11, k4=8, k5=9, k6=13, k7=12 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=14, k1=9, k2=16, k3=11, k4=11, k5=12, k6=13, k7=14 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=80, k1=8, k2=5, k3=4, k6=2, k7=1 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=13, k1=10, k2=18, k3=11, k4=11, k5=8, k6=16, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=13, k1=10, k2=18, k3=11, k4=11, k5=8, k6=16, k7=13 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=14, k1=9, k2=16, k3=11, k4=12, k5=13, k6=13, k7=12 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=81, k1=7, k2=5, k3=4, k6=2, k7=1 |
