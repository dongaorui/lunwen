# Table: Hard Subset / Stress Test Metrics

| hard_subset | method | n | objective_accuracy | structure_completeness | constraint_coverage | objective_term_coverage | safe_consensus_score_mean | wrong_consensus_risk_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| capacity_or_fixed_or_shortage | Best-of-K | 60 | 0.7500 | 0.8314 | 0.9750 | 0.9944 | 0.7331 | 0.0000 |
| capacity_or_fixed_or_shortage | Consensus only | 60 | 0.8333 | 0.8107 | 0.9625 | 0.9889 | 0.7812 | 0.0000 |
| capacity_or_fixed_or_shortage | Direct | 60 | 0.6500 | 0.7824 | 0.9292 | 0.9556 | 0.6226 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-ConsensusSafe | 60 | 0.8333 | 0.8382 | 0.9833 | 1.0000 | 0.7812 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-Full | 60 | 0.8167 | 0.8387 | 0.9833 | 1.0000 | 0.7193 | 0.0507 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-FullV2 | 60 | 0.8167 | 0.8387 | 0.9833 | 1.0000 | 0.7700 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-HybridSafe | 60 | 0.8333 | 0.8382 | 0.9833 | 1.0000 | 0.7812 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-TypeAware | 60 | 0.8333 | 0.8132 | 0.9542 | 1.0000 | 0.7812 | 0.0000 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-TypeAware-Consensus | 60 | 0.8500 | 0.8382 | 0.9833 | 1.0000 | 0.7281 | 0.0509 |
| fixed_order_cost_big_m | Best-of-K | 20 | 1.0000 | 0.8707 | 1.0000 | 0.9833 | 0.9366 | 0.0000 |
| fixed_order_cost_big_m | Consensus only | 20 | 0.9500 | 0.8538 | 1.0000 | 0.9667 | 0.9429 | 0.0000 |
| fixed_order_cost_big_m | Direct | 20 | 0.9500 | 0.8060 | 0.9500 | 0.8667 | 0.8866 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-ConsensusSafe | 20 | 0.9500 | 0.8707 | 1.0000 | 1.0000 | 0.9429 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-Full | 20 | 0.9500 | 0.8707 | 1.0000 | 1.0000 | 0.9308 | 0.0121 |
| fixed_order_cost_big_m | ReplenishVerifier-FullV2 | 20 | 0.9500 | 0.8707 | 1.0000 | 1.0000 | 0.9429 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-HybridSafe | 20 | 0.9500 | 0.8707 | 1.0000 | 1.0000 | 0.9429 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-TypeAware | 20 | 0.9500 | 0.8707 | 1.0000 | 1.0000 | 0.9429 | 0.0000 |
| fixed_order_cost_big_m | ReplenishVerifier-TypeAware-Consensus | 20 | 1.0000 | 0.8707 | 1.0000 | 1.0000 | 0.9246 | 0.0120 |
| multi_item_capacity | Best-of-K | 20 | 0.5000 | 0.7631 | 0.9250 | 1.0000 | 0.5092 | 0.0000 |
| multi_item_capacity | Consensus only | 20 | 0.6000 | 0.7281 | 0.8875 | 1.0000 | 0.5783 | 0.0000 |
| multi_item_capacity | Direct | 20 | 0.4500 | 0.6875 | 0.8375 | 1.0000 | 0.4366 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-ConsensusSafe | 20 | 0.6000 | 0.7834 | 0.9500 | 1.0000 | 0.5783 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-Full | 20 | 0.5500 | 0.7850 | 0.9500 | 1.0000 | 0.4163 | 0.1286 |
| multi_item_capacity | ReplenishVerifier-FullV2 | 20 | 0.5500 | 0.7850 | 0.9500 | 1.0000 | 0.5449 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-HybridSafe | 20 | 0.6000 | 0.7834 | 0.9500 | 1.0000 | 0.5783 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-TypeAware | 20 | 0.6000 | 0.7084 | 0.8625 | 1.0000 | 0.5783 | 0.0000 |
| multi_item_capacity | ReplenishVerifier-TypeAware-Consensus | 20 | 0.6000 | 0.7834 | 0.9500 | 1.0000 | 0.4490 | 0.1293 |
| other | Best-of-K | 40 | 0.8500 | 0.7609 | 0.8861 | 0.7792 | 0.8165 | 0.0000 |
| other | Consensus only | 40 | 0.8250 | 0.7578 | 0.8861 | 0.7958 | 0.8290 | 0.0000 |
| other | Direct | 40 | 0.7750 | 0.6987 | 0.8167 | 0.8833 | 0.7540 | 0.0000 |
| other | ReplenishVerifier-ConsensusSafe | 40 | 0.8250 | 0.7595 | 0.8861 | 0.8083 | 0.8290 | 0.0000 |
| other | ReplenishVerifier-Full | 40 | 0.8500 | 0.7609 | 0.8861 | 0.7917 | 0.7401 | 0.0765 |
| other | ReplenishVerifier-FullV2 | 40 | 0.8500 | 0.7609 | 0.8861 | 0.7917 | 0.8165 | 0.0000 |
| other | ReplenishVerifier-HybridSafe | 40 | 0.8250 | 0.7595 | 0.8861 | 0.8083 | 0.8290 | 0.0000 |
| other | ReplenishVerifier-TypeAware | 40 | 0.8250 | 0.7318 | 0.8528 | 0.8417 | 0.8290 | 0.0000 |
| other | ReplenishVerifier-TypeAware-Consensus | 40 | 0.8500 | 0.7609 | 0.8861 | 0.7917 | 0.7401 | 0.0765 |
| single_item_multi_period_shortage | Best-of-K | 20 | 0.7500 | 0.8603 | 1.0000 | 1.0000 | 0.7536 | 0.0000 |
| single_item_multi_period_shortage | Consensus only | 20 | 0.9500 | 0.8503 | 1.0000 | 1.0000 | 0.8223 | 0.0000 |
| single_item_multi_period_shortage | Direct | 20 | 0.5500 | 0.8536 | 1.0000 | 1.0000 | 0.5446 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-ConsensusSafe | 20 | 0.9500 | 0.8603 | 1.0000 | 1.0000 | 0.8223 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-Full | 20 | 0.9500 | 0.8603 | 1.0000 | 1.0000 | 0.8108 | 0.0115 |
| single_item_multi_period_shortage | ReplenishVerifier-FullV2 | 20 | 0.9500 | 0.8603 | 1.0000 | 1.0000 | 0.8223 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-HybridSafe | 20 | 0.9500 | 0.8603 | 1.0000 | 1.0000 | 0.8223 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-TypeAware | 20 | 0.9500 | 0.8603 | 1.0000 | 1.0000 | 0.8223 | 0.0000 |
| single_item_multi_period_shortage | ReplenishVerifier-TypeAware-Consensus | 20 | 0.9500 | 0.8603 | 1.0000 | 1.0000 | 0.8108 | 0.0115 |
