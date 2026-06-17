# ReplenishVerifier

> **ReplenishVerifier: Constraint-Level LP-Structure Verification for LLM-Based Supply Chain Replenishment Optimization Modeling**  
> **ReplenishVerifier：面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证方法**

ReplenishVerifier is a research prototype for auditing LLM-generated optimization models in **supply chain replenishment**. It targets a concrete failure mode: generated PuLP/Python code can be executable, return solver status `Optimal`, and even agree with other candidates on objective values, while still omitting required replenishment structures such as inventory balance, capacity constraints, shortage/backlog variables, fixed ordering cost, binary setup/order triggers, or Big-M linking constraints.

The core thesis is:

> Correct optimization modeling requires constraint-level semantic structure, not only executable solver code or objective-value consensus. ReplenishVerifier verifies these structures from the LP artifact induced by generated code and uses the evidence for no-reference candidate selection, feedback, repair prompting, and future preference-data construction.

Formal candidate selection **must not use `reference_objective`**. Reference objectives are evaluation-only and may be used only after selection for metrics such as objective accuracy and relative error.

---

## What the current code implements

The repository currently supports the following pipeline:

1. Generate replenishment benchmark rows with natural-language prompts, sampled parameters, reference PuLP models, and replenishment-specific semantic metadata.
2. Execute LLM-generated PuLP candidates and export their induced `.lp` artifacts.
3. Parse LP artifact sections: objective, constraints, variable names, binary declarations, and bounds.
4. Check problem-type-aware required / optional replenishment structures.
5. Emit rule-level structure certificates with evidence, missing reasons, and repair hints.
6. Select candidates using no-reference policies.
7. Build generic or replenishment-specific repair prompts.
8. Build verifier-guided preference pairs for future training data.

The project is **not** a general LLM-for-OR agent, not a complete mathematical-equivalence checker, not a faithful reproduction of SIRL / OR-R1 / OptArgus / OptiRepair, and not an already completed DPO/RL training system.

All `*-like` methods are **lightweight signal-isolation baselines**. They are included to isolate whether generic execution, LP statistics, objective consensus, audit, or repair-prompt signals explain the gains; they are not faithful reproductions of the original systems.

---

## Repository layout

```text
replenishverifier/
  benchmark/            # schemas, templates, generator, semantic benchmark fields
  data/                 # problem-type-aware replenishment structure schema
  solver/               # PuLP runner and generated-code executor
  verifier/             # LP parser, LP graph evidence, structure rules, feedback
  pipeline/             # scoring utilities
  experiments/          # method selection, baselines, evaluation, tables, audits
  llm/                  # prompt building, code extraction, generation, repair generation

scripts/                # lightweight CLI entry points
papers/                 # Chinese and English paper drafts
docs/                   # experiment plans, risk audits, revision roadmap
runs/                   # smoke/demo and future real experiment outputs
data/generated/         # generated benchmark splits
data/candidates/        # candidate JSONL files
```

---

## Benchmark schema and generated fields

Supported problem types:

| problem_type | Required replenishment semantics |
|---|---|
| `single_period_newsvendor` | demand satisfaction, order quantity, ending inventory, shortage variable, ordering / holding / shortage costs |
| `single_item_multi_period` | period-indexed orders and inventory, inventory balance, ordering and holding costs |
| `single_item_multi_period_shortage` | inventory balance with shortage/backlog variables and shortage penalty |
| `multi_item_capacity` | item and period sets, item volume, shared storage capacity, per-period capacity constraints |
| `fixed_order_cost_big_m` | binary order trigger, fixed ordering cost, and Big-M linking constraint |

Generated benchmark rows now include replenishment-specific fields:

- `semantic_frame`: domain-specific frame with sets, parameters, decision variables, objective terms, constraints, solver type, replenishment structures, required structures, and optional structures.
- `replenishment_entities`: extracted replenishment entities such as demand, initial inventory, periods, items, order quantity, inventory level, shortage/backlog, costs, storage capacity, item volume, Big-M, and lead time when present.
- `replenishment_modeling_steps`: deterministic LP-structure-grounded steps for labeled benchmark rows. Unlabeled prompt rows omit this field by default to avoid leaking the modeling process.

