# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 6 | False | [0.06, 0.08, 0.21, 0.22, 0.26, 0.32] |
| average_runtime_sec | 9 | False | [0.10236309448024258, 0.10264730123220943, 0.10347915715770796, 0.1049287864274811, 0.10509241259191185, 0.1065681694552768, 0.10710286528454162, 0.1098520498489961, 0.1107699555112049] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 5 | False | [0.8841666666666665, 0.9136111111111112, 0.9319444444444445, 0.9394444444444444, 0.9444444444444444] |
| executable_rate | 3 | False | [0.91, 0.93, 0.97] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 8 | False | [0.02716798195453856, 0.11539140538885227, 0.11543912375010025, 0.12207044617125418, 0.13069974205493387, 0.1432223652661633, 0.1490602381285941, 0.1625847721523761] |
| mean_relative_error | 8 | False | [0.02716798195453856, 0.11539140538885227, 0.11543912375010025, 0.12207044617125418, 0.13069974205493387, 0.1432223652661633, 0.1490602381285941, 0.1625847721523761] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 8 | False | [0.1026707190903835, 0.10396647354355082, 0.10548981104511768, 0.1068684309720993, 0.10707192355766892, 0.10812218202045187, 0.10921559104463086, 0.10967037605587393] |
| objective_accuracy | 6 | False | [0.7, 0.77, 0.79, 0.82, 0.83, 0.85] |
| objective_accuracy_count | 6 | False | [70, 77, 79, 82, 83, 85] |
| objective_accuracy_total | 1 | True | [100] |
| objective_term_coverage | 7 | False | [0.9033333333333335, 0.9083333333333334, 0.9116666666666667, 0.9166666666666667, 0.9233333333333333, 0.926666666666667, 0.9366666666666665] |
| objective_term_lp_coefficient_coverage | 6 | False | [0.9072164948453612, 0.914089347079038, 0.9175257731958765, 0.9194139194139199, 0.9209621993127148, 0.9318996415770608] |
| objective_term_surface_coverage | 4 | False | [0.9816666666666666, 0.9866666666666666, 0.995, 1.0] |
| optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_error_rate | 3 | False | [0.03, 0.07, 0.09] |
| solver_status_infeasible_rate | 3 | False | [0.06, 0.08, 0.12] |
| solver_status_optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_timeout_rate | 1 | True | [0.0] |
| structure_complete_count | 1 | True | [0] |
| structure_complete_total | 1 | True | [100] |
| structure_completeness | 8 | False | [0.7489063492063489, 0.7805994047619054, 0.7895416666666661, 0.7898107142857139, 0.803203571428572, 0.8067105158730163, 0.8072660714285721, 0.807578571428572] |

## Saturated metrics

code_validity_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, optimal_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-HybridSafe: same_selection_rate=1.0000
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9500
- ReplenishVerifier-Full / ReplenishVerifier-FullV2: same_selection_rate=1.0000
- ReplenishVerifier-HybridSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9500
