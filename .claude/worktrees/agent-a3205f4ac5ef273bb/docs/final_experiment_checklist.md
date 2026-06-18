# Final Experiment Checklist for ReplenishVerifier

This checklist is the handoff from code hardening to real experiments. It does **not** contain experimental results. Keep every `[TO FILL AFTER REAL LLM EXPERIMENT]` result placeholder in the paper until the corresponding real run has completed.

## 1. Current completed engineering hardening

The current codebase has completed the planned defensive engineering pass:

- **`evidence_strength` layering**: rule certificates now distinguish `none`, `name_only`, `graph_supported`, `expression_supported`, `expression_and_graph`, and `strong` evidence.
- **Name-only is weak evidence**: a matching variable/constraint name alone is capped as weak evidence and cannot produce full structural credit.
- **Inventory balance index consistency**: lightweight checks inspect repeated/adjacent inventory state variables, order/demand/shortage terms, repeated self-cancellation patterns, and warnings.
- **Optional Big-M magnitude warning**: Big-M detection now includes a lightweight coefficient-ratio/magnitude check and warning, without claiming full bound-aware validation.
- **Weak graph evidence wording**: `LPStructureGraph` is documented as incidence-based auxiliary evidence, not complete graph matching or algebraic equivalence verification.
- **Hard Selection Gate**: formal selection scores are gated so that, by default, only executable + `Optimal` candidates can receive non-zero selection scores.
- **`prompt_builder` requires explicit PuLP constraint names**: prompts now prohibit anonymous constraints that PuLP exports as `_C1/_C2`.
- **Dry-run repair candidates**: repair generation supports `--dry_run`, writes uniform placeholder candidate code, and does not load/call an LLM.
- **Generic repair baseline**: repair generation supports `--repair_type generic` for generic execution/LP-artifact repair prompts.
- **Structure-aware repair prompt**: repair generation supports `--repair_type structure_aware` using ReplenishVerifier feedback and certificates.
- **Repair comparison script**: `replenishverifier.experiments.compare_repair_results` compares before/after evaluated candidate files.
- **Robustness naming variation guide**: `docs/robustness_naming_variation_guide.md` documents naming-perturbation experiments.
- **Paper draft safety wording**: English and Chinese drafts now include conservative wording about name-only evidence, graph evidence, expression-supported limitations, Hard Selection Gate, and repair claims.
- **`[TO FILL AFTER REAL LLM EXPERIMENT]` retained**: real-result placeholders remain in the paper; no repair or robustness results have been fabricated.

## 2. Conclusions that must not be written before real experiments

Do **not** write or imply the following claims until real LLM candidates and corresponding evaluations have completed:

- `ReplenishVerifier-Repair improves objective accuracy`.
- `ReplenishVerifier-Repair improves structure completeness`.
- `Structure-aware repair outperforms generic repair`.
- `Repair reduces missing Big-M / capacity / fixed-order-cost rates`.
- `Repair fixes feasible-but-wrong replenishment models`.
- `Repair does not degrade objective accuracy`.
- `Naming robustness is stable`.
- `ReplenishVerifier works robustly under randomized variable/constraint names`.
- `Real LLM case studies confirm the synthetic smoke-test pattern`.
- `Leakage Audit PASS` for the final real experiment.

Safe wording before experiments:

- “The code supports second-round repair candidate generation.”
- “The paper will report repair results after repaired candidates are generated and re-evaluated.”
- “Naming-variation robustness is part of the planned evaluation.”
- “Synthetic smoke tests are sanity checks only.”

## 3. Minimal real experiment workflow

### Step 1: Generate real LLM candidates

Run this on the server with the intended local model. This is the first step that actually uses the LLM.

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/benchmark/real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50.jsonl \
  --model /path/to/local/model \
  --k 4 \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95
```

Replace paths/model names with the actual server paths. Record model name, hardware, decoding parameters, and prompt version.

### Step 2: Run all methods

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50 \
  --k_values 1,2,4 \
  --timeout 30
```

