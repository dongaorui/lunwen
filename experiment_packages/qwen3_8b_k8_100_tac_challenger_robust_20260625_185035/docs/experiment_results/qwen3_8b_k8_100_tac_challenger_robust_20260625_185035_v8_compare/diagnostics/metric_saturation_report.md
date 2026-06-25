# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 6 | False | [0.06, 0.08, 0.21, 0.22, 0.26, 0.32] |
| average_runtime_sec | 9 | False | [0.10117242488195188, 0.10131179983029143, 0.1021149460261222, 0.10352442296687514, 0.10378406454226934, 0.10420069123967551, 0.10505465658614412, 0.10728065829141997, 0.10730774380150251] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 5 | False | [0.8841666666666665, 0.9136111111111112, 0.9319444444444445, 0.9394444444444444, 0.9444444444444444] |
| executable_rate | 3 | False | [0.91, 0.93, 0.97] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 9 | False | [0.02716798195453856, 0.11539140538885227, 0.11543912375010025, 0.12171229196279001, 0.12207044617125418, 0.12693941315575316, 0.13069974205493387, 0.1432223652661633, 0.1545558033671928] |
| mean_relative_error | 9 | False | [0.02716798195453856, 0.11539140538885227, 0.11543912375010025, 0.12171229196279001, 0.12207044617125418, 0.12693941315575316, 0.13069974205493387, 0.1432223652661633, 0.1545558033671928] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 8 | False | [0.10151429648976773, 0.1016090500052087, 0.10323109349701554, 0.10389498702716082, 0.10409268853254616, 0.10437650646781549, 0.10721609852043912, 0.10795338894240558] |
| objective_accuracy | 6 | False | [0.7, 0.8, 0.81, 0.82, 0.83, 0.85] |
| objective_accuracy_count | 6 | False | [70, 80, 81, 82, 83, 85] |
| objective_accuracy_total | 1 | True | [100] |
| objective_term_coverage | 6 | False | [0.9033333333333334, 0.9033333333333335, 0.9166666666666667, 0.9233333333333333, 0.926666666666667, 0.9366666666666665] |
| objective_term_lp_coefficient_coverage | 5 | False | [0.9072164948453612, 0.914089347079038, 0.9194139194139199, 0.9209621993127148, 0.9318996415770608] |
| objective_term_surface_coverage | 4 | False | [0.97, 0.9833333333333333, 0.9866666666666666, 1.0] |
| optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_error_rate | 3 | False | [0.03, 0.07, 0.09] |
| solver_status_infeasible_rate | 3 | False | [0.06, 0.08, 0.12] |
| solver_status_optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_timeout_rate | 1 | True | [0.0] |
| structure_complete_count | 1 | True | [0] |
| structure_complete_total | 1 | True | [100] |
| structure_completeness | 8 | False | [0.7489063492063489, 0.7805994047619054, 0.7899869047619044, 0.7900813492063488, 0.803203571428572, 0.8067105158730163, 0.8072660714285721, 0.807578571428572] |

## Saturated metrics

code_validity_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, optimal_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-HybridSafe: same_selection_rate=1.0000
- ReplenishVerifier-Full / ReplenishVerifier-FullV2: same_selection_rate=1.0000
