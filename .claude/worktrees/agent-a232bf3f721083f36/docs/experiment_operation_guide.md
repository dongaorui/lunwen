# ReplenishVerifier 实验操作指南

生成日期：2026-06-14

本文档用于以后在服务器或更强电脑上按步骤运行 ReplenishVerifier 论文实验。本文只说明实验怎么做、做完看什么文件、每个指标有什么用；不包含真实实验结果，也不编造任何数值结论。

重要约束：

- 不要把 synthetic demo candidates 当作主实验结果；
- 不要在 selection 阶段使用 `reference_objective`；
- 不要把 Oracle 方法放入主表；
- 不要在本地弱机器上强行跑真实 LLM 大实验；
- 正式结果进入论文前必须通过 leakage audit；
- 所有耗时的 LLM generation / repair generation 建议放到服务器或 GPU 机器上运行。

> 当前代码中的 LLM 生成入口是 `python -m replenishverifier.llm.run_generation`。如果后续新增 `replenishverifier.llm.generate_candidates` alias，也可以把命令替换成该入口。本文命令优先使用当前实际存在的模块名。

---

## 1. 实验整体目标

这篇论文的实验要证明：

1. **RQ1 / Candidate selection：** ReplenishVerifier 是否能比 Direct、Best-of-K、Solver-Filter 更好地选择结构正确的库存补货优化模型。
2. **RQ2 / Strong baseline comparison：** ReplenishVerifier 是否比 SIRL-like LP-Stats、OptArgus-like Audit、OR-R1-like Voting 更能发现 replenishment-specific missing structures。
3. **RQ3 / Repair usefulness：** ReplenishVerifier-Repair 的结构反馈是否比 generic repair prompt 更有用。
4. **RQ4 / No answer leakage：** 整个 candidate selection 是否没有使用 reference objective。
5. **RQ5 / Practicality：** LP structure verification 的额外运行开销是否可接受。

核心思想是：solver feedback 能发现代码运行错误、求解失败和一部分 infeasible / invalid model，但它不一定能发现“模型能求解但缺少库存平衡、缺少 Big-M、缺少 fixed ordering cost”等补货语义结构错误。ReplenishVerifier 的实验要证明 LP artifact 级别的 replenishment-specific structure verification 能补上这类信号。

---

## 2. 实验总流程

```text
Benchmark generation
→ Real LLM candidate generation
→ Candidate execution and LP export
→ Method comparison
→ Error type analysis
→ Case study extraction
→ Repair candidate generation
→ Repair comparison
→ Low-K analysis
→ Robustness analysis
→ Runtime overhead analysis
→ Leakage audit
→ Paper table generation
```

每一步作用：

1. **Benchmark generation**：生成带 reference PuLP code、reference LP、`expected_structures` 和 `reference_objective` 的标准库存补货问题。
2. **Real LLM candidate generation**：用真实 LLM 生成每个问题的 K 个候选 PuLP 模型代码，避免主实验只依赖 synthetic demo。
3. **Candidate execution and LP export**：执行候选代码、调用 solver、导出 LP artifact，并记录 executable / status / objective / LP path。
4. **Method comparison**：比较 Direct、Best-of-K、Solver-Filter、OR-R1-like、SIRL-like、OptArgus-like、OptiRepair-like、Structure-Only、ReplenishVerifier-Full 等方法选择的候选质量。
5. **Error type analysis**：分析不同方法选中的模型主要错在哪里，尤其关注 replenishment-specific missing structures。
6. **Case study extraction**：抽取适合写进论文的真实案例，展示 baseline 看起来能跑但缺关键结构，而 ReplenishVerifier 能指出结构缺失。
7. **Repair candidate generation**：基于结构反馈生成二轮修复候选，与 generic repair prompt 对比。
8. **Repair comparison**：比较 repair 前后结构完整性、执行率、Optimal rate 和 objective accuracy 是否改善或退化。
9. **Low-K analysis**：分析 K=1/2/4 时选择空间变小时方法是否仍然有增益。
10. **Robustness analysis**：检查变量名随机化或重命名后 verifier 是否仍能检测结构，回应“是否过度依赖变量名”的质疑。
11. **Runtime overhead analysis**：分解 code execution、solver、LP export、LP parsing、structure checking 的时间，证明额外开销可接受。
12. **Leakage audit**：证明 formal selection 不偷用 reference objective，也不把答案用于候选选择。
13. **Paper table generation**：把实验结果整理成论文主表、baseline 表、ablation 表、low-K 表、error type 表和 case study 表。

