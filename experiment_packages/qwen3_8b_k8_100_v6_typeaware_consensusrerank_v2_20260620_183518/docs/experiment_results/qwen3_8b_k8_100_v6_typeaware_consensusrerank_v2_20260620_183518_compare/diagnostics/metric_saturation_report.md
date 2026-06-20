# Metric Saturation Report

This report is diagnostic only and does not affect formal selection.

## Metric unique-value counts

| metric | unique_values | saturated | values |
| --- | --- | --- | --- |
| average_repair_feedback_count | 4 | False | [0.16, 0.17, 0.18, 0.19] |
| average_runtime_sec | 8 | False | [0.1031413847062504, 0.10321830591652542, 0.10332591666665394, 0.104100436787121, 0.10534032450756058, 0.11023205878969748, 0.11176597978861537, 0.11183014262875077] |
| code_validity_rate | 1 | True | [1.0] |
| constraint_coverage | 4 | False | [0.86875, 0.87, 0.8863888888888889, 0.8875] |
| executable_rate | 2 | True | [0.89, 0.91] |
| inventory_balance_accuracy | 1 | True | [1.0] |
| mean_objective_gap | 6 | False | [0.09793749807425998, 0.10560406630396485, 0.1091272807774531, 0.11291288810053687, 0.1180026845344572, 0.11902872801475164] |
| mean_relative_error | 6 | False | [0.09793749807425998, 0.10560406630396485, 0.1091272807774531, 0.11291288810053687, 0.1180026845344572, 0.11902872801475164] |
| median_objective_gap | 1 | True | [0.0] |
| median_relative_error | 1 | True | [0.0] |
| median_runtime_sec | 6 | False | [0.10591208000550978, 0.1061307304771617, 0.10687042050994933, 0.10735854299855419, 0.11110881849890575, 0.11192747150198556] |
| objective_accuracy | 5 | False | [0.69, 0.71, 0.72, 0.74, 0.76] |
| objective_accuracy_count | 5 | False | [69, 71, 72, 74, 76] |
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
| structure_completeness | 6 | False | [0.7353994047619041, 0.740297222222222, 0.7496190476190471, 0.7507777777777771, 0.7547972222222219, 0.7552257936507933] |

## Saturated metrics

code_validity_rate, executable_rate, inventory_balance_accuracy, median_objective_gap, median_relative_error, objective_accuracy_total, objective_term_coverage, objective_term_lp_coefficient_coverage, objective_term_surface_coverage, optimal_rate, solver_status_error_rate, solver_status_optimal_rate, solver_status_timeout_rate, structure_complete_count, structure_complete_total

## High-overlap method pairs

High same_selection_rate can make headline metrics identical even when method names differ.

- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-HybridSafe: same_selection_rate=1.0000
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9700
- ReplenishVerifier-ConsensusSafe / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=1.0000
- ReplenishVerifier-Full / Structure only: same_selection_rate=0.9900
- ReplenishVerifier-HybridSafe / ReplenishVerifier-TypeAware: same_selection_rate=0.9700
- ReplenishVerifier-HybridSafe / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=1.0000
- ReplenishVerifier-TypeAware / ReplenishVerifier-TypeAware-Consensus: same_selection_rate=0.9700
