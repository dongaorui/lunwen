# Repair Loop Experiment Guide

## 1. Why repair prompts alone are not enough

A repair prompt is only an instruction. It does not prove that a candidate was repaired, that the repaired code executes, or that the resulting LP contains the missing replenishment structures. Therefore, prompt generation should be described as repair-feedback or repair-prompt generation, not as repair performance.

## 2. Why real repaired candidates are required

A valid repair experiment must call the chosen local LLM or model endpoint to produce second-round candidate code, then rerun the same solver/export/verification pipeline. Only after that can the paper report repair objective accuracy, structure completeness, or missing-structure reductions.

## 3. Generic vs structure-aware repair

- Generic repair uses execution and generic LP-artifact feedback: missing objective, no variables, suspicious placeholder names, solver errors, empty model.
- Structure-aware repair uses ReplenishVerifier certificates: low-score inventory balance, missing Big-M linking, weak capacity evidence, missing fixed-order-cost objective terms, and evidence-strength details.

This separation prevents attributing generic repair gains to replenishment-specific structure feedback.

## 4. How to generate repair candidates

Structure-aware repair:

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/benchmark/real_50.jsonl \
  --repair_prompts runs/real_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_repaired_structure.jsonl \
  --model /path/to/local/model \
  --repair_type structure_aware
```

Generic repair baseline:

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/benchmark/real_50.jsonl \
  --repair_prompts runs/real_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_repaired_generic.jsonl \
  --model /path/to/local/model \
  --repair_type generic
```

Dry run for pipeline checks only:

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/benchmark/real_50.jsonl \
  --repair_prompts runs/real_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out /tmp/repair_dry_run.jsonl \
  --model dummy \
  --dry_run
```

`--dry_run` writes placeholder code to keep downstream schemas uniform. It must not be used as a repair experiment result.

## 5. How to rerun all methods

Evaluate repaired candidates with the same benchmark:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_repaired_structure.jsonl \
  --out_dir runs/real_50_repaired_structure \
  --k_values 1,2,4 \
  --timeout 30
```

Repeat for generic repair.

## 6. How to compare before and after

```bash
python -m replenishverifier.experiments.compare_repair_results \
  --before runs/real_50/candidate_evaluations.jsonl \
  --after runs/real_50_repaired_structure/candidate_evaluations.jsonl \
  --out runs/real_50_repaired_structure/repair_comparison.json
```

## 7. Metrics proving repair effectiveness

A strong repair result should show improvement in at least some of:

- Objective Accuracy before / after;
- Structure Completeness before / after;
- Inventory Balance Accuracy before / after;
- missing_big_m rate before / after;
- missing_fixed_order_cost rate before / after;
- missing_capacity_constraint rate before / after;
- Avg Repair Feedback Count;
- number of repaired candidates.

## 8. If objective accuracy decreases

A repaired model can become structurally more complete while objective accuracy decreases if the LLM over-corrects, changes assumptions, uses wrong coefficients, or introduces execution instability. Report this as a repair trade-off and use case studies. Do not hide decreases.

## 9. Results suitable for the main table

Main-paper repair claims require real generated repaired candidates, rerun evaluation, leakage audit, and preferably comparison to generic repair. Use aggregate metrics from the real LLM setting.

## 10. Results suitable only for appendix

- Synthetic smoke repair examples;
- dry-run outputs;
- tiny debugging subsets;
- hand-inspected anecdotes without full rerun;
- optional objective-consensus variants unless promoted to the main method.

## 11. Dry-run warning

Dry run only checks that prompts render and downstream JSONL schemas remain stable. It is not a repair experiment and must not be described as successful repair.
