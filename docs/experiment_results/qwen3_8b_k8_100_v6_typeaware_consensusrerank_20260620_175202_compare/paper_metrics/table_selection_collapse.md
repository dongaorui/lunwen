# Table: Selection Collapse Diagnostics

| diagnostic_type | method_a | method_b | methods | n_common | same_selection_rate | count | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_same_selection_pair | Best-of-K | ReplenishVerifier-Full | Best-of-K; ReplenishVerifier-Full | 100 | 0.9500 | 95 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | Consensus only | Solver only | Consensus only; Solver only | 100 | 0.9600 | 96 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-TypeAware-Consensus | 100 | 1.0000 | 100 | Methods select the same candidate on nearly all shared problems. |
| high_same_selection_pair | ReplenishVerifier-TypeAware | ReplenishVerifier-TypeAware-Consensus | ReplenishVerifier-TypeAware; ReplenishVerifier-TypeAware-Consensus | 100 | 0.9700 | 97 | Methods select the same candidate on nearly all shared problems. |
| metric_duplicate_group |  |  | Best-of-K; Structure only |  |  | 2 | Methods have identical headline metric values. |
| metric_duplicate_group |  |  | ReplenishVerifier-ConsensusSafe; ReplenishVerifier-Full; ReplenishVerifier-TypeAware-Consensus |  |  | 3 | Methods have identical headline metric values. |
| candidate_rank_distribution | Best-of-K |  | Best-of-K | 100 |  | 100 | k0=19, k1=12, k2=14, k3=13, k4=5, k5=10, k6=16, k7=11 |
| candidate_rank_distribution | Consensus only |  | Consensus only | 100 |  | 100 | k0=3, k1=16, k2=12, k3=12, k4=8, k5=14, k6=17, k7=18 |
| candidate_rank_distribution | Direct |  | Direct | 100 |  | 100 | k0=100 |
| candidate_rank_distribution | ReplenishVerifier-ConsensusSafe |  | ReplenishVerifier-ConsensusSafe | 100 |  | 100 | k0=3, k1=17, k2=15, k3=15, k4=7, k5=11, k6=18, k7=14 |
| candidate_rank_distribution | ReplenishVerifier-Full |  | ReplenishVerifier-Full | 100 |  | 100 | k0=16, k1=14, k2=13, k3=13, k4=6, k5=10, k6=18, k7=10 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware |  | ReplenishVerifier-TypeAware | 100 |  | 100 | k0=3, k1=17, k2=15, k3=13, k4=8, k5=11, k6=20, k7=13 |
| candidate_rank_distribution | ReplenishVerifier-TypeAware-Consensus |  | ReplenishVerifier-TypeAware-Consensus | 100 |  | 100 | k0=3, k1=17, k2=15, k3=15, k4=7, k5=11, k6=18, k7=14 |
| candidate_rank_distribution | Solver only |  | Solver only | 100 |  | 100 | k0=3, k1=15, k2=13, k3=13, k4=8, k5=14, k6=15, k7=19 |
| candidate_rank_distribution | Structure only |  | Structure only | 100 |  | 100 | k0=81, k1=7, k2=5, k3=4, k6=2, k7=1 |