---

## 3. 实验一：Benchmark 生成实验

### 目的

生成标准库存补货问题，包括五类问题：

1. `single_period_newsvendor`
2. `single_item_multi_period`
3. `single_item_multi_period_shortage`
4. `multi_item_capacity`
5. `fixed_order_cost_big_m`

每条样本应包含自然语言描述、参数、reference PuLP code、reference LP 路径、reference objective 和 expected structures。

### 推荐命令

```bash
python scripts/generate_benchmark.py \
  --output data/generated/real_50.jsonl \
  --lp-dir runs/lp/real_50 \
  --n-per-type 10 \
  --seed 42
```

### 输出文件

- `data/generated/real_50.jsonl`
- `runs/lp/real_50/`

### 做完后看什么

检查：

1. 是否总共有 50 条；
2. 每类问题是否 10 条；
3. 每条是否有 `natural_language`；
4. 每条是否有 `expected_structures`；
5. 每条是否有 `reference_objective`；
6. 每条是否有 reference LP；
7. reference solver status 是否是 `Optimal`；
8. `reference_lp_path` 指向的 LP 文件是否存在。

可以写一个轻量检查脚本或用 Python 单行读取 JSONL 统计，但不要把检查结果写成论文结果。

### 指标/字段有什么用

- `expected_structures`：用于判断结构完整性，是 ReplenishVerifier 的核心监督信号。
- `reference_objective`：只能用于最终 evaluation，不能用于 selection。
- `problem_type`：用于分类型分析，说明哪些补货结构最难。
- `difficulty`：用于难度分析，观察方法在 easy / medium / hard 上是否稳定。
- `reference_lp_path`：用于检查 reference LP 是否可解析，以及后续对照结构规则。

---

## 4. 实验二：真实 LLM 候选代码生成实验

### 目的

生成真实 LLM candidates。论文主实验不能只用 synthetic demo candidates。

每个 benchmark problem 生成 K 个候选代码，后续 Best-of-K、Voting、Solver-Filter 和 ReplenishVerifier selection 都需要同一候选池。

### 推荐命令

当前代码实际入口：

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/real_50.jsonl \
  --model Qwen/Qwen3-8B \
  --out data/candidates/qwen3_8b_k4_real_50.jsonl \
  --k 4 \
  --temperature 0.7 \
  --top_p 0.9 \
  --max_new_tokens 2048 \
  --prompt_type hidden_verifier \
  --seed 42 \
  --trust_remote_code
```

如果后续新增 `generate_candidates` alias，则可使用：

```bash
python -m replenishverifier.llm.generate_candidates \
  --benchmark data/generated/real_50.jsonl \
  --model Qwen/Qwen3-8B \
  --out data/candidates/qwen3_8b_k4_real_50.jsonl \
  --k 4 \
  --temperature 0.7 \
  --top_p 0.9 \
  --max_new_tokens 2048 \
  --seed 42 \
  --prompt_type hidden_verifier
```

> 注意：主实验推荐 `--prompt_type hidden_verifier` 或 `plain`，二者都不暴露 `expected_structures`。`structured` 会显示 expected structures，只能用于 guided generation 或 appendix ablation，不能作为主实验默认设置。seed 能提高可复现性，但 GPU sampling、Transformers backend、CUDA kernel、硬件和模型版本可能导致完全 deterministic 不能保证；正式实验应保存 raw generations、prompt_type、seed、decoding parameters 和 model path/hash。

### 输出文件

- `data/candidates/qwen3_8b_k4_real_50.jsonl`

### 做完后看什么

检查：

1. 每个 `problem_id` 是否有 4 个 candidates；
2. `generated_code` 是否为空；
3. `error` 或 `generation_error` 是否过多；
4. 是否有模型输出非 Python 代码；
5. 是否有代码没有使用 PuLP；
6. prompt 是否过度泄漏 `expected_structures`；
7. 输出 JSONL 中是否保留了 prompt，方便后续 leakage / prompt audit。

### 指标有什么用

- **生成成功率**：说明模型能不能稳定生成代码。
- **空代码比例**：说明 code extraction 是否有问题。
- **K=4**：为 Best-of-K、Voting、ReplenishVerifier selection 提供候选空间。
- **plain_prompt**：避免把 verifier 规则直接告诉模型，否则优势不明显。

### 服务器建议

这个实验需要加载 LLM，是最应该放到服务器或 GPU 机器上跑的步骤之一。本地弱机器只建议用 `--max_samples 1` 或小模型做格式 smoke check，不建议跑正式结果。

---

## 5. 实验三：候选执行、LP 导出与方法比较

### 目的

执行真实 LLM 生成的候选代码，导出 LP artifact，解析 LP，并比较所有 selection 方法。这个实验支撑论文 Main Results 和 Strong Baseline Comparison。

### 推荐命令

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50 \
  --k_values 1,2,4 \
  --timeout 30 \
  --no_demo_if_empty
```

