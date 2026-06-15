# ReplenishVerifier

**ReplenishVerifier** 是一个面向论文原型的 Python 研究代码框架，用于：

> **ReplenishVerifier: LP-Structure-Grounded Verification for LLM-Based Replenishment Optimization Modeling**  
> **ReplenishVerifier：面向库存补货优化的大语言模型 LP 结构验证增强方法**

本项目聚焦 **inventory replenishment optimization**，不是通用 LLM-for-OR 框架。它从 LLM 生成的 PuLP 代码中导出 LP artifact，解析 variables、constraints、objective、binary declarations 和 bounds，并检查补货模型中常见的结构：inventory balance、shortage/backlog、capacity、fixed ordering cost、binary setup/order trigger、Big-M linking 等。

这些 LP 结构证据可用于：

- candidate selection；
- missing-structure feedback；
- repair prompt generation；
- future preference data / DPO / PRM construction。

**重要原则：formal candidate selection 不使用 `reference_objective`。** `reference_objective` 只用于最终 evaluation metrics，例如 objective accuracy 和 relative error。

---

## 1. 论文定位

ReplenishVerifier 的定位是：

> a replenishment-specific LP-structure supervision layer for LLM-generated optimization models.

它不是：

- 通用 optimization modeling agent；
- 完整 hallucination detector；
- 完整 optimization repair system；
- SIRL / OptArgus / OptiRepair / OR-R1 / StepORLM 的完整复现；
- 库存补货 policy learning 方法。

它要证明的增量是：**补货语义结构监督是否能提供超出 generic solver feedback、LP artifact statistics、objective consensus、generic hallucination audit 和 generic repair prompt 的信号。**

---

## 2. 与相关工作的区别

| Related line | What it emphasizes | How this project uses it |
|---|---|---|
| OptiMUS-like modeling/debugging | LLM + solver + code generation/debugging | 作为通用 solver-agent 背景；本文不做完整 agent 复现 |
| SIRL-like solver-informed learning | solver execution, LP artifacts, verifiable reward | 实现 `SIRL-like LP-Stats`，只用 generic LP artifact statistics |
| OR-R1-like voting/RL | valid-code reward, executable reward, majority/objective consensus | 实现 `OR-R1-like Voting`，不使用 reference objective 或补货结构 |
| StepORLM / GenPRM | process supervision / process reward model | 将 LP structure labels 作为 verifiable process evidence，不声称训练 PRM |
| OptArgus-like audit | generic optimization-model hallucination/structure audit | 实现 `OptArgus-like Audit`，不检查 inventory balance / Big-M 等补货语义 |
| OptiRepair-like repair | generic/supply-chain model diagnosis and repair | 实现 `OptiRepair-like Repair-Prompt`，只用 generic repair feedback |
| Inventory RL / MARLIM / MABIM | inventory policy learning / simulation benchmark | 作为领域背景，不作为直接 baseline |

所有 `*-like` baseline 都是 **lightweight signal-isolation baselines**，不是完整复现原论文系统。

---

## 3. 项目结构

```text
replenishverifier/
  benchmark/            # benchmark schemas, templates, generator
  solver/               # PuLP runner and generated-code executor
  verifier/             # LP parser, replenishment structure rules, feedback
  pipeline/             # scoring and candidate-selection utilities
  experiments/          # all-method evaluation, baselines, tables, case studies
  llm/                  # code extraction, prompt building, generation, repair generation

scripts/
  generate_benchmark.py
  run_candidate_selection.py
  run_structure_verification.py
  evaluate_results.py

papers/
  replenishverifier_draft_zh.md
  replenishverifier_draft_en.md

docs/
  literature_audit.md
  code_and_claim_risk_audit.md
  paper_experiment_revision_plan.md
  real_llm_experiment_checklist.md

data/
  generated/            # generated benchmark splits
  candidates/           # LLM/demo candidate JSONL files

runs/
  smoke_literature_driven/
  paper_tables_literature_driven/
```

---

## 4. Method pipeline and key modules

