# Run Commands

```bash
EXP=qwen3_8b_k8_100_v6_typeaware_consensusrerank
BENCH=data/generated/test_100_v6.jsonl
CAND=data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl
RUNDIR=runs/qwen3_8b_k8_100_v6_typeaware_consensusrerank

python -m replenishverifier.experiments.run_all_methods \
  --benchmark "$BENCH" \
  --candidates "$CAND" \
  --out_dir "$RUNDIR" \
  --k_values 1,2,4,8 \
  --timeout 30 \
  --no_demo_if_empty

python -m replenishverifier.experiments.diagnose_selection_metrics \
  --exp_dir "$RUNDIR" \
  --candidates "$CAND" \
  --benchmark "$BENCH" \
  --out_dir "$RUNDIR/diagnostics"

python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir "$RUNDIR"

python -m replenishverifier.experiments.audit_leakage \
  --exp_dir "$RUNDIR" \
  --write_report

python -m replenishverifier.experiments.build_paper_metrics \
  --exp_dir "$RUNDIR" \
  --out_dir "$RUNDIR/paper_metrics" \
  --k_values 1,2,4,8 \
  --bootstrap_samples 1000 \
  --seed 42
```
