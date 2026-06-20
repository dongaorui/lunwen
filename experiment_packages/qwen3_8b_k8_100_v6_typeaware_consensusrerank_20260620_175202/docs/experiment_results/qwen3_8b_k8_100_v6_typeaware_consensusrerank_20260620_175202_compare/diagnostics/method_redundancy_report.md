# Method Redundancy Report

This report is diagnostic only and does not affect formal selection.

## Method pairs with same_selection_rate >= 0.95

| method_a | method_b | n_common | same_count | same_selection_rate |
| --- | --- | --- | --- | --- |
| Best-of-K | ReplenishVerifier-Full | 100 | 95 | 0.9500 |
| Consensus only | Solver only | 100 | 96 | 0.9600 |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | 100 | 97 | 0.9700 |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware-Consensus | 100 | 100 | 1.0000 |
| ReplenishVerifier-TypeAware | ReplenishVerifier-TypeAware-Consensus | 100 | 97 | 0.9700 |

## Metrics-identical method groups

- ReplenishVerifier-ConsensusSafe, ReplenishVerifier-TypeAware-Consensus

## Same objective_accuracy but different selection groups

- Best-of-K, Structure only
- Consensus only, ReplenishVerifier-ConsensusSafe, ReplenishVerifier-Full, ReplenishVerifier-TypeAware, ReplenishVerifier-TypeAware-Consensus

## Recommended display families

- Solver family: Solver only, Solver-Filter
- Structure family: Structure only, Structure-Only
- Consensus family: Consensus only, OR-R1-like Voting, Solver + Consensus
- Full verifier family: ReplenishVerifier-Full, ReplenishVerifier-Repair, Structure-Grounded Consistency