Default selection uses the Hard Selection Gate. Do not pass `--allow_feasible_selection` for the main experiment unless the paper explicitly justifies that policy.

### Step 3: Run leakage audit

```bash
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_real_50
```

Do not write `Leakage Audit PASS` in the paper until this command passes on the final result directory.

### Step 4: Error analysis

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k4_real_50
```

Use this to quantify missing inventory balance, missing Big-M, missing capacity, solver-not-optimal, objective mismatch, and other selected-candidate errors.

### Step 5: Case studies

```bash
python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/qwen3_8b_k4_real_50
```

Case studies for the main paper should come from real LLM candidates, not synthetic smoke candidates.

### Step 6: Build paper tables

```bash
python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_real_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_real_50
```

Only copy tables to the paper after checking the generated CSV/Markdown and audit output.

## 4. Repair-loop workflow

Repair experiments are optional for the first main result, but required before making repair-effectiveness claims.

### Step 1: Generate structure-aware repaired candidates

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/benchmark/real_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_real_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_repaired_structure.jsonl \
  --model /path/to/local/model \
  --repair_type structure_aware
```

### Step 2: Generate generic repaired candidates

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/benchmark/real_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_real_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_repaired_generic.jsonl \
  --model /path/to/local/model \
  --repair_type generic
```

### Step 3: Re-evaluate repaired candidates

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_repaired_structure.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50_repaired_structure \
  --k_values 1,2,4 \
  --timeout 30

python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_repaired_generic.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50_repaired_generic \
  --k_values 1,2,4 \
  --timeout 30
```

### Step 4: Compare before and after repair

```bash
python -m replenishverifier.experiments.compare_repair_results \
  --before runs/qwen3_8b_k4_real_50/candidate_evaluations.jsonl \
  --after runs/qwen3_8b_k4_real_50_repaired_structure/candidate_evaluations.jsonl \
  --out runs/qwen3_8b_k4_real_50_repaired_structure/repair_comparison.json

python -m replenishverifier.experiments.compare_repair_results \
  --before runs/qwen3_8b_k4_real_50/candidate_evaluations.jsonl \
  --after runs/qwen3_8b_k4_real_50_repaired_generic/candidate_evaluations.jsonl \
  --out runs/qwen3_8b_k4_real_50_repaired_generic/repair_comparison.json
```

The comparison script only summarizes evaluated files. It does not prove repair success by itself; inspect aggregate metrics and case studies.

## 5. Naming-robustness workflow

### Step 1: Generate renamed candidates

```bash
python -m replenishverifier.experiments.rename_variables_for_robustness \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_renamed.jsonl \
  --mode random
```

Optional additional modes:

```bash
python -m replenishverifier.experiments.rename_variables_for_robustness \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_renamed_semantic.jsonl \
  --mode semantic

python -m replenishverifier.experiments.rename_variables_for_robustness \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_renamed_adversarial.jsonl \
  --mode adversarial
```

### Step 2: Rerun evaluation

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_renamed.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50_renamed \
  --k_values 1,2,4 \
  --timeout 30
