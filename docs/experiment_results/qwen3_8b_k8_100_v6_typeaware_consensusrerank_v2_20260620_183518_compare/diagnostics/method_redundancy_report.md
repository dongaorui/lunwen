# Method Redundancy Report

This report is diagnostic only and does not affect formal selection.

## Method pairs with same_selection_rate >= 0.95

| method_a | method_b | n_common | same_count | same_selection_rate |
| --- | --- | --- | --- | --- |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | 100 | 100 | 1.0000 |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | 100 | 97 | 0.9700 |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware-Consensus | 100 | 100 | 1.0000 |
| ReplenishVerifier-Full | Structure only | 100 | 99 | 0.9900 |
| ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware | 100 | 97 | 0.9700 |
| ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware-Consensus | 100 | 100 | 1.0000 |
| ReplenishVerifier-TypeAware | ReplenishVerifier-TypeAware-Consensus | 100 | 97 | 0.9700 |

## Metrics-identical method groups

- ReplenishVerifier-ConsensusSafe, ReplenishVerifier-HybridSafe, ReplenishVerifier-TypeAware-Consensus

## Same objective_accuracy but different selection groups

- Consensus only, ReplenishVerifier-ConsensusSafe, ReplenishVerifier-HybridSafe, ReplenishVerifier-TypeAware, ReplenishVerifier-TypeAware-Consensus
- ReplenishVerifier-Full, Structure only

## Recommended display families

- Solver family: Solver only, Solver-Filter
- Structure family: Structure only, Structure-Only
- Consensus family: Consensus only, OR-R1-like Voting, Solver + Consensus
- Full verifier family: ReplenishVerifier-Full, ReplenishVerifier-Repair, Structure-Grounded Consistency