The generator validates each row with lightweight rules and raises `ValueError` on malformed rows. It does not call an LLM during validation.

---

## Problem-type-aware structure schema

`replenishverifier/data/structure_schema.py` defines `EXPECTED_STRUCTURES_BY_TYPE`. Each problem type has:

- `required`: structures included in the main structure score;
- `optional`: structures reported in certificates but excluded from the main score denominator;
- `forbidden`: explicit metadata reserved for future diagnostics.

Current structure keys include inventory balance, order variables, inventory variables, shortage variables, capacity constraints, binary order variables, Big-M constraints, lead time, order cost, holding cost, shortage cost, fixed order cost, demand satisfaction, nonnegative bounds, and objective minimization.

If a benchmark instance has truthy `expected_structures`, those keys override the default required set for that instance. Otherwise the problem-type schema is used as fallback.

---

## Method and selection policies

Core ReplenishVerifier scoring uses candidate-observable signals only:

```text
0.25 executable
+ 0.25 optimal solver status
+ 0.35 required replenishment structure score
+ 0.15 semantic consistency
```

The hard selection gate gives non-zero formal selection score only to executable + `Optimal` candidates by default. Structure certificates are still retained for failed candidates for diagnosis and repair.

Implemented methods include:

- `Direct`
- `Best-of-K`
- `Solver-Filter`
- `OR-R1-like Voting` — lightweight executable / valid-code / objective-consensus baseline; no replenishment structures; no reference objective.
- `SIRL-like LP-Stats` — lightweight generic LP-artifact statistics baseline; no replenishment structures.
- `OptArgus-like Audit` — lightweight generic optimization-model audit baseline; no inventory-specific checks.
- `OptiRepair-like Repair-Prompt` — lightweight generic repair-readiness / feedback baseline; no replenishment-specific feedback.
- `Structure-Only`
- `Structure-Grounded Consistency` — ReplenishVerifier-style selector using execution, solver status, LP artifact structure coverage, required replenishment structures, and candidate objective consensus; no reference objective.
- `ReplenishVerifier-Full`
- `ReplenishVerifier-Repair` — should be reported as actual repair only after real repaired candidates are generated and re-evaluated.

`--use_objective_consensus` is optional and uses only candidate-objective clustering within the same problem. It never uses `reference_objective` and should be treated as an appendix ablation unless explicitly made part of the final method.

---

## Pre-experiment protocol safeguards

Candidate generation supports `--prompt_type hidden_verifier|plain|structured`.

- `hidden_verifier` is the recommended main-experiment setting. It hides `expected_structures`, keeps the PuLP solve/export contract, and asks for clear variable/constraint names without exposing required replenishment structure labels.
- `plain` hides `expected_structures` and gives the natural-language problem plus JSON parameters. Parameters are provided so generated PuLP code can build an executable instance model.
- `structured` exposes expected structures and is only for guided generation or appendix ablations. It must not be used as the default main-experiment prompt.

Generation rows should save raw generations, `prompt_type`, seed, decoding parameters, and model path/version/hash where available. Seeds improve reproducibility, but exact determinism is not guaranteed across GPU sampling, Transformers backends, CUDA kernels, hardware, or model versions.

`run_all_methods` writes both structure-aware `repair_prompts.*` and generic `generic_repair_prompts.*`. Generic repair uses execution/solver/audit feedback only and intentionally avoids replenishment-specific missing-structure labels. Structure-aware repair may use missing required structures, rule certificates, and replenishment repair hints.

Runtime overhead is a required future reporting metric. Use `python -m replenishverifier.experiments.analyze_runtime_overhead --exp_dir <exp_dir>` after an evaluation run to summarize total candidate evaluation time, LP parse time, and structure-check time. Missing timing fields are reported as `NA`; no runtime numbers should be invented before real experiments.

Variable-renaming robustness uses `rename_variables_for_robustness.py` as a lightweight text-level perturbation. It is not AST-safe renaming and should be manually spot-checked before formal experiments.