```

### Step 3: Compare original vs renamed

Inspect:

- executable rate;
- optimal rate;
- objective accuracy;
- structure completeness;
- inventory balance accuracy;
- missing Big-M rate;
- missing fixed-order-cost rate;
- missing capacity-constraint rate;
- average repair feedback count;
- evidence-strength distribution if needed.

If renamed candidates break due to text-level renaming, inspect a sample and either document the limitation or implement a safer renaming procedure in future work. Do not force a robustness claim.

## 6. Code-entry completeness check

A lightweight static check confirms that the current experiment entry points exist:

| Purpose | Entry point | Status |
|---|---|---|
| Real candidate generation | `python -m replenishverifier.llm.run_generation` | Present |
| Main all-method evaluation | `python -m replenishverifier.experiments.run_all_methods` | Present |
| Hard Gate flag | `--allow_feasible_selection` in `run_all_methods` | Present, default false |
| Leakage audit | `python -m replenishverifier.experiments.audit_leakage` | Present |
| Error analysis | `python -m replenishverifier.experiments.analyze_error_types` | Present |
| Case study extraction | `python -m replenishverifier.experiments.extract_case_studies` | Present |
| Paper table generation | `python -m replenishverifier.experiments.build_paper_tables` | Present |
| Structure-aware repair generation | `python -m replenishverifier.llm.run_repair_generation --repair_type structure_aware` | Present |
| Generic repair generation | `python -m replenishverifier.llm.run_repair_generation --repair_type generic` | Present |
| Repair dry run | `python -m replenishverifier.llm.run_repair_generation --dry_run` | Present |
| Repair before/after comparison | `python -m replenishverifier.experiments.compare_repair_results` | Present |
| Naming robustness candidate generation | `python -m replenishverifier.experiments.rename_variables_for_robustness` | Present |

No additional large code feature is required before starting real experiments.

## 7. Success criteria before paper update

Before updating the paper’s result sections, check these criteria:

- Main table contains real LLM results, not synthetic smoke results.
- Formal selection rows use no reference objective for ranking.
- Hard Selection Gate is active in the main run.
- Leakage audit passes on the final experiment directory.
- ReplenishVerifier-Full improves or meaningfully changes structure completeness compared with generic baselines.
- Case studies show at least one Solver-Filter or generic-baseline failure involving replenishment structure.
- Case studies include examples where SIRL-like LP-Stats or OptArgus-like Audit misses replenishment-specific errors.
- If repair is reported, repaired candidates were actually generated and re-evaluated.
- If repair is reported, missing-structure rates decrease for at least one key structure such as Big-M, capacity, inventory balance, or fixed-order cost.
- If repair is reported, objective accuracy does not collapse; if it drops, the trade-off is discussed honestly.
- At least 3 real case studies are available for Section 7 or appendix.

## 8. What to do if results are weak

- **All candidates are too good**: use a weaker model, smaller model, higher temperature, or a plainer prompt without expected-structure hints. The goal is to expose realistic modeling failures.
- **All candidates are too bad**: reduce difficulty, start with easy/medium problem types, lower K, inspect generation formatting, or improve only the prompt interface without changing the verifier claims.
- **Structure metrics are high but objective accuracy is poor**: write this as a limitation. Structure correctness is not sufficient for full mathematical correctness; coefficient, time-index, and boundary-condition errors remain possible.
- **Repair makes results worse**: do not report repair as a main positive result. Use repair prompts and failure cases as analysis or appendix material.
- **Naming robustness is poor**: report the sensitivity as a limitation and avoid strong robustness claims. State that stronger graph matching, role inference, and coefficient-pattern verification are future work.
- **Leakage audit fails**: fix the result construction or selection policy before using the run. Do not paper over leakage failures.
- **No good real case studies appear**: expand the sample, use a weaker model, or move the claim to a more conservative aggregate-only discussion.

## 9. Recommended run priority

### First priority

Run the minimum publishable real experiment:

- `real_50 + K=4`;
- main comparison through `run_all_methods`;
- leakage audit.

### Second priority

Run qualitative and diagnostic analysis:

- error analysis;
- case studies;
- paper table generation.

### Third priority

Run the repair loop:

- structure-aware repair generation;
- generic repair generation;
- repaired-candidate re-evaluation;
- before/after repair comparison.

### Fourth priority

Run robustness and overhead analyses:

- naming variation robustness;
- runtime overhead;
- optional larger benchmark or appendix ablations.

## Final recommendation

The code now has the needed defensive mechanisms and experiment entry points. It does not need another large method redesign before the real experiments. The next step should be to run the smallest real LLM experiment (`real_50`, `K=4`), audit leakage, inspect error types and case studies, and only then update the paper’s `[TO FILL AFTER REAL LLM EXPERIMENT]` result sections.
