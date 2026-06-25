# qwen3_8b_k8_100_tac_challenger_robust_20260625_185035 Cross-Pool Robustness Summary

This directory summarizes the TAC challenger / Pareto-safe override evaluation across two candidate pools.

## Candidate Pools

| Pool | Candidate File | Result Directory |
|---|---|---|
| V8 | `data/candidates/qwen3_8b_k8_100_v8_candidate_diversity.jsonl` | `docs/experiment_results/qwen3_8b_k8_100_tac_challenger_robust_20260625_185035_v8_compare` |
| V9 | `data/candidates/qwen3_8b_k8_100_v9_regen_seed123.jsonl` | `docs/experiment_results/qwen3_8b_k8_100_tac_challenger_robust_20260625_185035_v9_compare` |

## Purpose

The goal is to evaluate whether TypeAware-Consensus remains robust across different regenerated candidate pools, instead of being optimized for one fixed candidate file.

## No-Reference Policy

Formal selection does not use reference_objective, objective_correct, oracle labels, reference LP, or reference answer.
