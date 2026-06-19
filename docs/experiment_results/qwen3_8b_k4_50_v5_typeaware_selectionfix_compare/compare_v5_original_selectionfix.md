# v5 Original vs v5 SelectionFix Comparison

This report compares the original v5 TypeAware experiment with the selection/reporting/diagnostics-fixed version.

| method | metric | v5_original | v5_selectionfix | delta_selectionfix_vs_original |
| --- | --- | ---: | ---: | ---: |
| Best-of-K | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Best-of-K | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Best-of-K | objective_accuracy | 0.7000 | 0.6800 | -0.0200 |
| Best-of-K | structure_completeness | 0.7774 | 0.7774 | +0.0000 |
| Best-of-K | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Best-of-K | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Consensus only | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Consensus only | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Consensus only | objective_accuracy | 0.7000 | 0.7200 | +0.0200 |
| Consensus only | structure_completeness | 0.7770 | 0.7747 | -0.0023 |
| Consensus only | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Consensus only | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Direct | executable_rate | 0.9000 | 0.9000 | +0.0000 |
| Direct | optimal_rate | 0.8000 | 0.8000 | +0.0000 |
| Direct | objective_accuracy | 0.6800 | 0.6800 | +0.0000 |
| Direct | structure_completeness | 0.7446 | 0.7446 | +0.0000 |
| Direct | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Direct | constraint_coverage | 0.8775 | 0.8775 | +0.0000 |
| OR-R1-like Voting | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| OR-R1-like Voting | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| OR-R1-like Voting | objective_accuracy | 0.7000 | 0.7200 | +0.0200 |
| OR-R1-like Voting | structure_completeness | 0.7770 | 0.7747 | -0.0023 |
| OR-R1-like Voting | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| OR-R1-like Voting | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| OptArgus-like Audit | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| OptArgus-like Audit | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| OptArgus-like Audit | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| OptArgus-like Audit | structure_completeness | 0.7774 | 0.7750 | -0.0024 |
| OptArgus-like Audit | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| OptArgus-like Audit | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| OptiRepair-like Repair-Prompt | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| OptiRepair-like Repair-Prompt | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| OptiRepair-like Repair-Prompt | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| OptiRepair-like Repair-Prompt | structure_completeness | 0.7774 | 0.7750 | -0.0024 |
| OptiRepair-like Repair-Prompt | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| OptiRepair-like Repair-Prompt | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| ReplenishVerifier-Full | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| ReplenishVerifier-Full | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| ReplenishVerifier-Full | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| ReplenishVerifier-Full | structure_completeness | 0.7774 | 0.7774 | +0.0000 |
| ReplenishVerifier-Full | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| ReplenishVerifier-Full | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| ReplenishVerifier-Repair | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| ReplenishVerifier-Repair | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| ReplenishVerifier-Repair | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| ReplenishVerifier-Repair | structure_completeness | 0.7774 | 0.7774 | +0.0000 |
| ReplenishVerifier-Repair | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| ReplenishVerifier-Repair | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| ReplenishVerifier-TypeAware | executable_rate | 0.9400 | 0.9000 | -0.0400 |
| ReplenishVerifier-TypeAware | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| ReplenishVerifier-TypeAware | objective_accuracy | 0.7200 | 0.7000 | -0.0200 |
| ReplenishVerifier-TypeAware | structure_completeness | 0.7770 | 0.7483 | -0.0287 |
| ReplenishVerifier-TypeAware | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| ReplenishVerifier-TypeAware | constraint_coverage | 0.9128 | 0.8778 | -0.0350 |
| SIRL-like LP-Stats | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| SIRL-like LP-Stats | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| SIRL-like LP-Stats | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| SIRL-like LP-Stats | structure_completeness | 0.7770 | 0.7747 | -0.0023 |
| SIRL-like LP-Stats | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| SIRL-like LP-Stats | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Solver + Consensus | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Solver + Consensus | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Solver + Consensus | objective_accuracy | 0.7000 | 0.7200 | +0.0200 |
| Solver + Consensus | structure_completeness | 0.7770 | 0.7747 | -0.0023 |
| Solver + Consensus | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Solver + Consensus | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Solver + Structure | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Solver + Structure | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Solver + Structure | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Solver + Structure | structure_completeness | 0.7774 | 0.7774 | +0.0000 |
| Solver + Structure | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Solver + Structure | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Solver + Structure + Consensus | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Solver + Structure + Consensus | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Solver + Structure + Consensus | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Solver + Structure + Consensus | structure_completeness | 0.7770 | 0.7770 | +0.0000 |
| Solver + Structure + Consensus | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Solver + Structure + Consensus | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Solver only | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Solver only | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Solver only | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Solver only | structure_completeness | 0.7774 | 0.7742 | -0.0032 |
| Solver only | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Solver only | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Solver-Filter | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Solver-Filter | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Solver-Filter | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Solver-Filter | structure_completeness | 0.7774 | 0.7742 | -0.0032 |
| Solver-Filter | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Solver-Filter | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Structure + Consensus | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Structure + Consensus | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Structure + Consensus | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Structure + Consensus | structure_completeness | 0.7770 | 0.7770 | +0.0000 |
| Structure + Consensus | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Structure + Consensus | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Structure only | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Structure only | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Structure only | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Structure only | structure_completeness | 0.7774 | 0.7774 | +0.0000 |
| Structure only | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Structure only | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Structure-Grounded Consistency | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Structure-Grounded Consistency | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Structure-Grounded Consistency | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Structure-Grounded Consistency | structure_completeness | 0.7770 | 0.7770 | +0.0000 |
| Structure-Grounded Consistency | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Structure-Grounded Consistency | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
| Structure-Only | executable_rate | 0.9400 | 0.9400 | +0.0000 |
| Structure-Only | optimal_rate | 0.8200 | 0.8200 | +0.0000 |
| Structure-Only | objective_accuracy | 0.7000 | 0.7000 | +0.0000 |
| Structure-Only | structure_completeness | 0.7774 | 0.7774 | +0.0000 |
| Structure-Only | inventory_balance_accuracy | 1.0000 | 1.0000 | +0.0000 |
| Structure-Only | constraint_coverage | 0.9128 | 0.9128 | +0.0000 |
