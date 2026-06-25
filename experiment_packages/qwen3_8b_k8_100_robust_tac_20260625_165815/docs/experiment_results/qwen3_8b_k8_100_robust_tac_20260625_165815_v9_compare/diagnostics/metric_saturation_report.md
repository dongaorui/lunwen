# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 5 | False | [0.06, 0.07, 0.19, 0.24, 0.29] |
| average_runtime_sec | 9 | False | [0.09944188429042697, 0.09957587540848181, 0.10094614791683852, 0.10177593609900214, 0.10236328626400791, 0.10250259555876255, 0.10707269012462348, 0.10862598038627766, 0.10895004399353639] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 5 | False | [0.8708333333333332, 0.9258333333333333, 0.9354166666666666, 0.9416666666666665, 0.9479166666666665] |
| executable_rate | 3 | False | [0.9, 0.94, 0.97] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 8 | False | [0.06909311975255193, 0.14746602743650278, 0.152981575186416, 0.15673177466999227, 0.15701977638922446, 0.16103655740803302, 0.16472504985684194, 0.1735049389666212] |
| mean_relative_error | 8 | False | [0.06909311975255193, 0.14746602743650278, 0.152981575186416, 0.15673177466999227, 0.15701977638922446, 0.16103655740803302, 0.16472504985684194, 0.1735049389666212] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 8 | False | [0.0990518419421278, 0.09936232049949467, 0.10093744995538145, 0.1013204600312747, 0.10164860700024292, 0.1077087220037356, 0.10771834047045559, 0.10784664651146159] |
| objective_accuracy | 4 | False | [0.67, 0.78, 0.8, 0.81] |
| objective_accuracy_count | 4 | False | [67, 78, 80, 81] |
| objective_accuracy_total | 1 | True | [100] |
| objective_term_coverage | 7 | False | [0.9066666666666668, 0.9133333333333337, 0.9166666666666667, 0.92, 0.9233333333333333, 0.9266666666666665, 0.94] |
| objective_term_lp_coefficient_coverage | 5 | False | [0.9037037037037041, 0.9106529209621995, 0.9209621993127148, 0.9243986254295533, 0.9361702127659575] |
| objective_term_surface_coverage | 2 | True | [0.9866666666666666, 1.0] |
| optimal_rate | 2 | True | [0.77, 0.87] |
| solver_status_error_rate | 3 | False | [0.03, 0.06, 0.1] |
| solver_status_infeasible_rate | 3 | False | [0.07, 0.08, 0.12] |
| solver_status_optimal_rate | 2 | True | [0.77, 0.87] |
| solver_status_timeout_rate | 1 | True | [0.0] |
| structure_complete_count | 1 | True | [0] |
| structure_complete_total | 1 | True | [100] |
| structure_completeness | 8 | False | [0.7374920634920632, 0.7898369047619052, 0.7920624999999997, 0.7925767857142855, 0.8041702380952386, 0.8081355158730164, 0.8086910714285719, 0.8088577380952385] |

## Saturated metrics

code_validity_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, objective_term_surface_coverage, optimal_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- Consensus only / Solver only: same_selection_rate=0.9600
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-HybridSafe: same_selection_rate=1.0000
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9700
- ReplenishVerifier-Full / ReplenishVerifier-FullV2: same_selection_rate=1.0000
- ReplenishVerifier-HybridSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9700