可选 objective-consensus ablation：

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50_consensus \
  --k_values 1,2,4 \
  --timeout 30 \
  --no_demo_if_empty \
  --use_objective_consensus
```

`--no_demo_if_empty` 很重要：正式实验中，如果 candidate file 为空，应该失败，而不是自动生成 synthetic demo candidates。

### 输出文件

`runs/qwen3_8b_k4_real_50/` 下重点看：

- `candidate_evaluations.jsonl`
- `candidate_evaluations.csv`
- `candidate_evaluations.md`
- `main_results.jsonl`
- `main_results.csv`
- `main_results.md`
- `ablation_results.jsonl`
- `ablation_results.csv`
- `ablation_results.md`
- `low_resource_results.jsonl`
- `low_resource_results.csv`
- `low_resource_results.md`
- `difficulty_results.jsonl`
- `difficulty_results.csv`
- `difficulty_results.md`
- `benchmark_summary.jsonl`
- `benchmark_summary.csv`
- `benchmark_summary.md`
- `repair_prompts.jsonl`
- `repair_prompts.csv`
- `repair_prompts.md`
- `summary.md`
- `manifest.json`
- `candidate_runs/`
- `candidate_runs_k1/`、`candidate_runs_k2/`、`candidate_runs_k4/`

### 重点比较方法

- `Direct`
- `Best-of-K`
- `Solver-Filter`
- `OR-R1-like Voting`
- `SIRL-like LP-Stats`
- `OptArgus-like Audit`
- `OptiRepair-like Repair-Prompt`
- `Structure-Only`
- `ReplenishVerifier-Full`
- `ReplenishVerifier-Repair`

### 主要指标与用途

#### Executable Rate

代码能不能运行。

作用：

- 衡量 LLM 生成代码的基本可靠性；
- Direct 如果低，说明原始模型代码能力不足；
- Solver-Filter 通常会提高这个指标。

#### Optimal Rate

solver 是否返回 `Optimal`。

作用：

- 衡量候选是否能形成可求解模型；
- Hard Selection Gate 默认要求正式 selection 只能选择 executable + Optimal candidates；如需允许 feasible，必须显式传入 `--allow_feasible_selection`，默认不要开启；
- 如果 Optimal Rate 很低，说明模型生成的 PuLP 质量差或 benchmark 太难。

#### Objective Accuracy

候选目标值和 reference objective 的接近程度。

作用：

- 只能用于最终 evaluation；
- 不能用于 candidate selection；
- 用来判断结构正确之外，目标值是否也接近参考模型。

注意：如果 ReplenishVerifier 的 Structure Completeness 高，但 Objective Accuracy 低，说明结构正确不是完整数学正确，可能还有系数、索引或边界错误。

#### Relative Error

目标值相对误差。

作用：

- 比 Objective Accuracy 更细；
- 可看 mean、median、p90；
- 判断是否有少数极端错误。

#### Structure Completeness

required replenishment structures 被检测到的比例。

作用：

- 这是本文最核心指标；
- 用来证明 ReplenishVerifier 能选出结构更完整的候选；
- 应重点比较 ReplenishVerifier-Full vs Solver-Filter / SIRL-like / OptArgus-like。

#### Inventory Balance Accuracy

需要库存平衡的问题中，是否检测到库存平衡。

作用：

- 库存补货模型最核心结构；
- 如果 Solver-Filter 选中 Optimal 但缺 inventory balance，这是最强 case study。

#### Constraint Coverage

required structures / constraints 的宏平均覆盖率。

作用：

- 综合衡量结构覆盖；
- 比单个结构更稳定；
- 主表里应该重点报告。

#### Avg Runtime

平均运行时间。

作用：

- 证明 LP parsing + structure checking 的额外开销可接受；
- 如果比 solver execution 小很多，可以作为方法优势。

#### Avg Repair Feedback Count

平均修复反馈数量。

作用：

- 衡量 verifier 是否能产生可解释反馈；
- 不是越多越好；
- 要结合 error type 看，重点是反馈是否具体、有用。

---

## 6. 方法比较结果如何解释

### Main Results

主表应回答：ReplenishVerifier-Full 是否在 Structure Completeness、Constraint Coverage、Inventory Balance Accuracy 上优于 Direct、Best-of-K、Solver-Filter。

建议重点看：

- `main_results.md`
- `summary.md`
- `candidate_evaluations.md`

解释方式：

- 如果 ReplenishVerifier-Full 的 structure 指标更高，说明补货结构验证提供了 selection 增量；
- 如果 Objective Accuracy 也更高，说明结构信号和数学正确性有正相关；
- 如果 Structure Completeness 高但 Objective Accuracy 不高，要诚实说明 verifier 只验证 high-level structures，不保证系数、索引、边界完全正确。

### Strong Baseline Comparison

强 baseline 对比应回答：ReplenishVerifier 是否比 SIRL-like LP-Stats、OptArgus-like Audit、OR-R1-like Voting 更能发现 replenishment-specific missing structures。

解释方式：

- SIRL-like LP-Stats 可以看 LP artifact 是否完整，但不理解库存语义；
- OptArgus-like Audit 可以发现 generic objective/variable/constraint 问题，但不针对 inventory balance / Big-M / fixed ordering cost；
- OR-R1-like Voting 可以利用候选间 consensus，但如果多数候选犯同一个结构错误，Voting 也可能选错；
- ReplenishVerifier 的优势应体现在 replenishment-specific structures 上。

---

## 7. 实验四：错误类型分析

### 目的

分析不同方法选中的 candidate 错在哪里。

### 推荐命令

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k4_real_50
```

