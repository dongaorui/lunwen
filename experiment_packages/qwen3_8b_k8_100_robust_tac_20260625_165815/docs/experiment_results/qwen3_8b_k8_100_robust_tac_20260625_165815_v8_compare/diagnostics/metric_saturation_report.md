# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 7 | False | [0.06, 0.08, 0.21, 0.22, 0.26, 0.32, 0.33] |
| average_runtime_sec | 9 | False | [0.10805507289478555, 0.10835000263759867, 0.11827753858058714, 0.11999570040032267, 0.12047044033068233, 0.12594592943089084, 0.14063440895173698, 0.14161453537875787, 0.14195978770032525] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 6 | False | [0.8841666666666665, 0.9136111111111112, 0.9306944444444444, 0.9319444444444445, 0.9394444444444444, 0.9444444444444444] |
| executable_rate | 3 | False | [0.91, 0.93, 0.97] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 8 | False | [0.02716798195453856, 0.11373143685970537, 0.11543912375010025, 0.12041047764210727, 0.13069974205493387, 0.13385472372576399, 0.13619577736145197, 0.1432223652661633] |
| mean_relative_error | 8 | False | [0.02716798195453856, 0.11373143685970537, 0.11543912375010025, 0.12041047764210727, 0.13069974205493387, 0.13385472372576399, 0.13619577736145197, 0.1432223652661633] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 8 | False | [0.10569305595709011, 0.10705810249783099, 0.1110607900773175, 0.11124915402615443, 0.11204600153723732, 0.13012709899339825, 0.13117876049363986, 0.13704378303373232] |
| objective_accuracy | 5 | False | [0.7, 0.78, 0.82, 0.83, 0.85] |
| objective_accuracy_count | 5 | False | [70, 78, 82, 83, 85] |
| objective_accuracy_total | 1 | True | [100] |
| objective_term_coverage | 8 | False | [0.9000000000000001, 0.9033333333333334, 0.9033333333333335, 0.9100000000000001, 0.9166666666666667, 0.9233333333333333, 0.926666666666667, 0.9366666666666665] |
| objective_term_lp_coefficient_coverage | 5 | False | [0.9072164948453612, 0.9175257731958765, 0.9194139194139199, 0.9209621993127148, 0.9318996415770608] |
| objective_term_surface_coverage | 4 | False | [0.9766666666666666, 0.9866666666666666, 0.99, 1.0] |
| optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_error_rate | 3 | False | [0.03, 0.07, 0.09] |
| solver_status_infeasible_rate | 3 | False | [0.06, 0.08, 0.12] |
| solver_status_optimal_rate | 2 | True | [0.78, 0.87] |
| solver_status_timeout_rate | 1 | True | [0.0] |
| structure_complete_count | 1 | True | [0] |
| structure_complete_total | 1 | True | [100] |
| structure_completeness | 8 | False | [0.7489063492063489, 0.7805994047619054, 0.7889930555555553, 0.7905763888888887, 0.803203571428572, 0.8067105158730163, 0.8072660714285721, 0.807578571428572] |

## Saturated metrics

code_validity_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, optimal_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- Consensus only / Solver only: same_selection_rate=0.9500
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-HybridSafe: same_selection_rate=1.0000
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9500
- ReplenishVerifier-Full / ReplenishVerifier-FullV2: same_selection_rate=1.0000
- ReplenishVerifier-HybridSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9500