Preference pairs exported by `build_preference_data.py` are future DPO/PRM/LoRA-style learning signals. They do not imply that any SFT, DPO, PRM, RL, LoRA, or TGRPO training has been completed. Formal selection and preference construction do not use `reference_objective`; reference objectives are evaluation-only.

---

## Installation and tests

Python 3.10+ is expected.

```bash
python -m pip install -r requirements.txt
python -m pytest
```

If running local LLM generation or repair generation, install the required model stack separately, e.g. `torch`, `transformers`, and `accelerate`. Real LLM generation is intentionally not required for the unit tests.

---

## 中文实验路线：从简单到正式

下面按“最容易 → 最正式”的顺序说明怎么做实验、每一步产物是干嘛的、后续命令的路径怎么对应。正式论文结果只能来自真实 LLM candidates；demo/smoke 只能证明 pipeline 能跑通。

### 0. 路径命名规则先看懂

本项目命令基本遵循同一套路径传递关系：

```text
benchmark JSONL        -> --benchmark
candidate JSONL        -> --candidates
实验输出目录           -> --out_dir / --exp_dir
repair prompt JSONL    -> --repair_prompts
repaired candidate JSONL -> 下一轮 --candidates
```

常用对应关系：

| 文件或目录 | 谁生成 | 后面怎么用 | 用途 |
|---|---|---|---|
| `data/generated/test_50.jsonl` | `scripts/generate_benchmark.py` | 作为 `--benchmark` | 题目、参数、reference 信息、expected structures |
| `runs/lp/test_50/` | `scripts/generate_benchmark.py --lp-dir` | 一般不手动传给主实验 | 保存 reference LP，方便检查 benchmark/reference 是否正常 |
| `data/candidates/qwen3_8b_k4_50.jsonl` | `llm.run_generation` | 作为 `run_all_methods --candidates` | 真实 LLM 生成的 K 个候选代码 |
| `runs/qwen3_8b_k4_50/` | `experiments.run_all_methods` | 作为后续 `--exp_dir` | 主实验结果、candidate evaluations、repair prompts、summary |
| `runs/qwen3_8b_k4_50/repair_prompts.jsonl` | `run_all_methods` | 作为 structure-aware repair 的 `--repair_prompts` | 含补货结构反馈的 repair prompt |
| `runs/qwen3_8b_k4_50/generic_repair_prompts.jsonl` | `run_all_methods` | 作为 generic repair 的 `--repair_prompts` | 只含 generic execution/solver/audit feedback 的公平对照 |
| `data/candidates/qwen3_8b_k4_50_repaired.jsonl` | `llm.run_repair_generation` | 再作为 `run_all_methods --candidates` | 二轮修复后的 candidates |
| `runs/qwen3_8b_k4_50_repaired/` | 第二次 `run_all_methods` | 作为 repair 后结果目录 | 用来和 repair 前 `runs/qwen3_8b_k4_50/` 对比 |

命名建议：输入 candidate 文件和输出目录保持同一个实验名。例如：

```text
data/candidates/qwen3_8b_k4_50.jsonl
runs/qwen3_8b_k4_50/
runs/paper_tables_qwen3_8b_k4_50/
```

这样后续 `--candidates`、`--exp_dir`、`--out_dir` 不容易填错。

### 1. 最简单：只检查环境和单元测试

```bash
python -m pip install -r requirements.txt
python -m pytest
```

这一步不需要模型，也不会产生论文结果。它只回答：当前代码、parser、structure rules、baselines、runtime analyzer、repair prompt、preference data 等测试是否通过。

如果这一步失败，先修测试，不要继续做真实实验。

### 2. 生成一个小 benchmark，确认题目和 reference LP 正常

先跑一个很小的 split，例如每类 1 个：

```bash
python scripts/generate_benchmark.py \
  --output data/generated/test_small.jsonl \
  --lp-dir runs/lp/test_small \
  --n-per-type 1 \
  --seed 42
```

这一步的结果用于 sanity check：

