# Comparison vs Previous Experiment

- Previous report: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026/docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare`
- New report: `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_175202_compare`

## Best Method Summary

- Previous best method: `Best-of-K` with objective_accuracy `0.7500`
- New best method: `Best-of-K` with objective_accuracy `0.7400`

## Main Result Delta

| method | previous objective_accuracy | new objective_accuracy | delta |
| --- | ---: | ---: | ---: |
| Best-of-K | 0.7500 | 0.7400 | -0.0100 |
| Consensus only | 0.7300 | 0.7200 | -0.0100 |
| Direct | 0.6900 | 0.6900 | +0.0000 |
| ReplenishVerifier-ConsensusSafe | nan | 0.7200 | +nan |
| ReplenishVerifier-Full | 0.7400 | 0.7200 | -0.0200 |
| ReplenishVerifier-TypeAware | 0.7200 | 0.7200 | +0.0000 |
| ReplenishVerifier-TypeAware-Consensus | 0.7200 | 0.7200 | +0.0000 |
| Solver only | 0.7300 | 0.7100 | -0.0200 |
| Structure only | 0.7400 | 0.7400 | +0.0000 |

## Oracle / Pass@K Delta

| k | previous oracle objective | new oracle objective | delta |
| --- | ---: | ---: | ---: |
| 1 | 0.6900 | 0.6900 | +0.0000 |
| 2 | 0.7200 | 0.7200 | +0.0000 |
| 4 | 0.7800 | 0.7800 | +0.0000 |
| 8 | 0.7800 | 0.7800 | +0.0000 |
