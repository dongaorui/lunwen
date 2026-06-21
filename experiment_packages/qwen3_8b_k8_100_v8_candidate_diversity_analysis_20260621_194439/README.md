# qwen3_8b_k8_100_v8_candidate_diversity_analysis_20260621_194439 Experiment Package

This package contains the Qwen3-8B k=8 / 100-problem candidate-diversity prompt experiment.

## Inputs

- Benchmark: `data/generated/test_100_v6.jsonl`
- Candidates: `data/candidates/qwen3_8b_k8_100_v8_candidate_diversity.jsonl`
- Run dir: `runs/qwen3_8b_k8_100_v8_candidate_diversity_analysis_20260621_194439`
- Report dir: `docs/experiment_results/qwen3_8b_k8_100_v8_candidate_diversity_analysis_20260621_194439_compare`

## Purpose

Evaluate whether candidate-specific diversity prompting improves the candidate pool and downstream no-reference selection.

## Notes

Formal selection must not use reference_objective, objective_correct, oracle, reference LP, or reference answer.

The candidate file is stored in compressed form under the docs report directory.
