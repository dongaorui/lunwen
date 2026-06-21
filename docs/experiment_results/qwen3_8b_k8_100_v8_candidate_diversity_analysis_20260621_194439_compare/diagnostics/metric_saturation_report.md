# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 6 | False | [0.06, 0.08, 0.21, 0.22, 0.26, 0.32] |
| average_runtime_sec | 8 | False | [0.09791823292151093, 0.09806360026123002, 0.09952404345560353, 0.1008856815751642, 0.10094159828033299, 0.102299042812665, 0.10508136263815686, 0.1051750386581989] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 5 | False | [0.8841666666666665, 0.9136111111111112, 0.9319444444444445, 0.9394444444444444, 0.9444444444444444] |
| executable_rate | 3 | False | [0.91, 0.93, 0.97] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 7 | False | [0.02521487350406109, 0.12019787827543556, 0.12086552290781873, 0.13069974205493387, 0.13672429613082127, 0.1432223652661633, 0.1461869405077073] |
| mean_relative_error | 7 | False | [0.02521487350406109, 0.12019787827543556, 0.12086552290781873, 0.13069974205493387, 0.13672429613082127, 0.1432223652661633, 0.1461869405077073] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 6 | False | [0.09853669352014549, 0.09973695399821736, 0.10000160700292327, 0.10413932148367167, 0.10552951347199269, 0.10587692647823133] |
| objective_accuracy | 5 | False | [0.7, 0.78, 0.79, 0.82, 0.83] |
| objective_accuracy_count | 5 | False | [70, 78, 79, 82, 83] |
| objective_accuracy_total | 1 | True | [100] |
| objective_term_coverage | 8 | False | [0.8966666666666668, 0.9033333333333334, 0.9033333333333335, 0.9133333333333334, 0.9166666666666667, 0.9233333333333333, 0.926666666666667, 0.9366666666666665] |
| objective_term_lp_coefficient_coverage | 6 | False | [0.9072164948453612, 0.9106529209621994, 0.9140893470790379, 0.9194139194139199, 0.9209621993127148, 0.9318996415770608] |
| objective_term_surface_coverage | 5 | False | [0.9766666666666666, 0.9833333333333333, 0.9866666666666666, 0.9933333333333333, 1.0] |
| optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_error_rate | 3 | False | [0.03, 0.07, 0.09] |
| solver_status_infeasible_rate | 3 | False | [0.06, 0.08, 0.12] |
| solver_status_optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_timeout_rate | 1 | True | [0.0] |
| structure_complete_count | 1 | True | [0] |
| structure_complete_total | 1 | True | [100] |
| structure_completeness | 7 | False | [0.7489063492063489, 0.7805994047619054, 0.7898051587301583, 0.7904003968253965, 0.803203571428572, 0.8067105158730163, 0.807578571428572] |

## Saturated metrics

code_validity_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, optimal_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-HybridSafe: same_selection_rate=1.0000
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=1.0000
- ReplenishVerifier-Full / ReplenishVerifier-FullV2: same_selection_rate=1.0000
- ReplenishVerifier-Full / Structure only: same_selection_rate=0.9600
- ReplenishVerifier-FullV2 / Structure only: same_selection_rate=0.9600
- ReplenishVerifier-HybridSafe / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=1.0000