- `data/generated/test_small.jsonl`：后面所有实验的 `--benchmark`。
- `runs/lp/test_small/`：reference PuLP model 导出的 LP 文件，用来检查 benchmark/reference 是否能正常构建。

如果只是调 pipeline，用小 split 就够了；正式实验再生成 `test_50.jsonl` 或更大的 split。

### 3. 检查 reference LP 的结构验证是否正常

```bash
python scripts/run_structure_verification.py \
  --benchmark data/generated/test_small.jsonl \
  --out runs/structure_check_test_small.jsonl
```

这一步是检查 verifier 本身：reference models 应该能提供 required structures 的证据。输出的 JSONL 可用来查看每个 problem 的 detected/missing/certificates。

如果 reference LP 都大量 missing，说明 benchmark schema、reference model、LP parser 或 structure rules 有问题，不应该继续跑 LLM 实验。

### 4. 跑 demo/synthetic candidates，只验证 pipeline 能否跑通

仓库里有一个轻量 demo candidate 文件：

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test.jsonl \
  --candidates data/candidates/demo_candidates.jsonl \
  --out_dir runs/demo_pipeline_check \
  --k_values 1,2,4 \
  --timeout 30
```

这一步的作用是检查主 pipeline：执行 candidate、导出 LP、parse LP、structure check、baseline selection、summary、repair prompts 是否能完整跑通。

不要把 `runs/demo_pipeline_check/` 当论文主结果。它只能说明“代码流程能跑”。

重点看这些文件：

- `runs/demo_pipeline_check/candidate_evaluations.jsonl`：每个候选的执行、LP parse、结构检测、runtime 字段。
- `runs/demo_pipeline_check/main_results.md`：各方法选出来的结果。
- `runs/demo_pipeline_check/summary.md`：方法级 summary。
- `runs/demo_pipeline_check/repair_prompts.jsonl`：structure-aware repair prompts。
- `runs/demo_pipeline_check/generic_repair_prompts.jsonl`：generic repair prompts。

### 5. 需要真实模型时：下载或指定模型路径

真实 LLM generation 才需要模型。推荐先用 Hugging Face 模型名直接跑；Transformers 会下载到本机缓存：

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

如果你想提前下载到固定目录，先安装 Hugging Face CLI，然后下载：

```bash
python -m pip install -U huggingface_hub
huggingface-cli download Qwen/Qwen3-8B \
  --local-dir /home/dongaorui/models/Qwen3-8B
```

之后把 `--model` 改成本地目录：

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/test_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50.jsonl \
  --model /home/dongaorui/models/Qwen3-8B \
  --k 4 \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --prompt_type hidden_verifier \
  --seed 42 \
  --trust_remote_code
```

路径匹配原则：

- `--benchmark` 必须指向已经生成的 benchmark JSONL，例如 `data/generated/test_50.jsonl`。
- `--out` 是新生成的 candidate JSONL，例如 `data/candidates/qwen3_8b_k4_50.jsonl`。
- `--model` 可以是 Hugging Face 模型名，也可以是本地模型目录；本地目录里应有 `config.json`、tokenizer 文件和模型权重。
- 主实验优先用 `--prompt_type hidden_verifier` 或 `plain`，不要把 `structured` 当主实验默认 prompt，因为它会显示 `expected_structures`。

如果模型需要登录权限，先在终端里执行：

```bash
huggingface-cli login
```

seed 能提高复现性，但 GPU sampling、Transformers 版本、CUDA kernel 和硬件差异可能导致不能完全 deterministic。正式实验要保存 raw generations、`prompt_type`、seed、decoding parameters 和模型路径/版本/hash。

### 6. 正式 evaluation：比较不同方法谁选得更好

真实 candidates 生成后，用同一个 benchmark 和 candidates 跑所有方法：

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out_dir runs/qwen3_8b_k4_50 \
  --k_values 1,2,4 \
  --timeout 30
