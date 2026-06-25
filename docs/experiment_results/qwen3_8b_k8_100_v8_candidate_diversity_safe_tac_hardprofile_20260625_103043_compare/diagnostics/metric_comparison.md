# Metric Comparison

| method | metric | reported | recomputed | delta | status |
| --- | --- | --- | --- | --- | --- |
| Best-of-K | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Best-of-K | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Best-of-K | objective_accuracy | 0.7900 | 0.7900 | 0.0000 | OK |
| Best-of-K | structure_completeness | 0.8032 | 0.8032 | 0.0000 | OK |
| Best-of-K | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Best-of-K | constraint_coverage | 0.9394 | 0.9394 | 0.0000 | OK |
| Best-of-K | average_runtime_sec | 0.1051 | 0.1051 | -0.0000 | OK |
| Best-of-K | average_repair_feedback_count | 0.2600 | 0.2600 | 0.0000 | OK |
| Consensus only | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Consensus only | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Consensus only | objective_accuracy | 0.8300 | 0.8300 | 0.0000 | OK |
| Consensus only | structure_completeness | 0.7895 | 0.7895 | 0.0000 | OK |
| Consensus only | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Consensus only | constraint_coverage | 0.9319 | 0.9319 | 0.0000 | OK |
| Consensus only | average_runtime_sec | 0.1026 | 0.1026 | 0.0000 | OK |
| Consensus only | average_repair_feedback_count | 0.3200 | 0.3200 | 0.0000 | OK |
| Direct | executable_rate | 0.9100 | 0.9100 | 0.0000 | OK |
| Direct | optimal_rate | 0.7800 | 0.7800 | 0.0000 | OK |
| Direct | objective_accuracy | 0.7000 | 0.7000 | 0.0000 | OK |
| Direct | structure_completeness | 0.7489 | 0.7489 | 0.0000 | OK |
| Direct | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Direct | constraint_coverage | 0.8842 | 0.8842 | -0.0000 | OK |
| Direct | average_runtime_sec | 0.1071 | 0.1071 | 0.0000 | OK |
| Direct | average_repair_feedback_count | 0.2100 | 0.2100 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | objective_accuracy | 0.8300 | 0.8300 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | structure_completeness | 0.8067 | 0.8067 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | constraint_coverage | 0.9444 | 0.9444 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | average_runtime_sec | 0.1049 | 0.1049 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | average_repair_feedback_count | 0.2200 | 0.0800 | -0.1400 | MISMATCH |
| ReplenishVerifier-Full | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-Full | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-Full | objective_accuracy | 0.8300 | 0.8300 | 0.0000 | OK |
| ReplenishVerifier-Full | structure_completeness | 0.8076 | 0.8076 | -0.0000 | OK |
| ReplenishVerifier-Full | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-Full | constraint_coverage | 0.9444 | 0.9444 | 0.0000 | OK |
| ReplenishVerifier-Full | average_runtime_sec | 0.1108 | 0.1108 | -0.0000 | OK |
| ReplenishVerifier-Full | average_repair_feedback_count | 0.2200 | 0.2200 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | objective_accuracy | 0.8300 | 0.8300 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | structure_completeness | 0.8076 | 0.8076 | -0.0000 | OK |
| ReplenishVerifier-FullV2 | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | constraint_coverage | 0.9444 | 0.9444 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | average_runtime_sec | 0.1108 | 0.1108 | -0.0000 | OK |
| ReplenishVerifier-FullV2 | average_repair_feedback_count | 0.2200 | 0.0800 | -0.1400 | MISMATCH |
| ReplenishVerifier-HybridSafe | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | objective_accuracy | 0.8300 | 0.8300 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | structure_completeness | 0.8067 | 0.8067 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | constraint_coverage | 0.9444 | 0.9444 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | average_runtime_sec | 0.1049 | 0.1049 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | average_repair_feedback_count | 0.2200 | 0.0800 | -0.1400 | MISMATCH |
| ReplenishVerifier-TypeAware | executable_rate | 0.9300 | 0.9300 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | objective_accuracy | 0.8300 | 0.8300 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | structure_completeness | 0.7806 | 0.7806 | -0.0000 | OK |
| ReplenishVerifier-TypeAware | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | constraint_coverage | 0.9136 | 0.9136 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | average_runtime_sec | 0.1035 | 0.1035 | -0.0000 | OK |
| ReplenishVerifier-TypeAware | average_repair_feedback_count | 0.1400 | 0.0600 | -0.0800 | MISMATCH |
| ReplenishVerifier-TypeAware-Consensus | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | objective_accuracy | 0.8500 | 0.8500 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | structure_completeness | 0.8073 | 0.8073 | -0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | constraint_coverage | 0.9444 | 0.9444 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | average_runtime_sec | 0.1066 | 0.1066 | -0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | average_repair_feedback_count | 0.2200 | 0.0800 | -0.1400 | MISMATCH |
| Solver only | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Solver only | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Solver only | objective_accuracy | 0.7700 | 0.7700 | 0.0000 | OK |
| Solver only | structure_completeness | 0.7898 | 0.7898 | 0.0000 | OK |
| Solver only | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Solver only | constraint_coverage | 0.9319 | 0.9319 | 0.0000 | OK |
| Solver only | average_runtime_sec | 0.1024 | 0.1024 | -0.0000 | OK |
| Solver only | average_repair_feedback_count | 0.3200 | 0.3200 | 0.0000 | OK |
| Structure only | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Structure only | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Structure only | objective_accuracy | 0.8200 | 0.8200 | 0.0000 | OK |
| Structure only | structure_completeness | 0.8076 | 0.8076 | -0.0000 | OK |
| Structure only | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Structure only | constraint_coverage | 0.9444 | 0.9444 | 0.0000 | OK |
| Structure only | average_runtime_sec | 0.1099 | 0.1099 | -0.0000 | OK |
| Structure only | average_repair_feedback_count | 0.2200 | 0.2200 | 0.0000 | OK |
