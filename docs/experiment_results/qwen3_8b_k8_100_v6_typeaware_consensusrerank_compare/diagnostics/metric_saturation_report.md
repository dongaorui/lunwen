# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 3 | False | [0.16, 0.17, 0.18] |
| average_runtime_sec | 7 | False | [0.08017485634947662, 0.080341006880044, 0.08037188921764027, 0.08140620609628968, 0.08467722187866457, 0.08544953194912523, 0.0855314682185417] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 3 | False | [0.86875, 0.87, 0.8875] |
| executable_rate | 2 | True | [0.89, 0.91] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 6 | False | [0.07471643562626562, 0.08833053002267295, 0.09885670705514639, 0.10560406630396485, 0.11291288810053687, 0.11902872801475164] |
| mean_relative_error | 6 | False | [0.07471643562626562, 0.08833053002267295, 0.09885670705514639, 0.10560406630396485, 0.11291288810053687, 0.11902872801475164] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 5 | False | [0.08023024146677926, 0.08036095747957006, 0.08159820700529963, 0.08573452447308227, 0.08622193548944779] |
| objective_accuracy | 5 | False | [0.69, 0.72, 0.73, 0.74, 0.75] |
| objective_accuracy_count | 5 | False | [69, 72, 73, 74, 75] |
| objective_accuracy_total | 1 | True | [100] |
| objective_term_coverage | 1 | True | [0.9466666666666665] |
| objective_term_lp_coefficient_coverage | 2 | True | [0.9513108614232209, 0.9523809523809523] |
| objective_term_surface_coverage | 1 | True | [0.98] |
| optimal_rate | 2 | True | [0.81, 0.85] |
| solver_status_error_rate | 2 | True | [0.09, 0.11] |
| solver_status_infeasible_rate | 3 | False | [0.04, 0.06, 0.08] |
| solver_status_optimal_rate | 2 | True | [0.81, 0.85] |
| solver_status_timeout_rate | 1 | True | [0.0] |
| structure_complete_count | 1 | True | [0] |
| structure_complete_total | 1 | True | [100] |
| structure_completeness | 5 | False | [0.7353994047619041, 0.740297222222222, 0.7508309523809519, 0.750894444444444, 0.7552257936507933] |

## Saturated metrics

code_validity_rate, executable_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, objective_term_coverage, objective_term_lp_coefficient_coverage, objective_term_surface_coverage, optimal_rate, solver_status_error_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- Consensus only / Solver only: same_selection_rate=0.9600
- ReplenishVerifier-Full / Structure only: same_selection_rate=0.9900
- ReplenishVerifier-TypeAware / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=1.0000
