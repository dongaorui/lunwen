# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | ReplenishVerifier-FullV2 | ReplenishVerifier-Full; ReplenishVerifier-FullV2 | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-Full | Structure only | ReplenishVerifier-Full; Structure only | 100 | 0.9600 | 96 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-FullV2 | Structure only | ReplenishVerifier-FullV2; Structure only | 100 | 0.9600 | 96 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-HybridSafe; ReplenishVerifier-TypeAware-Consensus |  |  | 3 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-Full; ReplenishVerifier-FullV2; Structure only |  |  | 3 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=18, k1=13, k2=8, k3=20, k4=12, k6=17, k7=12 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=11, k1=10, k2=14, k3=14, k4=14, k5=6, k6=19, k7=12 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100 |
| candidate_rank_distribution | ReplenishVerifier-ConsensusSafe |  | ReplenishVerifier-ConsensusSafe | 100 |  | 100 | k0=8, k1=16, k2=8, k3=26, k4=8, k5=4, k6=19, k7=11 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=51, k1=19, k2=2, k3=17, k4=3, k5=1, k6=5, k7=2 |
| candidate_rank_distribution | ReplenishVerifier-FullV2 |  | ReplenishVerifier-FullV2 | 100 |  | 100 | k0=51, k1=19, k2=2, k3=17, k4=3, k5=1, k6=5, k7=2 |
| candidate_rank_distribution | ReplenishVerifier-HybridSafe |  | ReplenishVerifier-HybridSafe | 100 |  | 100 | k0=8, k1=16, k2=8, k3=26, k4=8, k5=4, k6=19, k7=11 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=7, k1=15, k2=9, k3=25, k4=9, k5=4, k6=20, k7=11 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=8, k1=16, k2=8, k3=26, k4=8, k5=4, k6=19, k7=11 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=12, k1=11, k2=13, k3=13, k4=16, k5=7, k6=17, k7=11 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=54, k1=17, k2=2, k3=16, k4=3, k5=1, k6=5, k7=2 |
