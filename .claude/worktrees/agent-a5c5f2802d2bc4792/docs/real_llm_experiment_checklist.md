# Real LLM experiment checklist

This checklist gives a reproducible path from real LLM candidate generation to tables and second-round repair for:

> ReplenishVerifier: Constraint-Level LP-Structure Verification for LLM-Based Supply Chain Replenishment Optimization Modeling

It assumes package name `replenishverifier`. Do not fill paper tables with synthetic/demo numbers. All unfinished results must remain `[TO FILL AFTER REAL LLM EXPERIMENT]`.

## 0. Principle

Formal candidate selection must not use `reference_objective`. Reference objectives are only for final metrics such as objective accuracy and relative error. Always run leakage audit after experiments.

## 1. Generate benchmark split

Example 50-instance test split:

```bash
python scripts/generate_benchmark.py \
  --output data/generated/test_50.jsonl \
  --lp-dir runs/lp/test_50 \
  --n-per-type 10 \
  --seed 42
```

For a larger run, increase `--n-per-type` and record the seed.

## 2. Generate K real LLM candidates

Example with Qwen3-8B:

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/test_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50.jsonl \
  --model Qwen/Qwen3-8B \
  --k 4 \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --prompt_type hidden_verifier \
  --seed 42 \
  --trust_remote_code
```

Use `hidden_verifier` or `plain` for main experiments because they do not reveal `expected_structures`. Reserve `structured` for guided generation or appendix ablations only. The seed improves reproducibility, but exact determinism is not guaranteed across GPU sampling, Transformers backends, CUDA kernels, hardware, or model versions.

Record in the paper:

- model name/path and version;
- hardware;
- K;
- temperature/top-p/max tokens;
- prompt template;
- whether expected structures are shown to the generator;
- extraction strategy (`code_extractor.py`).

## 3. Run all selection methods

Main no-reference selection run:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out_dir runs/qwen3_8b_k4_50 \
  --k_values 1,2,4 \
  --timeout 30
```

Optional objective-consensus ablation for ReplenishVerifier-Full:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out_dir runs/qwen3_8b_k4_50_consensus \
  --k_values 1,2,4 \
  --timeout 30 \
  --use_objective_consensus
```

`--use_objective_consensus` uses only candidate objective clustering, not the reference objective. Treat it as appendix ablation unless it is central to the paper.

## 4. Analyze outputs

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_50

python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.analyze_runtime_overhead \
  --exp_dir runs/qwen3_8b_k4_50
```

The leakage audit must pass before using the results. Runtime overhead is a future reporting metric; missing timing fields are reported as `NA` and must not be replaced with invented values.

## 5. Main-table recommendation

Use real LLM candidates for the main table:

- `Direct`
- `Best-of-K`
- `Solver-Filter`
- `OR-R1-like Voting`
- `SIRL-like LP-Stats`
- `OptArgus-like Audit`
- `Structure-Grounded Consistency`
- `ReplenishVerifier-Full`

Add `ReplenishVerifier-Repair` to the main table only after running actual second-round repair candidates and evaluating them. Treat every `*-like` baseline as a lightweight signal-isolation baseline, not a faithful reproduction.

Keep these in appendix unless space allows:

- `Structure-Only`
- `OptiRepair-like Repair-Prompt`
- `ReplenishVerifier-Full + objective consensus`
- synthetic/demo smoke results

## 6. Generate second-round repair candidates

After `run_all_methods`, use `repair_prompts.jsonl` for structure-aware repair. For the fair generic-control repair run, use `generic_repair_prompts.jsonl` and pass `--repair_type generic`; generic repair prompts use execution/solver/audit feedback only and do not expose replenishment-specific missing-structure labels.

Structure-aware example:

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/generated/test_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50_repaired.jsonl \
  --model Qwen/Qwen3-8B \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --trust_remote_code
```

Generic-control example uses the same entry point with a different prompt file:

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/generated/test_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_50/generic_repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50_generic_repaired.jsonl \
  --model Qwen/Qwen3-8B \
  --repair_type generic \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --trust_remote_code
```

Then evaluate repaired candidates:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50_repaired.jsonl \
  --out_dir runs/qwen3_8b_k4_50_repaired \
  --k_values 1,2,4 \
  --timeout 30

python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_50_repaired
```

For the paper, call this “second-round LLM repair” only if this generation and evaluation step is actually run. Otherwise call it “repair prompt generation.”

## 7. Case study selection

Use case studies from real LLM runs where:

1. a generic baseline selects an executable/optimal candidate;
2. the selected candidate misses a replenishment structure such as inventory balance, capacity, or Big-M;
3. `ReplenishVerifier-Full` selects a structurally complete candidate;
4. the baseline did not use reference objective.

Synthetic demo cases are useful for method illustration but should not be the primary evidence in the main paper.

## 8. Reporting checklist

Report:

- benchmark size and problem types;
- candidate-generation settings;
- timeout and solver backend;
- all compared method definitions;
- whether `--use_objective_consensus` is enabled;
- leakage audit result;
- summary table path;
- case study source path;
- limitations: heuristic LP parsing, variable-name sensitivity, no coefficient/index proof, and synthetic smoke results not being main evidence.
