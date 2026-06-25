# qwen3_8b_k8_100_tac_challenger_robust_20260625_185035_v9_compare

This directory contains the TAC challenger / Pareto-safe override experiment result for V9.

## Inputs

- Benchmark: `data/generated/test_100_v6.jsonl`
- Candidates: `data/candidates/qwen3_8b_k8_100_v9_regen_seed123.jsonl`
- Run dir: `runs/qwen3_8b_k8_100_tac_challenger_robust_20260625_185035_v9`

## Key Files

- `main_results.md`
- `diagnostics/`
- `paper_metrics/`
- `no_leakage_audit.json`
- `candidates/`

## No-Reference Policy

Formal selection methods do not use reference_objective, objective_correct, oracle labels, reference LPs, or reference answers. Oracle metrics are post-hoc diagnostics only.