Pipeline:

1. LLM generates PuLP candidates.
2. `solver/code_executor.py` executes candidate code and records solver status/objective.
3. Candidate model exports a `.lp` file.
4. `verifier/lp_parser.py` parses variables, constraints, objective, binaries, and bounds.
5. `verifier/lp_graph.py` builds weak LP-structure evidence.
6. `verifier/structure_rules.py` emits structure certificates and structure scores.
7. `experiments/run_all_methods.py` selects candidates with no-reference policies.
8. `experiments/build_preference_data.py` can build chosen/rejected pairs for future DPO/PRM work.

Key modules:

| Module | Purpose |
|---|---|
| `replenishverifier/data/structure_schema.py` | central `EXPECTED_STRUCTURES_BY_TYPE` schema with required/optional/forbidden structures |
| `replenishverifier/verifier/lp_parser.py` | lightweight PuLP LP parser |
| `replenishverifier/verifier/lp_graph.py` | weak LP graph evidence detectors |
| `replenishverifier/verifier/structure_rules.py` | structure detection and per-rule certificates |
| `replenishverifier/verifier/feedback.py` | natural-language structure feedback |
| `replenishverifier/experiments/audit_leakage.py` | no-reference selection audit |
| `replenishverifier/experiments/build_preference_data.py` | preference pair construction |

Structure certificates include one record per rule:

```json
{
  "rule_name": "big_m_constraint",
  "required": true,
  "passed": true,
  "score": 1.0,
  "evidence": [{"constraint": "big_m_0", "expr": "Q_0 - 100 Y_0 <= 0"}],
  "missing_reason": "",
  "repair_hint": ""
}
```

The main `structure_score` is computed only over required structures from the problem-type schema. Optional structures are reported but do not affect the main score. The central schema is `EXPECTED_STRUCTURES_BY_TYPE`; each entry defines `required`, `optional`, and `forbidden` sets. If a benchmark instance contains explicit `expected_structures`, its truthy keys override the default required set for that instance, while the default schema remains fallback metadata. Missing-structure feedback, repair prompts, and error-type analysis all consume the required-only `missing` list.

---

## 5. 安装

推荐 Python 3.10+。

```bash
python -m pip install -r requirements.txt
```

如果要运行本地 LLM generation / repair generation，还需要：

```bash
python -m pip install torch transformers accelerate
```

本地模型实验不需要 API。若使用本地 Qwen，需要给 `--model` 传本地模型路径，而不是远程模型名。

---

## 6. Benchmark 生成

生成一个 50 条测试集（每类 10 条）：

```bash
python scripts/generate_benchmark.py \
  --output data/generated/test_50.jsonl \
  --lp-dir runs/lp/test_50 \
  --n-per-type 10 \
  --seed 42
```

建议先跑 50 条、K=4 的真实 LLM candidates，确认候选质量、case study 和运行时间后，再扩大到 300 条或更多。

支持的问题类型：

| problem_type | 说明 |
|---|---|
| `single_period_newsvendor` | 单品单周期，含订货量、剩余库存、缺货变量、持有成本、缺货成本 |
| `single_item_multi_period` | 单品多周期，含库存平衡、订货量、库存变量、持有成本 |
| `single_item_multi_period_shortage` | 单品多周期，允许缺货/backlog，含缺货变量与缺货惩罚 |
| `multi_item_capacity` | 多品多周期，含库存平衡和容量约束 |
| `fixed_order_cost_big_m` | 多周期固定订货成本，含 binary setup/order trigger 和 Big-M 约束 |

---

## 7. Run verifier, certificates, and preference data

验证 reference LP 并生成 structure certificates：

```bash
python scripts/run_structure_verification.py \
  --benchmark data/generated/test_50.jsonl \
  --out runs/structure_check_test_50.jsonl
```

输出中的 `structure_verification.certificates` 包含每条 rule 的：

- `rule_name`
- `required`
- `optional`
- `passed`
- `score`
- `evidence`
- `missing_reason`
- `repair_hint`

