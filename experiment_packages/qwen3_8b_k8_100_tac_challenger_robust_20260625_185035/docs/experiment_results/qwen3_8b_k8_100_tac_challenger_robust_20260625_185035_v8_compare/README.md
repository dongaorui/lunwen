# qwen3_8b_k8_100_tac_challenger_robust_20260625_185035_v8_compare

This directory contains the TAC challenger / Pareto-safe override experiment result for V8.

## Inputs

- Benchmark: `data/generated/test_100_v6.jsonl`
- Candidates: `data/candidates/qwen3_8b_k8_100_v8_candidate_diversity.jsonl`
- Run dir: `runs/qwen3_8b_k8_100_tac_challenger_robust_20260625_185035_v8`

## Key Files

- `main_results.md`
- `diagnostics/`
- `paper_metrics/`
- `no_leakage_audit.json`
- `candidates/`

## No-Reference Policy

Formal selection methods do not use reference_objective, objective_correct, oracle labels, reference LPs, or reference answers. Oracle metrics are post-hoc diagnostics only.
