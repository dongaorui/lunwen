# Table: Hard Subset / Stress Test Metrics

| hard_subset | method | n | objective_accuracy | structure_completeness | constraint_coverage | objective_term_coverage | safe_consensus_score_mean | wrong_consensus_risk_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| capacity_or_fixed_or_shortage | Best-of-K | 60 | 0.8000 | 0.8302 | 0.9750 | 0.9944 | 0.7407 | 0.0000 |
| capacity_or_fixed_or_shortage | Consensus only | 60 | 0.8000 | 0.8126 | 0.9646 | 0.9944 | 0.7666 | 0.0000 |
| capacity_or_fixed_or_shortage | Direct | 60 | 0.5833 | 0.7401 | 0.8792 | 0.9556 | 0.5657 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-ConsensusSafe | 60 | 0.8000 | 0.8378 | 0.9854 | 1.0000 | 0.7666 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-Full | 60 | 0.7833 | 0.8380 | 0.9854 | 1.0000 | 0.7040 | 0.0507 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-FullV2 | 60 | 0.7833 | 0.8380 | 0.9854 | 1.0000 | 0.7547 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-HybridSafe | 60 | 0.8000 | 0.8378 | 0.9854 | 1.0000 | 0.7666 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-TypeAware | 60 | 0.8000 | 0.8258 | 0.9708 | 1.0000 | 0.7666 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-TypeAware-Consensus | 60 | 0.8000 | 0.8378 | 0.9854 | 1.0000 | 0.6963 | 0.0506 |
| fixed_order_cost_big_m | Best-of-K | 20 | 1.0000 | 0.8710 | 1.0000 | 0.9833 | 0.9042 | 0.0000 |
| fixed_order_cost_big_m | Consensus only | 20 | 0.9500 | 0.8515 | 1.0000 | 0.9833 | 0.9256 | 0.0000 |
| fixed_order_cost_big_m | Direct | 20 | 0.7500 | 0.6800 | 0.8000 | 0.8667 | 0.7149 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-ConsensusSafe | 20 | 0.9500 | 0.8710 | 1.0000 | 1.0000 | 0.9256 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-Full | 20 | 0.9500 | 0.8710 | 1.0000 | 1.0000 | 0.9137 | 0.0119 |
| fixed_order_cost_big_m | ReplenishVerifier-FullV2 | 20 | 0.9500 | 0.8710 | 1.0000 | 1.0000 | 0.9256 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-HybridSafe | 20 | 0.9500 | 0.8710 | 1.0000 | 1.0000 | 0.9256 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-TypeAware | 20 | 0.9500 | 0.8710 | 1.0000 | 1.0000 | 0.9256 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-TypeAware-Consensus | 20 | 0.9500 | 0.8710 | 1.0000 | 1.0000 | 0.8556 | 0.0111 |
| multi_item_capacity | Best-of-K | 20 | 0.5500 | 0.7594 | 0.9250 | 1.0000 | 0.5804 | 0.0000 |
| multi_item_capacity | Consensus only | 20 | 0.5500 | 0.7328 | 0.8938 | 1.0000 | 0.5804 | 0.0000 |
| multi_item_capacity | Direct | 20 | 0.5500 | 0.6875 | 0.8375 | 1.0000 | 0.5304 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-ConsensusSafe | 20 | 0.5500 | 0.7828 | 0.9563 | 1.0000 | 0.5804 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-Full | 20 | 0.5500 | 0.7828 | 0.9563 | 1.0000 | 0.4508 | 0.1295 |
| multi_item_capacity | ReplenishVerifier-FullV2 | 20 | 0.5500 | 0.7828 | 0.9563 | 1.0000 | 0.5804 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-HybridSafe | 20 | 0.5500 | 0.7828 | 0.9563 | 1.0000 | 0.5804 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-TypeAware | 20 | 0.5500 | 0.7469 | 0.9125 | 1.0000 | 0.5804 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-TypeAware-Consensus | 20 | 0.5500 | 0.7828 | 0.9563 | 1.0000 | 0.4508 | 0.1295 |
| other | Best-of-K | 40 | 0.8250 | 0.7651 | 0.8917 | 0.8000 | 0.8089 | 0.0000 |
| other | Consensus only | 40 | 0.8000 | 0.7625 | 0.8917 | 0.8167 | 0.8152 | 0.0000 |
| other | Direct | 40 | 0.8000 | 0.7336 | 0.8583 | 0.8500 | 0.7902 | 0.0000 |
| other | ReplenishVerifier-ConsensusSafe | 40 | 0.8000 | 0.7637 | 0.8917 | 0.8167 | 0.8152 | 0.0000 |
| other | ReplenishVerifier-Full | 40 | 0.8500 | 0.7651 | 0.8917 | 0.8000 | 0.7371 | 0.0718 |
| other | ReplenishVerifier-FullV2 | 40 | 0.8500 | 0.7651 | 0.8917 | 0.8000 | 0.8089 | 0.0000 |
| other | ReplenishVerifier-HybridSafe | 40 | 0.8000 | 0.7637 | 0.8917 | 0.8167 | 0.8152 | 0.0000 |
| other | ReplenishVerifier-TypeAware | 40 | 0.8000 | 0.7359 | 0.8583 | 0.8500 | 0.8152 | 0.0000 |
| other | ReplenishVerifier-TypeAware-Consensus | 40 | 0.8250 | 0.7651 | 0.8917 | 0.8000 | 0.7371 | 0.0718 |
| single_item_multi_period_shortage | Best-of-K | 20 | 0.8500 | 0.8603 | 1.0000 | 1.0000 | 0.7375 | 0.0000 |
| single_item_multi_period_shortage | Consensus only | 20 | 0.9000 | 0.8536 | 1.0000 | 1.0000 | 0.7937 | 0.0000 |
| single_item_multi_period_shortage | Direct | 20 | 0.4500 | 0.8528 | 1.0000 | 1.0000 | 0.4518 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-ConsensusSafe | 20 | 0.9000 | 0.8594 | 1.0000 | 1.0000 | 0.7937 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-Full | 20 | 0.8500 | 0.8603 | 1.0000 | 1.0000 | 0.7474 | 0.0106 |
| single_item_multi_period_shortage | ReplenishVerifier-FullV2 | 20 | 0.8500 | 0.8603 | 1.0000 | 1.0000 | 0.7580 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-HybridSafe | 20 | 0.9000 | 0.8594 | 1.0000 | 1.0000 | 0.7937 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-TypeAware | 20 | 0.9000 | 0.8594 | 1.0000 | 1.0000 | 0.7937 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-TypeAware-Consensus | 20 | 0.9000 | 0.8594 | 1.0000 | 1.0000 | 0.7826 | 0.0112 |
