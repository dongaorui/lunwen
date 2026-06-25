# Analysis Summary: Safe TypeAware-Consensus Hard-Profile Experiment

## Experiment Setup

- Benchmark: `data/generated/test_100_v6.jsonl`
- Candidates: `data/candidates/qwen3_8b_k8_100_v8_candidate_diversity.jsonl`
- Problems: 100
- Candidates per problem: 8

## Goal

This experiment further improves `ReplenishVerifier-TypeAware-Consensus` for hard problem types such as capacity-constrained, fixed-order-cost, shortage/backorder, newsvendor, and lead-time-style cases. The selector remains no-reference and uses solver safety, safe consensus, objective-term coverage, problem-type schema coverage, and text-triggered hard gates.

## Interpretation

The goal is not to weaken Consensus-only, Structure-only, or Best-of-K baselines, but to make TypeAware-Consensus more robust on structurally demanding cases where raw consensus or structure-only selection may be insufficient. Diagnostics report selector-limited versus pool-limited failures by problem type.

## No-Reference Policy

Formal selection does not use `reference_objective`, `objective_correct`, oracle labels, reference LPs, or reference answers. These fields may appear only in post-hoc diagnostics.
