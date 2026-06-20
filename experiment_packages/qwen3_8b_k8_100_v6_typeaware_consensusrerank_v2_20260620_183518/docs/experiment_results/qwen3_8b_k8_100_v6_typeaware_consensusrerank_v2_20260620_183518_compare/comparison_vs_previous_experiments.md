# Comparison vs Previous Experiments

- Old best report: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare`
- Bad/previous v2 attempt: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_175202/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_175202_compare`
- New report: `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare`

## Best Method Summary

- Old best: `Best-of-K` objective_accuracy `0.7500`
- Bad attempt best: `Best-of-K` objective_accuracy `0.7400`
- New best: `Best-of-K` objective_accuracy `0.7600`

## Main Result Delta

| method | old best | bad attempt | new | new-old | new-bad |
| --- | ---: | ---: | ---: | ---: | ---: |
| Best-of-K | 0.7500 | 0.7400 | 0.7600 | +0.0100 | +0.0200 |
| Consensus only | 0.7300 | 0.7200 | 0.7200 | -0.0100 | +0.0000 |
| Direct | 0.6900 | 0.6900 | 0.6900 | +0.0000 | +0.0000 |
| ReplenishVerifier-ConsensusSafe | nan | 0.7200 | 0.7200 | +nan | +0.0000 |
| ReplenishVerifier-Full | 0.7400 | 0.7200 | 0.7400 | +0.0000 | +0.0200 |
| ReplenishVerifier-HybridSafe | nan | nan | 0.7200 | +nan | +nan |
| ReplenishVerifier-TypeAware | 0.7200 | 0.7200 | 0.7200 | +0.0000 | +0.0000 |
| ReplenishVerifier-TypeAware-Consensus | 0.7200 | 0.7200 | 0.7200 | +0.0000 | +0.0000 |
| Solver only | 0.7300 | 0.7100 | 0.7100 | -0.0200 | +0.0000 |
| Structure only | 0.7400 | 0.7400 | 0.7400 | +0.0000 | +0.0000 |

## Interpretation Guide

- `new-old > 0`: new method improved over the old best package.
- `new-bad > 0`: new method recovered from the bad v2 attempt.
- Check whether Full is restored near 0.7400.
- Check whether HybridSafe / ConsensusSafeV2 improves over Full and Best-of-K.
- Check no-leakage audit before using results in the thesis.
