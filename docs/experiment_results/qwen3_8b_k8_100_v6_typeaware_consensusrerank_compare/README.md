# Qwen3-8B k=8 / 100-problem TypeAware Consensus Rerank Experiment

This folder contains the final packaged experiment artifacts for:

- model: Qwen/Qwen3-8B
- prompt type: type_aware_hidden_verifier
- benchmark: `data/generated/test_100_v6.jsonl`
- candidates: `data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl`
- run dir: `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank`
- problems: 100
- candidates per problem: 8
- total candidates: 800

## Contents

- `main_results.md`: main method comparison
- `candidate_evaluations.csv`: evaluated candidate-level results
- `selected_results.csv`: selected candidate results by method
- `diagnostics/`: selection diagnostics, join diagnostics, redundancy analysis
- `paper_metrics/`: paper-ready tables
- `error_type_summary.md`: error taxonomy summary
- `no_leakage_audit.json` / leakage report: leakage audit
- `candidates/`: compressed 800 generated candidate records
- `logs/`: experiment execution logs

## Important Notes

Candidates were not regenerated for this run. The experiment reruns evaluation, selection, diagnostics, error analysis, leakage audit, and paper metrics on the existing 800 candidates.

Formal selection does not use reference objective, objective_correct, oracle, reference LP, or reference answer.