### 输出文件

- `runs/qwen3_8b_k4_real_50/error_type_summary.md`
- `runs/qwen3_8b_k4_real_50/error_type_summary.csv`
- `runs/qwen3_8b_k4_real_50/error_type_summary.jsonl`
- `runs/qwen3_8b_k4_real_50/error_type_details.md`
- `runs/qwen3_8b_k4_real_50/error_type_details.csv`
- `runs/qwen3_8b_k4_real_50/error_type_details.jsonl`

### 重点看什么

错误类型包括：

- `execution_error`
- `objective_error`
- `generic_variable_error`
- `generic_constraint_error`
- `missing_inventory_balance`
- `missing_shortage_variable`
- `missing_capacity_constraint`
- `missing_binary_setup`
- `missing_big_m`
- `missing_fixed_order_cost`

### 指标有什么用

- 证明 Solver-Filter 能处理执行问题，但可能漏掉语义结构问题；
- 证明 SIRL-like LP-Stats 能看 LP 是否完整，但不理解补货语义；
- 证明 OptArgus-like Audit 能发现 generic error，但不够 replenishment-specific；
- 为 case study 提供素材。

### 论文写法建议

- 不只报告总错误率，还要报告 replenishment-specific error 的比例；
- 强调“能求解/Optimal 不等于结构正确”；
- 给出每个 baseline 最常见的 failure mode。

---

## 8. 实验五：Case Study 抽取

### 目的

找出能写进论文的真实案例。

### 推荐命令

```bash
python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/qwen3_8b_k4_real_50
```

### 输出文件

- `runs/qwen3_8b_k4_real_50/case_studies.md`
- `runs/qwen3_8b_k4_real_50/case_studies.csv`
- `runs/qwen3_8b_k4_real_50/case_studies.jsonl`

### 最值得写进论文的案例

1. Solver-Filter 选中 `Optimal`，但缺少 inventory balance；
2. OR-R1-like Voting 选中多数候选共同错误的 Big-M 模型；
3. SIRL-like LP-Stats 认为 LP artifact 合法，但缺 fixed ordering cost；
4. OptArgus-like Audit 只能给 generic issue，但 ReplenishVerifier 给出具体结构反馈；
5. ReplenishVerifier 选中结构更完整但目标值不是表面最优的候选。

### 怎么判断 case study 好不好

好的 case 应该满足：

