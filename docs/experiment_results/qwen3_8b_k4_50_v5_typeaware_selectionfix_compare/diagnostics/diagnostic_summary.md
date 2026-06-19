# Selection Metric Diagnostics

```json
{
  "exp_dir": "runs/qwen3_8b_k4_50_v5_typeaware_selectionfix",
  "candidates_path": "data/candidates/qwen3_8b_k4_50_v5_typeaware.jsonl",
  "benchmark_path": "data/generated/test_50.jsonl",
  "status_counts": {
    "OK": 151,
    "MISMATCH": 1,
    "MISSING": 113
  },
  "note": "objective_correct_posthoc appears only in diagnostics and is not a formal selection signal."
}
```