```

这一步会把每个 candidate 执行并导出 LP，然后比较多种 selection 方法：

- `Direct`：直接取第一个候选。
- `Best-of-K`：从 K 个候选中选可用候选。
- `Solver-Filter`：只看 executable / Optimal / objective presence。
- `OR-R1-like Voting`：看候选间 objective consensus、可执行性、代码/LP 有效性。
- `SIRL-like LP-Stats`：只看 generic LP artifact statistics。
- `OptArgus-like Audit`：只做 generic objective/variables/constraints audit。
- `OptiRepair-like Repair-Prompt`：只用 generic repair-readiness feedback。
- `Structure-Only`：只看补货结构完整性。
- `ReplenishVerifier-Full`：看 execution、solver status、required replenishment structure、semantic consistency。

对比时主要看：

- `runs/qwen3_8b_k4_50/main_results.md` 和 `.csv`：每种方法最终选择的结果。
- `runs/qwen3_8b_k4_50/summary.md`：方法级汇总。
- `runs/qwen3_8b_k4_50/candidate_evaluations.jsonl`：每个候选的详细结构证据、missing structures、runtime。
- `runs/qwen3_8b_k4_50/ablation_results.*`：ablation 对比。
- `runs/qwen3_8b_k4_50/low_resource_results.*`：K=1/2/4 等低资源对比。

正式 selection 不使用 `reference_objective`。`reference_objective` 只能在最终 evaluation metric 中用来计算 objective accuracy / relative error。

跑完必须做 leakage audit：

```bash
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_50 \
  --write_report
```

如果 leakage audit 不通过，不要使用该实验结果写论文。

### 7. 生成论文表格、错误分析和 case studies

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_50
```

这些输出分别用于：

- error analysis：回答哪些补货结构最容易 missing。
- case studies：挑典型失败/成功样例写论文分析。
- paper tables：把实验结果整理成 Markdown/CSV/JSON 表格。

不要手填 paper table 数字；应从真实 `runs/<exp_dir>/` 生成。

### 8. 进阶：repair 对比

先用 structure-aware repair prompts 生成二轮候选：

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
  --repair_type structure_aware \
  --trust_remote_code
```

再用 generic repair prompts 做公平对照：

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/generated/test_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_50/generic_repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50_generic_repaired.jsonl \
  --model Qwen/Qwen3-8B \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --repair_type generic \
  --trust_remote_code
```

然后分别重新 evaluation：

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50_repaired.jsonl \
  --out_dir runs/qwen3_8b_k4_50_repaired \
  --k_values 1,2,4 \
  --timeout 30

python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50_generic_repaired.jsonl \
  --out_dir runs/qwen3_8b_k4_50_generic_repaired \
  --k_values 1,2,4 \
  --timeout 30
```

对比方式：

```bash
python -m replenishverifier.experiments.compare_repair_results \
  --before runs/qwen3_8b_k4_50/candidate_evaluations.jsonl \
  --after runs/qwen3_8b_k4_50_repaired/candidate_evaluations.jsonl
```

只有真实生成 repaired candidates 并重新评估后，才能说“repair 结果”；否则只能说“repair prompt generation”。

### 9. 进阶：runtime overhead、命名鲁棒性、preference data

Runtime overhead：

```bash
python -m replenishverifier.experiments.analyze_runtime_overhead \
  --exp_dir runs/qwen3_8b_k4_50
```

输出：

- `runs/qwen3_8b_k4_50/runtime_overhead.md`
- `runs/qwen3_8b_k4_50/runtime_overhead.csv`
- `runs/qwen3_8b_k4_50/runtime_overhead.jsonl`

它回答 verifier 额外开销是多少。字段缺失会显示 `NA`，不要编数字。

命名鲁棒性：

```bash
python -m replenishverifier.experiments.rename_variables_for_robustness \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50_renamed_random.jsonl \
  --mode random \
  --seed 42

python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50_renamed_random.jsonl \
  --out_dir runs/qwen3_8b_k4_50_renamed_random \
  --k_values 1,2,4 \
  --timeout 30
```

这只是 lightweight text-level perturbation，不是完整 AST-safe renaming。正式使用前要抽样人工检查 renamed code 是否仍合理。

Preference data：

```bash
python -m replenishverifier.experiments.build_preference_data \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out runs/qwen3_8b_k4_50/preference_pairs.jsonl \
  --min_score_gap 0.10 \
  --max_pairs_per_problem 3
