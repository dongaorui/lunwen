# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | ReplenishVerifier-FullV2 | ReplenishVerifier-Full; ReplenishVerifier-FullV2 | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe |  |  | 2 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-Full; ReplenishVerifier-FullV2; Structure only |  |  | 3 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=21, k1=10, k2=1, k3=26, k4=10, k5=10, k6=11, k7=11 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=10, k1=12, k2=11, k3=17, k4=11, k5=14, k6=13, k7=12 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100 |
| candidate_rank_distribution | ReplenishVerifier-ConsensusSafe |  | ReplenishVerifier-ConsensusSafe | 100 |  | 100 | k0=9, k1=9, k2=4, k3=32, k4=12, k5=11, k6=13, k7=10 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=47, k1=17, k2=2, k3=24, k4=4, k5=3, k6=2, k7=1 |
| candidate_rank_distribution | ReplenishVerifier-FullV2 |  | ReplenishVerifier-FullV2 | 100 |  | 100 | k0=47, k1=17, k2=2, k3=24, k4=4, k5=3, k6=2, k7=1 |
| candidate_rank_distribution | ReplenishVerifier-HybridSafe |  | ReplenishVerifier-HybridSafe | 100 |  | 100 | k0=9, k1=9, k2=4, k3=32, k4=12, k5=11, k6=13, k7=10 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=9, k1=9, k2=5, k3=30, k4=12, k5=10, k6=15, k7=10 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=10, k1=13, k2=4, k3=31, k4=13, k5=12, k6=10, k7=7 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=10, k1=12, k2=12, k3=18, k4=12, k5=12, k6=14, k7=10 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=52, k1=19, k2=2, k3=20, k4=2, k5=2, k6=2, k7=1 |
