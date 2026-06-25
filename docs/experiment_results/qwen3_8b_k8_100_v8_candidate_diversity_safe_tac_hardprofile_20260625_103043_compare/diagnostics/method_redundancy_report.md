# Method Redundancy Report

This report is diagnostic only and does not affect formal selection.

## Method pairs with same_selection_rate >= 0.95

| method_a | method_b | n_common | same_count | same_selection_rate |
| --- | --- | --- | --- | --- |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | 100 | 100 | 1.0000 |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-TypeAware | 100 | 95 | 0.9500 |
| ReplenishVerifier-Full | ReplenishVerifier-FullV2 | 100 | 100 | 1.0000 |
| ReplenishVerifier-HybridSafe | ReplenishVerifier-TypeAware | 100 | 95 | 0.9500 |

## Metrics-identical method groups

- ReplenishVerifier-ConsensusSafe, ReplenishVerifier-HybridSafe

## Same objective_accuracy but different selection groups

- Consensus only, ReplenishVerifier-ConsensusSafe, ReplenishVerifier-Full, ReplenishVerifier-FullV2, ReplenishVerifier-HybridSafe, ReplenishVerifier-TypeAware

## Alias-like same-selection pairs

| method_a | method_b | same_selection_rate | objective_accuracy | recommendation |
| --- | --- | ---: | ---: | --- |
| ReplenishVerifier-ConsensusSafe | ReplenishVerifier-HybridSafe | 1.0000 | 0.83 | alias_like_same_selection |
| ReplenishVerifier-Full | ReplenishVerifier-FullV2 | 1.0000 | 0.83 | alias_like_same_selection |

## Recommended display families

- Main table: Direct, Best-of-K, Consensus only, ReplenishVerifier-Full, ReplenishVerifier-ConsensusSafe/HybridSafe family representative, ReplenishVerifier-TypeAware-Consensus when not alias-like.
- Appendix ablations: Solver-only variants, Structure-only variants, TypeAware, FullV2-Guarded, FullV2-CandidatePoolAware, repair-prompt variants.
- Merge explanation: methods marked alias_like_same_selection should be explained together rather than over-claimed as independent gains.