```

它生成 chosen/rejected pairs，未来可用于 DPO/PRM/reranker/LoRA 等训练。但在真正训练并评估前，不能声称 ReplenishVerifier-DPO、PRM 或 LoRA 有提升。

---

## Benchmark generation

Labeled benchmark split:

```bash
python scripts/generate_benchmark.py \
  --output data/generated/test_50.jsonl \
  --lp-dir runs/lp/test_50 \
  --n-per-type 10 \
  --seed 42
```

Unlabeled prompt-only rows:

```bash
python scripts/generate_benchmark.py \
  --output data/generated/prompts_50.jsonl \
  --n-per-type 10 \
  --seed 42 \
  --unlabeled
```

Unlabeled rows omit `reference_code`, `reference_objective`, and `expected_structures`. They also omit `replenishment_modeling_steps` by default. Use `--include-modeling-steps` only for explicit process-supervision data export.

The parameter RNG and language-template RNG are separated; language template selection does not affect sampled parameters or reference objectives.

---

## Real LLM experiment workflow

Do **not** use smoke/demo runs as main paper evidence. Main claims require real LLM candidates.

Example generation command, to be run only when real experiments are intended:

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

Evaluation workflow after real candidates exist:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out_dir runs/qwen3_8b_k4_50 \
  --k_values 1,2,4 \
  --timeout 30

python -m replenishverifier.experiments.analyze_error_types --exp_dir runs/qwen3_8b_k4_50
python -m replenishverifier.experiments.extract_case_studies --exp_dir runs/qwen3_8b_k4_50
python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_50
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_50 \
  --write_report
```

The leakage audit must pass before results are used in the paper.

---

## Repair and preference data

Repair prompts are generated from missing required structures. Actual repair claims require a second LLM generation pass and re-evaluation:

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

If this step is not run and evaluated, write only “repair prompt generation,” not “repair result.”

Verifier-guided preference pairs can be built for future DPO / PRM / reranker experiments:

```bash
python -m replenishverifier.experiments.build_preference_data \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out runs/qwen3_8b_k4_50/preference_pairs.jsonl \
  --min_score_gap 0.10 \
  --max_pairs_per_problem 3
```

Preference data is future training data; it is not evidence that DPO, PRM, or RL training has already been completed.

---

## Synthetic smoke tests

Synthetic/demo smoke tests are allowed only for checking that the pipeline runs end to end. They must not be reported as main empirical results.

Existing smoke outputs under `runs/smoke_*` and `runs/paper_tables_*` are sanity-check artifacts. Any main-table value in a paper draft must remain:

```text
[TO FILL AFTER REAL LLM EXPERIMENT]
```

until real LLM experiments are completed and audited.

---

## Known limitations

- The LP parser depends on PuLP LP format.
- Structure verification is heuristic and is not full mathematical-equivalence verification.
- The verifier may miss coefficient errors, index errors, boundary-condition errors, or invalid Big-M magnitudes.
- The benchmark currently covers only a small set of replenishment model families.
- Selection weights are hand-designed and should later be learned or calibrated.
- Repair effectiveness requires real repaired LLM candidates and re-evaluation.
- Preference pairs do not imply completed DPO / PRM / RL training.
- All `*-like` baselines are lightweight signal-isolation baselines, not faithful reproductions.
- Executing external generated code is risky; untrusted candidates should be run in a sandbox.

---

## Documentation for submission preparation

- `docs/ccfa_revision_roadmap.md` — roadmap for moving from current prototype to a stronger submission.
- `docs/submit_readiness_checklist.md` — code, documentation, real LLM experiment, paper, and CCF-A risk checklist.
- `docs/real_llm_experiment_checklist.md` — real experiment protocol.
- `docs/paper_experiment_revision_plan.md` — paper table and baseline design plan.
- `docs/code_and_claim_risk_audit.md` — code/claim consistency and leakage-risk audit.
