# Robustness to Naming Variations / 命名变化鲁棒性实验指南

## 1. Why this experiment is needed

ReplenishVerifier uses LP artifacts and still benefits from variable and constraint names. A reviewer may ask whether the method only rewards familiar names such as `inventory_balance`, `Q`, `I`, and `Y`. Naming-variation experiments test whether the verifier remains useful when semantically equivalent candidates use different names.

## 2. Reviewer concern addressed

This experiment directly addresses the concern that structural rules can be gamed by names alone. In the hardened implementation, a structure name alone is weak evidence: high confidence requires expression-level and/or incidence/index evidence. The naming-variation experiment measures the remaining sensitivity to names.

## 3. How to generate renamed candidates

Use the lightweight candidate renamer:

```bash
python -m replenishverifier.experiments.rename_variables_for_robustness \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_renamed.jsonl \
  --mode random
```

Supported modes:

- `semantic`: replaces common symbols with descriptive names, e.g. `Q -> order_qty`.
- `random`: replaces common symbols with random neutral names.
- `adversarial`: uses less canonical but still readable names.

The renamer is intentionally lightweight and text-based. For a camera-ready robustness study, inspect a sample of renamed code and consider an AST-based renamer as future work if necessary.

## 4. How to rerun evaluation

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_renamed.jsonl \
  --out_dir runs/real_50_renamed \
  --k_values 1,2,4 \
  --timeout 30
```

Default selection uses the Hard Selection Gate: only executable + Optimal candidates can receive a non-zero formal selection score.

## 5. Metrics to inspect

Compare original vs renamed runs on:

- executable rate;
- optimal rate;
- objective accuracy;
- structure completeness;
- inventory balance accuracy;
- missing Big-M rate;
- missing fixed-order-cost rate;
- missing capacity-constraint rate;
- average repair feedback count;
- evidence-strength distribution (`name_only`, `expression_supported`, `strong`).

## 6. If performance drops

A performance drop should be reported honestly. It means some rules still depend on recognizable naming. Emphasize that the hardened version caps name-only evidence and preserves certificates for diagnosis, but full naming invariance requires stronger graph matching and coefficient-pattern verification.

## 7. If performance is stable

If structure completeness and objective accuracy remain stable after renaming, this is a strong positive result. The paper can state that ReplenishVerifier is not merely matching canonical names; expression and incidence evidence preserve much of the signal under naming perturbations.

## 8. Suggested paper subsection

Chinese title:

> 命名变化鲁棒性实验

English title:

> Robustness to Naming Variations

Keep all result cells as `[TO FILL AFTER REAL LLM EXPERIMENT]` until the renamed-candidate evaluation is actually run on the server. Do not infer results from the existence of the script.
