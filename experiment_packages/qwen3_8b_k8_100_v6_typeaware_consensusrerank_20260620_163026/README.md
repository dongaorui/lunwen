# qwen3_8b_k8_100_v6_typeaware_consensusrerank Experiment Package

Generated at: 20260620_163026

## Inputs

- Benchmark: data/generated/test_100_v6.jsonl
- Candidates: data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl
- Run dir: runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank
- Report dir: docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare

## Main commands

```bash
pytest \
  tests/test_diagnose_selection_metrics.py \
  tests/test_leakage_audit.py \
  tests/test_paper_metrics.py \
  tests/test_selection_gating.py

python -m replenishverifier.experiments.paper_metrics \
  --benchmark data/generated/test_100_v6.jsonl \
  --candidates data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl \
  --out_dir docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare \
  --exp_dir runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank \
  --write_report
```

## Important files

- `docs/experiment_results/qwen3_8b_k8_100_v6_typeaware_consensusrerank_compare/main_results.md`
- `runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank/diagnostics/`
- `logs/pytest_selected.log`
- `logs/paper_metrics.log`
- `logs/git_state.txt`
- `logs/working_tree.diff`
- `logs/input_integrity.txt`

## Notes

This package is intended to preserve the full local experiment record, including code state, logs, inputs, reports, and diagnostics.
