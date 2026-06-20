# qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518 Experiment Package

This package contains the third-round v2 Qwen3-8B k=8 / 100-problem experiment.

## Inputs

- Benchmark: `data/generated/test_100_v6.jsonl`
- Candidates: `data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl`
- Run dir: `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518`
- Report dir: `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare`
- Old best package: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_163026`
- Bad previous attempt: `experiment_packages/qwen3_8b_k8_100_v6_typeaware_consensusrerank_20260620_175202`

## Important Files

- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare/main_results.md`
- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare/comparison_vs_previous_experiments.md`
- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare/comparison_vs_old_and_bad.csv`
- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare/diagnostics/`
- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare/paper_metrics/`
- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518_compare/regression_diagnostics/`
- `logs/input_integrity.txt`
- `logs/git_status_short.txt`

## Notes

Candidates were not regenerated.

Formal selection must not use reference_objective, objective_correct, oracle, reference LP, or reference answer.