运行完整候选评估后，可构造 preference pairs：

```bash
python -m replenishverifier.experiments.build_preference_data \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out runs/qwen3_8b_k4_50/preference_pairs.jsonl \
  --min_score_gap 0.10 \
  --max_pairs_per_problem 3
```

Preference builder 使用 executable、Optimal、structure completeness 和更少 repair feedback 来构造 chosen/rejected pairs，不使用 reference objective。

---

## 8. Synthetic smoke test

Synthetic demo 只用于验证 pipeline 是否跑通，**不是正式实验结果**，不能写成主论文结论。

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test.jsonl \
  --candidates data/candidates/demo_candidates.jsonl \
  --out_dir runs/smoke_literature_driven \
  --k_values 1,2,4 \
  --timeout 30
```

分析输出：

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/smoke_literature_driven

python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/smoke_literature_driven

python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/smoke_literature_driven \
  --out_dir runs/paper_tables_literature_driven

python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/smoke_literature_driven
```

当前 smoke sanity check 的输出位置：

- `runs/smoke_literature_driven/summary.md`
- `runs/smoke_literature_driven/case_studies.md`
- `runs/paper_tables_literature_driven/`

这些结果只能作为 sanity check / appendix illustration。

---

## 9. Strong baseline smoke test

`run_all_methods` 当前包含：

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

Baseline 定义：

- `Solver-Filter`：只使用 candidate 自身的 executable、solver status 是否 Optimal、是否返回 objective。
- `OR-R1-like Voting`：使用 executable、Optimal、代码/LP 输出有效性、候选间 objective consensus；不使用 reference objective 或补货结构。
- `SIRL-like LP-Stats`：只使用 generic LP artifact statistics，例如 LP 是否导出、objective/constraint section、变量/约束/binary/bounds 数量、objective 项数、约束-变量比例。
- `OptArgus-like Audit`：只检查 generic objective/variables/constraints、empty model、objective 是否含变量、placeholder names、boundedness、generic issue 数量。
- `OptiRepair-like Repair-Prompt`：只基于 execution/generic audit 生成 generic repair feedback，不生成 inventory balance / Big-M 等补货语义反馈。
- `Structure-Only`：只使用 replenishment LP structure completeness。
- `ReplenishVerifier-Full`：使用 executable + Optimal + replenishment-specific LP structure completeness + semantic consistency。
- `ReplenishVerifier-Repair`：生成 replenishment-specific repair prompts；只有在真实 repaired candidates 被生成并评估后，才能称为二轮 repair 结果。

---

## 10. Real LLM experiment

主实验必须使用真实 LLM candidates。示例流程如下。

### 10.1 生成 50 条 benchmark

```bash
python scripts/generate_benchmark.py \
  --output data/generated/test_50.jsonl \
  --lp-dir runs/lp/test_50 \
  --n-per-type 10 \
  --seed 42
```

### 10.2 用本地或 Hugging Face 模型生成 K=4 candidates

Hugging Face model name 示例：

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/test_50.jsonl \
  --out data/candidates/qwen3_8b_k4_50.jsonl \
  --model Qwen/Qwen3-8B \
  --k 4 \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --trust_remote_code
```

本地模型路径示例：

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/test_50.jsonl \
  --out data/candidates/local_qwen_k4_50.jsonl \
  --model /path/to/local/Qwen3-8B \
  --k 4 \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95 \
  --trust_remote_code
```

### 10.3 跑所有方法

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out_dir runs/qwen3_8b_k4_50 \
  --k_values 1,2,4 \
  --timeout 30
```

可选 objective-consensus ablation：

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50.jsonl \
  --out_dir runs/qwen3_8b_k4_50_consensus \
  --k_values 1,2,4 \
  --timeout 30 \
  --use_objective_consensus
```

`--use_objective_consensus` 只使用候选之间的 objective clustering，不使用 reference objective。建议作为 appendix ablation。

### 10.4 分析和表格

