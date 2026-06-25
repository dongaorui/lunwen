# Metric Comparison

| method | metric | reported | recomputed | delta | status |
| --- | --- | --- | --- | --- | --- |
| Best-of-K | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Best-of-K | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Best-of-K | objective_accuracy | 0.7900 | 0.7900 | 0.0000 | OK |
| Best-of-K | structure_completeness | 0.8042 | 0.8042 | -0.0000 | OK |
| Best-of-K | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Best-of-K | constraint_coverage | 0.9417 | 0.9417 | -0.0000 | OK |
| Best-of-K | average_runtime_sec | 0.1034 | 0.1034 | -0.0000 | OK |
| Best-of-K | average_repair_feedback_count | 0.2400 | 0.2400 | 0.0000 | OK |
| Consensus only | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Consensus only | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Consensus only | objective_accuracy | 0.8000 | 0.8000 | 0.0000 | OK |
| Consensus only | structure_completeness | 0.7920 | 0.7920 | -0.0000 | OK |
| Consensus only | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Consensus only | constraint_coverage | 0.9343 | 0.9343 | 0.0000 | OK |
| Consensus only | average_runtime_sec | 0.1007 | 0.1007 | 0.0000 | OK |
| Consensus only | average_repair_feedback_count | 0.3000 | 0.3000 | 0.0000 | OK |
| Direct | executable_rate | 0.9000 | 0.9000 | 0.0000 | OK |
| Direct | optimal_rate | 0.7700 | 0.7700 | 0.0000 | OK |
| Direct | objective_accuracy | 0.6700 | 0.6700 | 0.0000 | OK |
| Direct | structure_completeness | 0.7375 | 0.7375 | -0.0000 | OK |
| Direct | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Direct | constraint_coverage | 0.8708 | 0.8708 | 0.0000 | OK |
| Direct | average_runtime_sec | 0.1062 | 0.1062 | 0.0000 | OK |
| Direct | average_repair_feedback_count | 0.2400 | 0.2400 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | objective_accuracy | 0.8000 | 0.8000 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | structure_completeness | 0.8081 | 0.8081 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | constraint_coverage | 0.9479 | 0.9479 | 0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | average_runtime_sec | 0.1030 | 0.1030 | -0.0000 | OK |
| ReplenishVerifier-ConsensusSafe | average_repair_feedback_count | 0.1900 | 0.0700 | -0.1200 | MISMATCH |
| ReplenishVerifier-Full | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-Full | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-Full | objective_accuracy | 0.8100 | 0.8100 | 0.0000 | OK |
| ReplenishVerifier-Full | structure_completeness | 0.8089 | 0.8089 | -0.0000 | OK |
| ReplenishVerifier-Full | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-Full | constraint_coverage | 0.9479 | 0.9479 | 0.0000 | OK |
| ReplenishVerifier-Full | average_runtime_sec | 0.1085 | 0.1085 | -0.0000 | OK |
| ReplenishVerifier-Full | average_repair_feedback_count | 0.1900 | 0.1900 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | objective_accuracy | 0.8100 | 0.8100 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | structure_completeness | 0.8089 | 0.8089 | -0.0000 | OK |
| ReplenishVerifier-FullV2 | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | constraint_coverage | 0.9479 | 0.9479 | 0.0000 | OK |
| ReplenishVerifier-FullV2 | average_runtime_sec | 0.1085 | 0.1085 | -0.0000 | OK |
| ReplenishVerifier-FullV2 | average_repair_feedback_count | 0.1900 | 0.0700 | -0.1200 | MISMATCH |
| ReplenishVerifier-HybridSafe | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | objective_accuracy | 0.8000 | 0.8000 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | structure_completeness | 0.8081 | 0.8081 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | constraint_coverage | 0.9479 | 0.9479 | 0.0000 | OK |
| ReplenishVerifier-HybridSafe | average_runtime_sec | 0.1030 | 0.1030 | -0.0000 | OK |
| ReplenishVerifier-HybridSafe | average_repair_feedback_count | 0.1900 | 0.0700 | -0.1200 | MISMATCH |
| ReplenishVerifier-TypeAware | executable_rate | 0.9400 | 0.9400 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | objective_accuracy | 0.8000 | 0.8000 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | structure_completeness | 0.7898 | 0.7898 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | constraint_coverage | 0.9258 | 0.9258 | 0.0000 | OK |
| ReplenishVerifier-TypeAware | average_runtime_sec | 0.1020 | 0.1020 | -0.0000 | OK |
| ReplenishVerifier-TypeAware | average_repair_feedback_count | 0.1200 | 0.0600 | -0.0600 | MISMATCH |
| ReplenishVerifier-TypeAware-Consensus | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | objective_accuracy | 0.8200 | 0.8200 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | structure_completeness | 0.8087 | 0.8087 | -0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | constraint_coverage | 0.9479 | 0.9479 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | average_runtime_sec | 0.1033 | 0.1033 | 0.0000 | OK |
| ReplenishVerifier-TypeAware-Consensus | average_repair_feedback_count | 0.1900 | 0.0700 | -0.1200 | MISMATCH |
| Solver only | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Solver only | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Solver only | objective_accuracy | 0.7400 | 0.7400 | 0.0000 | OK |
| Solver only | structure_completeness | 0.7923 | 0.7923 | -0.0000 | OK |
| Solver only | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Solver only | constraint_coverage | 0.9354 | 0.9354 | 0.0000 | OK |
| Solver only | average_runtime_sec | 0.1003 | 0.1003 | -0.0000 | OK |
| Solver only | average_repair_feedback_count | 0.2900 | 0.2900 | 0.0000 | OK |
| Structure only | executable_rate | 0.9700 | 0.9700 | 0.0000 | OK |
| Structure only | optimal_rate | 0.8700 | 0.8700 | 0.0000 | OK |
| Structure only | objective_accuracy | 0.8100 | 0.8100 | 0.0000 | OK |
| Structure only | structure_completeness | 0.8089 | 0.8089 | -0.0000 | OK |
| Structure only | inventory_balance_accuracy | 1.0000 | 1.0000 | 0.0000 | OK |
| Structure only | constraint_coverage | 0.9479 | 0.9479 | 0.0000 | OK |
| Structure only | average_runtime_sec | 0.1083 | 0.1083 | 0.0000 | OK |
| Structure only | average_repair_feedback_count | 0.1900 | 0.1900 | 0.0000 | OK |
