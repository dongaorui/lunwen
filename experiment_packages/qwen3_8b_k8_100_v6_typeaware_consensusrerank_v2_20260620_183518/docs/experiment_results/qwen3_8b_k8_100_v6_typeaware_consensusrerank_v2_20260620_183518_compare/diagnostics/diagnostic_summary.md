# Selection Metric Diagnostics

```json
{
  "exp_dir": "runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank_v2_20260620_183518",
  "candidates_path": "data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl",
  "benchmark_path": "data/generated/test_100_v6.jsonl",
  "status_counts": {
    "OK": 80,
    "MISSING": 51
  },
  "unmatched_selected_rows": 0,
  "unmatched_reason_counts": {},
  "join_note": "All selected rows matched candidate evaluations by problem_id + candidate_id/rank.",
  "note": "objective_correct_posthoc appears only in diagnostics and is not a formal selection signal."
}
```
