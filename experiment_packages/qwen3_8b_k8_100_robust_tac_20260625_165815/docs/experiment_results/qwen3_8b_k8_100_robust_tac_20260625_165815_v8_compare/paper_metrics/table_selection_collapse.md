# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | Consensus only | Solver only | Consensus only; Solver only | 100 | 0.9500 | 95 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware | 100 | 0.9500 | 95 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | ReplenishVerifier-FullV2 | ReplenishVerifier-Full; ReplenishVerifier-FullV2 | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware | 100 | 0.9500 | 95 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe |  |  | 2 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-Full; ReplenishVerifier-FullV2 |  |  | 2 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=19, k1=14, k2=9, k3=19, k4=7, k5=5, k6=14, k7=13 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=14, k1=11, k2=19, k3=10, k4=9, k5=10, k6=12, k7=15 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100 |
| candidate_rank_distribution | ReplenishVerifier-ConsensusSafe |  | ReplenishVerifier-ConsensusSafe | 100 |  | 100 | k0=9, k1=13, k2=10, k3=21, k4=7, k5=10, k6=17, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=48, k1=20, k2=2, k3=19, k4=3, k5=1, k6=5, k7=2 |
| candidate_rank_distribution | ReplenishVerifier-FullV2 |  | ReplenishVerifier-FullV2 | 100 |  | 100 | k0=48, k1=20, k2=2, k3=19, k4=3, k5=1, k6=5, k7=2 |
| candidate_rank_distribution | ReplenishVerifier-HybridSafe |  | ReplenishVerifier-HybridSafe | 100 |  | 100 | k0=9, k1=13, k2=10, k3=21, k4=7, k5=10, k6=17, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=6, k1=13, k2=10, k3=21, k4=9, k5=9, k6=19, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=10, k1=20, k2=10, k3=21, k4=7, k5=9, k6=12, k7=11 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=14, k1=13, k2=16, k3=10, k4=10, k5=9, k6=14, k7=14 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=54, k1=17, k2=2, k3=16, k4=3, k5=1, k6=5, k7=2 |