```bash
python -m replenishverifier.experiments.analyze_error_types \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.extract_case_studies \
  --exp_dir runs/qwen3_8b_k4_50

python -m replenishverifier.experiments.build_paper_tables \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out_dir runs/paper_tables_qwen3_8b_k4_50

python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_50 \
  --write_report
```

leakage audit 必须通过后，结果才能进入论文。

---

## 11. Repair experiment

二轮 repair 实验需要先有 `repair_prompts.jsonl`，它由 `run_all_methods` 生成。

### 11.1 生成 repaired candidates

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

本地模型同样把 `--model` 换成本地路径。

### 11.2 评估 repaired candidates

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

如果没有运行这一步，只能说 ReplenishVerifier 生成了 repair prompts，不能说完成了 LLM repair。

---

## 12. Leakage audit

正式 candidate selection 不使用 `reference_objective`。请每次实验后运行：

```bash
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k4_50
```

通过时输出类似：

```text
LEAKAGE AUDIT PASSED: no reference_objective usage detected in formal selection scores.
```

如果 audit 失败，不要使用该实验结果。

---

## 13. 输出文件说明

`run_all_methods` 输出：

```text
<exp_dir>/candidate_evaluations.{jsonl,csv,md}
<exp_dir>/main_results.{jsonl,csv,md}
<exp_dir>/ablation_results.{jsonl,csv,md}
<exp_dir>/low_resource_results.{jsonl,csv,md}
<exp_dir>/difficulty_results.{jsonl,csv,md}
<exp_dir>/benchmark_summary.{jsonl,csv,md}
<exp_dir>/repair_prompts.{jsonl,csv,md}
<exp_dir>/summary.md
<exp_dir>/manifest.json
<exp_dir>/no_leakage_audit.json  # when audit_leakage --write_report is used
<exp_dir>/preference_pairs.{jsonl,csv}  # when build_preference_data is used
```

`analyze_error_types` 输出：

```text
<exp_dir>/error_type_details.{jsonl,csv,md}
<exp_dir>/error_type_summary.{jsonl,csv,md}
```

`extract_case_studies` 输出：

```text
<exp_dir>/case_studies.{jsonl,csv,md}
```

`build_paper_tables` 输出：

```text
<table_dir>/table1_benchmark.*
<table_dir>/table2_main.*
<table_dir>/table3_strong_baselines.*
<table_dir>/table4_ablation.*
<table_dir>/table5_low_resource.*
<table_dir>/table6_difficulty.*
<table_dir>/table7_error_types.*
<table_dir>/table8_case_studies.*
```

---

## Experiment Operation Guide

For detailed experimental steps, metrics, and interpretation, see:

[docs/experiment_operation_guide.md](docs/experiment_operation_guide.md)

Shortest workflow:

```bash
# 1. Generate benchmark
# 2. Generate real LLM candidates
# 3. Run all methods
# 4. Analyze error types
# 5. Extract case studies
# 6. Run repair experiment
# 7. Build paper tables
# 8. Run leakage audit
```

---

## 15. 注意事项

1. **不要把 synthetic demo 写成正式结果。** 它只能作为 sanity check。
2. **主实验必须使用真实 LLM candidates。** 建议先跑 50 条 K=4，再决定是否扩大到 300 条。
3. **formal selection 不使用 `reference_objective`。** reference objective 只用于 final evaluation。
4. **`*-like` baselines 是 lightweight baselines。** 不要说完整复现 SIRL、OptArgus、OptiRepair、OR-R1 或 StepORLM。
5. **ReplenishVerifier-Repair 只有在 repaired candidates 生成并重新评估后，才是真实 repair 实验。** 否则只是 repair prompt generation。
6. **LP parser 仍是原型。** 它依赖 PuLP LP 格式和部分命名/结构启发式，不保证完整数学正确性。
7. **代码执行风险。** `solver/code_executor.py` 会执行候选 Python 代码。接入外部不可信代码时应使用 Docker、firejail、nsjail 等沙箱。
8. **本地模型不需要 API。** 若使用本地 Qwen，请把 `--model` 设置为本地模型目录。
