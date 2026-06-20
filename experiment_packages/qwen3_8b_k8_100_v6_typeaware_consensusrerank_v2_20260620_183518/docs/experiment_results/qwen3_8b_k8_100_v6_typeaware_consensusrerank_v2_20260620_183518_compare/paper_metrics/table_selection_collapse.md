# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | Structure only | ReplenishVerifier-Full; Structure only | 100 | 0.9900 | 99 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-TypeAware | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-TypeAware; ReplenishVerifier-TypeAware-Consensus | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware-Consensus |  |  | 3 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-Full; Structure only |  |  | 2 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=28, k1=11, k2=10, k3=12, k4=13, k5=8, k6=9, k7=9 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=19, k1=13, k2=11, k3=14, k4=14, k5=7, k6=8, k7=14 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100 |
| candidate_rank_distribution | ReplenishVerifier-ConsensusSafe |  | ReplenishVerifier-ConsensusSafe | 100 |  | 100 | k0=15, k1=12, k2=13, k3=15, k4=15, k5=7, k6=10, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=80, k1=8, k2=5, k3=4, k6=2, k7=1 |
| candidate_rank_distribution | ReplenishVerifier-HybridSafe |  | ReplenishVerifier-HybridSafe | 100 |  | 100 | k0=15, k1=12, k2=13, k3=15, k4=15, k5=7, k6=10, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=15, k1=13, k2=13, k3=14, k4=15, k5=7, k6=11, k7=12 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=15, k1=12, k2=13, k3=15, k4=15, k5=7, k6=10, k7=13 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=18, k1=12, k2=12, k3=16, k4=14, k5=7, k6=8, k7=13 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=81, k1=7, k2=5, k3=4, k6=2, k7=1 |
