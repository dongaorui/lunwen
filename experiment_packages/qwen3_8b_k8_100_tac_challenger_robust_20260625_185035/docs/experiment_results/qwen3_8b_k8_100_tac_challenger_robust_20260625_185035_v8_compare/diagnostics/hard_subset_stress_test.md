# Hard Subset / Stress Test Diagnostics

This is post-hoc diagnostics only and must not be used for formal selection.

| hard_subset | method | n | objective_accuracy | structure_completeness | constraint_coverage | objective_term_coverage | safe_consensus_score_mean | wrong_consensus_risk_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| capacity_or_fixed_or_shortage | Consensus only | 60 | 0.8333333333333334 | 0.8107453703703703 | 0.9625 | 0.9888888888888888 | 0.7811507936507935 | 0.0 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-Full | 60 | 0.8166666666666667 | 0.8386759259259259 | 0.9833333333333333 | 1.0 | 0.7193016617063489 | 0.05073802083333331 |
| capacity_or_fixed_or_shortage | ReplenishVerifier-TypeAware-Consensus | 60 | 0.85 | 0.8381550925925925 | 0.9833333333333333 | 1.0 | 0.7281468005952377 | 0.0509206597222222 |
| capacity_or_fixed_or_shortage | Structure only | 60 | 0.8 | 0.8386759259259259 | 0.9833333333333333 | 0.9777777777777776 | 0.7429563492063492 | 0.0 |
| fixed_order_cost_big_m | Consensus only | 20 | 0.95 | 0.853 | 1.0 | 0.9666666666666666 | 0.9428571428571428 | 0.0 |
| fixed_order_cost_big_m | ReplenishVerifier-Full | 20 | 0.95 | 0.8707499999999999 | 1.0 | 1.0 | 0.9307558035714287 | 0.012101339285714247 |
| fixed_order_cost_big_m | ReplenishVerifier-TypeAware-Consensus | 20 | 1.0 | 0.8707499999999999 | 1.0 | 1.0 | 0.9246089285714287 | 0.011998214285714248 |
| fixed_order_cost_big_m | Structure only | 20 | 1.0 | 0.8707499999999999 | 1.0 | 0.9333333333333333 | 0.9366071428571429 | 0.0 |
| multi_item_capacity | Consensus only | 20 | 0.6 | 0.728125 | 0.8875 | 1.0 | 0.5782738095238095 | 0.0 |
| multi_item_capacity | ReplenishVerifier-Full | 20 | 0.55 | 0.7849999999999999 | 0.95 | 1.0 | 0.4163113839285715 | 0.1286290922619047 |
| multi_item_capacity | ReplenishVerifier-TypeAware-Consensus | 20 | 0.6 | 0.7834375 | 0.95 | 1.0 | 0.4489936755952382 | 0.12928013392857135 |
| multi_item_capacity | Structure only | 20 | 0.55 | 0.7849999999999999 | 0.95 | 1.0 | 0.5449404761904763 | 0.0 |
| other | Consensus only | 40 | 0.825 | 0.7588492063492065 | 0.8861111111111111 | 0.8083333333333332 | 0.8290178571428573 | 0.0 |
| other | ReplenishVerifier-Full | 40 | 0.85 | 0.7609325396825398 | 0.8861111111111111 | 0.7916666666666667 | 0.740060409580499 | 0.07645744756235819 |
| other | ReplenishVerifier-TypeAware-Consensus | 40 | 0.85 | 0.7609325396825398 | 0.8861111111111111 | 0.7916666666666667 | 0.740060409580499 | 0.07645744756235819 |
| other | Structure only | 40 | 0.85 | 0.7609325396825398 | 0.8861111111111111 | 0.7916666666666667 | 0.8165178571428573 | 0.0 |
| single_item_multi_period_shortage | Consensus only | 20 | 0.95 | 0.8511111111111112 | 1.0 | 1.0 | 0.8223214285714286 | 0.0 |
| single_item_multi_period_shortage | ReplenishVerifier-Full | 20 | 0.95 | 0.8602777777777776 | 1.0 | 1.0 | 0.8108377976190477 | 0.0114836309523809 |
| single_item_multi_period_shortage | ReplenishVerifier-TypeAware-Consensus | 20 | 0.95 | 0.8602777777777776 | 1.0 | 1.0 | 0.8108377976190477 | 0.0114836309523809 |
| single_item_multi_period_shortage | Structure only | 20 | 0.85 | 0.8602777777777776 | 1.0 | 1.0 | 0.7473214285714287 | 0.0 |
