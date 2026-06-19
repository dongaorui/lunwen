# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 3 | False | [0.16, 0.17, 0.18] |
| average_runtime_sec | 7 | False | [0.07608910176961217, 0.07614052371995057, 0.07634471278230194, 0.07737329612253234, 0.08137403486820403, 0.08220312194782309, 0.08226511004788335] |
| code_validity_rate | 2 | True | [0.99, 1.0] |
| constraint_coverage | 3 | False | [0.86875, 0.87, 0.8875] |
| executable_rate | 2 | True | [0.89, 0.91] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 6 | False | [0.08419267882517033, 0.09824885987056085, 0.09885670705514639, 0.10560406630396485, 0.11291288810053687, 0.11902872801475164] |
| mean_relative_error | 6 | False | [0.08419267882517033, 0.09824885987056085, 0.09885670705514639, 0.10560406630396485, 0.11291288810053687, 0.11902872801475164] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 6 | False | [0.07607361351256259, 0.07608360701124184, 0.07618108001770452, 0.07646371147711761, 0.08138560599763878, 0.08142478950321674] |
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
| structure_completeness | 4 | False | [0.7353994047619041, 0.740297222222222, 0.7508801587301582, 0.7552257936507933] |

## Saturated metrics

code_validity_rate, executable_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, objective_term_coverage, objective_term_lp_coefficient_coverage, objective_term_surface_coverage, optimal_rate, solver_status_error_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- Consensus only / Solver only: same_selection_rate=0.9700
- ReplenishVerifier-Full / Structure only: same_selection_rate=0.9900
- ReplenishVerifier-TypeAware / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=1.0000
