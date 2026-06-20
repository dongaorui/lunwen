# Selection Metric Diagnostics

```json
{
  "exp_dir": "runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank",
  "candidates_path": "data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl",
  "benchmark_path": "data/generated/test_100_v6.jsonl",
  "status_counts": {
    "OK": 64,
    "MISMATCH": 8,
    "MISSING": 32
  },
  "unmatched_selected_rows": 0,
  "unmatched_reason_counts": {},
  "join_note": "All selected rows matched candidate evaluations by problem_id + candidate_id/rank.",
  "note": "objective_correct_posthoc appears only in diagnostics and is not a formal selection signal."
}
```