- baseline 选中的模型看起来能跑；
- solver status 最好是 `Optimal`；
- 但缺少关键补货结构；
- ReplenishVerifier 能指出具体缺失结构；
- ReplenishVerifier 的反馈能自然转化成 repair prompt；
- 读者不需要看大量代码也能理解错误。

### 写进论文时需要展示什么

建议每个 case 展示：

- problem type 和简短自然语言描述；
- baseline 选中 candidate 的 LP 片段或约束片段；
- 缺失结构；
- ReplenishVerifier evidence / missing reason / repair hint；
- 为什么 solver 或 generic audit 没有发现该问题。

---

## 9. 实验六：Repair 候选生成与修复对比

### 目的

比较 ReplenishVerifier-Repair 的结构反馈是否比 generic repair prompt 更有用。

### Step 1：确认已有 repair prompts

`run_all_methods` 会生成：

- `runs/qwen3_8b_k4_real_50/repair_prompts.jsonl`
- `runs/qwen3_8b_k4_real_50/repair_prompts.md`

先检查这些文件中是否有：

- `problem_id`
- `candidate_id`
- missing structures
- structure-specific feedback
- generic repair feedback

### Step 2：生成 repaired candidates

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/generated/real_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_real_50/repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_repaired.jsonl \
  --model Qwen/Qwen3-8B \
  --max_new_tokens 2048 \
  --temperature 0.7 \
  --top_p 0.9 \
  --trust_remote_code
```

如果要做 generic repair prompt 对照，应另外生成一组 generic repaired candidates，例如：

```bash
python -m replenishverifier.llm.run_repair_generation \
  --benchmark data/generated/real_50.jsonl \
  --repair_prompts runs/qwen3_8b_k4_real_50/generic_repair_prompts.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_generic_repaired.jsonl \
  --model Qwen/Qwen3-8B \
  --max_new_tokens 2048 \
  --temperature 0.7 \
  --top_p 0.9 \
  --repair_type generic \
  --trust_remote_code
```

> `run_all_methods` 会同时输出 structure-aware 的 `repair_prompts.*` 和 generic 的 `generic_repair_prompts.*`。Generic repair 只能使用 execution / solver / generic audit feedback，不能包含 `inventory_balance`、Big-M、fixed-order-cost 等具体补货结构提示；structure-aware repair 才允许使用 missing structures、certificates 和 repair hints。

### Step 3：重新评估 repaired candidates

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_repaired.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50_repaired \
  --k_values 1,2,4 \
  --timeout 30 \
  --no_demo_if_empty
```

如果有 generic repaired candidates：

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_generic_repaired.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50_generic_repaired \
  --k_values 1,2,4 \
  --timeout 30 \
  --no_demo_if_empty
```

### 输出文件

- `data/candidates/qwen3_8b_k4_real_50_repaired.jsonl`
- `runs/qwen3_8b_k4_real_50_repaired/main_results.md`
- `runs/qwen3_8b_k4_real_50_repaired/candidate_evaluations.md`
- `runs/qwen3_8b_k4_real_50_repaired/repair_prompts.md`

建议最终汇总成：

- `repair_comparison.md`
- `repair_comparison.csv`

如果当前代码还没有专门的 `repair_comparison` 脚本，可以先用 `main_results.csv` 和 `candidate_evaluations.csv` 手动/脚本汇总，但不要编造结果。

### 看什么指标

比较 repair 前后：

- Structure Completeness 是否提升；
- `missing_inventory_balance` 是否下降；
- `missing_big_m` 是否下降；
- `missing_fixed_order_cost` 是否下降；
- Objective Accuracy 是否没有明显下降；
- Executable Rate 是否没有下降；
- Optimal Rate 是否没有下降。

### 结果怎么解释

- 如果 ReplenishVerifier-Repair 提升结构指标，说明结构反馈有效。
- 如果 generic repair 只能修 execution error，但不能修 Big-M / inventory balance，说明 replenishment-specific feedback 有增量。
- 如果 repair 后 Objective Accuracy 下降，说明结构修复可能引入数值错误，需要在 limitation 中讨论。
- 如果 repair 后 Executable Rate 下降，说明 prompt 可能让模型生成更复杂但不稳定的代码，需要调整 repair prompt。

---

## 10. 实验七：Low-K 分析

### 目的

分析候选数量少的时候方法是否还有用。

### 生成方式

已在主实验中通过 `--k_values 1,2,4` 生成。

主实验命令中必须包含：

```bash
--k_values 1,2,4
```

### 输出文件

- `runs/qwen3_8b_k4_real_50/low_resource_results.md`
- `runs/qwen3_8b_k4_real_50/low_resource_results.csv`
- `runs/qwen3_8b_k4_real_50/low_resource_results.jsonl`

### 看什么

- **K=1**：没有选择空间，主要看 verifier 能否识别错误并生成 feedback；selection 提升有限。
- **K=2**：选择空间很小，若 ReplenishVerifier 仍明显优于 Solver-Filter，说明结构信号强。
- **K=4**：主实验设置，比较所有方法的主要依据。

### 怎么解释

- 如果 K 增大时 ReplenishVerifier 优势扩大，说明结构信号能更好利用候选多样性；
- 如果 K=1 时也有诊断价值，说明 verifier 不只是 selector，也能作为 feedback generator；
- 如果 K=4 优势不明显，可能说明候选质量过高/过低，或 benchmark 区分度不足。

---

## 11. 实验八：Robustness 分析

### 目的

检查 ReplenishVerifier 是否过度依赖变量名。如果把变量名随机化或改成无语义名字，结构检测是否大幅下降。

### 当前实现状态

已新增轻量 renamed-candidate 生成入口，详见 `docs/robustness_naming_variation_guide.md`：

```bash
python -m replenishverifier.experiments.rename_variables_for_robustness \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out data/candidates/qwen3_8b_k4_real_50_renamed.jsonl \
  --mode descriptive_to_anonymous

python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/benchmark/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50_renamed.jsonl \
  --out_dir runs/real_50_renamed \
  --k_values 1,2,4 \
  --timeout 30
```

该脚本是 text-level perturbation，适合服务器实验前的轻量生成。若要做 camera-ready 命名鲁棒性实验，建议抽样检查 renamed code，必要时后续改为 AST-based renaming。不得根据脚本存在编造实验结果。

### 输出文件

建议输出：

- `robustness_variable_renaming.md`
- `robustness_variable_renaming.csv`
- `robustness_variable_renaming.jsonl`

### 看什么

- 原始命名下 Structure Completeness；
- 随机命名下 Structure Completeness；
- 下降幅度；
- 哪些规则最脆弱；
- name normalization / concept tagging 是否有帮助；
- LPStructureGraph 是否还能提供 weak evidence。

### 怎么解释

- 如果下降很小：说明鲁棒性不错。
- 如果下降明显：诚实写进 limitation，并说未来加入 graph matching / coefficient pattern matching。
- 如果只有 fixed-order / Big-M 类规则下降明显，可以说明这些结构比库存平衡更依赖命名与二进制变量语义。

---

## 12. 实验九：Runtime Overhead 分析

### 目的

证明 ReplenishVerifier 的额外开销不大。

### 当前实现状态

`run_all_methods` 的 candidate evaluation 会记录 runtime 字段，并可用 runtime analyzer 汇总：

- `code_execution_time`；
- `solver_time`；
- `solver_lp_export_time`；
- `lp_parse_time`；
- `structure_check_time`；
- `total_candidate_evaluation_time`。

使用如下命令：

```bash
python -m replenishverifier.experiments.analyze_runtime_overhead \
  --exp_dir runs/qwen3_8b_k4_real_50
```

缺失字段会在报告中显示为 `NA`，不要提前估计或编造 runtime 数字。

### 输出文件

建议输出：

- `runtime_overhead.md`
- `runtime_overhead.csv`
- `runtime_overhead.jsonl`

### 看什么

分解时间：

- code execution time；
- solver time；
- LP export time；
- LP parsing time；
- structure checking time；
- total verifier time。

### 怎么解释

- 如果 LP parsing + structure checking 时间远小于 solver execution，说明方法实用。
- 如果 overhead 较大，说明需要优化 parser 或减少 K。
- 如果 runtime 随 K 线性增加，要说明这是 candidate-level verification 的自然成本，可通过 early stopping / parallel execution 缓解。

---

## 13. Preference Data 导出（future learning signal）

### 目的

把 no-reference verifier 信号转成 chosen/rejected pairs，供未来 DPO / PRM / LoRA / reranker 等训练使用。只有真正训练并重新评估后，才能声称任何 DPO、LoRA 或 PRM 版本有提升。

### 推荐命令

```bash
python -m replenishverifier.experiments.build_preference_data \
  --exp_dir runs/qwen3_8b_k4_real_50 \
  --out runs/qwen3_8b_k4_real_50/preference_pairs.jsonl \
  --min_score_gap 0.10 \
  --max_pairs_per_problem 3
```

Preference construction 使用 executable status、Optimal status、structure completeness 和 repair-feedback count；不使用 `reference_objective`。输出 metadata 中应包含 `uses_reference_objective_for_preference=False`、`preference_source="replenishment_structure_verifier"`、missing structures、execution status、certificate summary、problem type、difficulty、prompt_type 和 candidate ids。

---

## 14. 实验十：Leakage Audit

### 目的

证明正式 selection 没有使用 reference objective。

### 推荐命令

```bash
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_real_50 \
  --write_report
```

### 输出文件

当前代码在 `--write_report` 下输出：

- `runs/qwen3_8b_k4_real_50/no_leakage_audit.json`

建议论文整理时另存或补充：

- `leakage_audit.md`
- `leakage_audit.json`

如果只运行当前脚本且不加 `--write_report`，它会在终端打印 audit 是否通过，但不一定写入 JSON 报告。

### 必须检查

1. ReplenishVerifier-Full 不使用 `reference_objective`；
2. Solver-Filter 不使用 `reference_objective`；
3. SIRL-like / OptArgus-like / OptiRepair-like 不偷用 expected replenishment structures；
4. reference objective 只用于 final evaluation；
5. Oracle 如果存在，不能放进主表；
6. `selection_score` 和 `score` 的来源必须是 no-reference selection policy；
7. `objective_accuracy`、`relative_error` 只能在 evaluation 字段中出现。

### 怎么解释

这个实验是防止审稿人质疑“你是不是用答案选候选”。

如果 audit 不通过，论文不能投，必须先修。修复后重新跑全部主实验或至少重新生成 selection outputs 和 audit report。

---

## 15. 实验十一：生成论文表格

### 目的

把实验结果整理成论文表格。

### 推荐命令

```bash
python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_real_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_real_50
```

### 输出文件

- `runs/paper_tables_qwen3_8b_k4_real_50/table1_benchmark.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table2_main.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table3_strong_baselines.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table4_ablation.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table5_low_resource.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table6_difficulty.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table7_error_types.md`
- `runs/paper_tables_qwen3_8b_k4_real_50/table8_case_studies.md`

每个表通常还有 `.csv` 和 `.jsonl` 版本。

### 做表前检查

生成论文表格前，建议先确认：

1. `run_all_methods` 已完成；
2. `analyze_error_types` 已完成；
3. `extract_case_studies` 已完成；
4. `audit_leakage` 已通过；
5. 没有把 synthetic demo 结果误当作 real LLM 主实验结果；
6. 表中的方法名和论文正文一致。

---

## 16. 异常情况怎么处理

### 所有候选都太好

处理：

1. 换弱一点模型；
2. 降低 prompt 约束，使用 plain prompt；
3. 增加 hard problem；
4. 加入更容易漏结构的 fixed-order / Big-M 变体。

解释：候选都接近正确时，selection 方法之间差异会变小，难以证明 verifier 增量。

### 所有候选都太差

处理：

1. 先跑 easy / medium subset；
2. 降低 benchmark 难度；
3. 检查 prompt 是否过短或 code extraction 是否失败；
4. 检查模型是否真的会生成 PuLP 代码。

解释：如果大多数候选都无法执行，则实验主要测代码生成能力，而不是结构验证能力。

### 结构分高但 objective 差

处理：

1. 检查系数、索引、初始库存、需求边界；
2. 把这种情况作为 limitation；
3. 强调 high-level structure completeness 不是 sufficient condition。

解释：结构正确只能证明关键结构存在，不能保证所有数学细节正确。

### 变量名鲁棒性差

处理：

1. 写进 limitation；
2. 强调未来加入 graph matching / coefficient pattern matching；
3. 增加 variable normalization、constraint pattern matching、binary-continuous linking detection。

### leakage audit 不通过

处理：

1. 停止使用该结果；
2. 检查 selection score 是否用到 reference objective；
3. 检查 prompt 是否泄漏 expected structures；
4. 修复代码后重新跑 selection 和 audit。

### runtime overhead 太大

处理：

1. 分析是 LP parsing 慢、structure checking 慢还是 solver 慢；
2. 优化 parser；
3. 降低 K 或并行候选执行；
4. 把 overhead 作为 limitation，而不是隐瞒。

---

## 16. 最终论文应该怎么用这些实验

- **Main Results** 用来支撑 RQ1：ReplenishVerifier 是否比 Direct、Best-of-K、Solver-Filter 更会选结构正确的候选。
- **Strong Baseline Comparison** 用来支撑 RQ2：ReplenishVerifier 是否比 SIRL-like LP-Stats、OptArgus-like Audit、OR-R1-like Voting 更能发现补货语义结构缺失。
- **Error Type Analysis** 用来支撑 RQ3：不同方法捕捉的错误类型不同，ReplenishVerifier 专门减少 replenishment-specific missing structures。
- **Low-K Analysis** 用来支撑 RQ4：候选数量少时，结构验证是否仍有诊断或选择价值。
- **Repair Experiment** 用来支撑 RQ5：结构反馈是否比 generic repair prompt 更能修补 inventory balance、Big-M、fixed ordering cost 等问题。
- **Robustness Analysis** 用来回应变量名依赖：证明方法不是只靠变量名，或诚实说明限制。
- **Runtime Overhead** 用来回应可用性：证明 LP parsing + structure checking 的额外开销可以接受。
- **Leakage Audit** 用来回应公平性和无答案泄漏：证明 selection 不用 reference objective。
- **Case Study** 用来展示可解释性：展示具体 LP evidence、missing reason 和 repair hint。

---

## 17. 哪些实验必须在服务器上跑

强烈建议服务器/GPU 运行：

1. 真实 LLM candidate generation；
2. repair candidate generation；
3. 大规模 K=4/K=8 主实验；
4. 大规模 robustness variable renaming；
5. 多模型对比；
6. 300 条以上 benchmark 的完整实验。

原因：这些步骤需要加载大模型或大量执行候选代码，耗时且占用内存/GPU。

---

## 18. 哪些实验可以本地小规模检查

本地弱机器可以做：

1. benchmark generation 的小规模检查，例如 `--n-per-type 1`；
2. reference LP structure verification；
3. synthetic demo smoke test；
4. 读取 JSONL 检查字段完整性；
5. leakage audit 的静态输出检查；
6. paper table generation，如果输入结果已经存在；
7. 少量 LP parser / structure rules 单元测试。

本地不要做：

- 正式 Qwen3-8B LLM generation；
- 大规模 repair generation；
- 大量候选代码执行；
- 任何会长时间占满 CPU/内存/GPU 的实验。

---

## 19. 推荐最短正式实验流程

服务器上建议按这个顺序：

```bash
# 1. Generate benchmark
python scripts/generate_benchmark.py \
  --output data/generated/real_50.jsonl \
  --lp-dir runs/lp/real_50 \
  --n-per-type 10 \
  --seed 42

# 2. Generate real LLM candidates
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/real_50.jsonl \
  --model Qwen/Qwen3-8B \
  --out data/candidates/qwen3_8b_k4_real_50.jsonl \
  --k 4 \
  --temperature 0.7 \
  --top_p 0.9 \
  --max_new_tokens 2048 \
  --trust_remote_code

# 3. Run all methods
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/real_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_real_50.jsonl \
  --out_dir runs/qwen3_8b_k4_real_50 \
  --k_values 1,2,4 \
  --timeout 30 \
  --no_demo_if_empty

# 4. Analyze error types
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k4_real_50

# 5. Extract case studies
python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/qwen3_8b_k4_real_50

# 6. Run leakage audit
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_real_50 \
  --write_report

# 7. Build paper tables
python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_real_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_real_50
```

repair 实验在主实验完成、case study 和 repair prompts 检查过后再跑，不要和主实验混在一起。

---

## 20. 下一步建议

最优先建议先做：

1. 在本地只生成 `--n-per-type 1` 的 benchmark，确认字段和 LP 输出格式；
2. 在服务器上跑 `real_50` 的真实 LLM candidate generation；
3. 用 `--no_demo_if_empty` 跑 `run_all_methods`，确保不是 synthetic demo；
4. 立刻跑 leakage audit；
5. 再看 error types 和 case studies，决定是否需要换模型、调 prompt 或扩大 benchmark。

只有当 `real_50` 能产生足够多“可执行但结构有缺陷”的候选时，才值得扩大到更大规模。否则应先调整 prompt、模型或 benchmark 难度。
