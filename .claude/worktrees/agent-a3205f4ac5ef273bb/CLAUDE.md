# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言与项目上下文

- 与用户沟通默认使用中文。
- 本仓库是 **ReplenishVerifier**：面向库存补货优化建模的论文原型代码，核心目标是从 LLM 生成的 PuLP 代码导出 LP artifact，并验证 replenishment-specific LP 结构。
- 当前项目使用 `planning-with-files`：开始较大任务前先读 `task_plan.md`、`findings.md`、`progress.md`，并在阶段完成或发现关键事实后更新这些文件。

## 常用命令

### 环境与测试

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m pytest tests/test_lp_parser.py -q
python -m pytest tests/test_structure_rules.py::test_reference_models_detect_new_required_structures -q
```

项目要求 Python 3.10+。`requirements.txt` 包含测试和本地 LLM 生成所需依赖；`pyproject.toml` 将 `tests/` 设为 pytest testpaths，并把仓库根目录加入 pythonpath。

### Benchmark、结构验证与 smoke 实验

```bash
python scripts/generate_benchmark.py \
  --output data/generated/test_50.jsonl \
  --lp-dir runs/lp/test_50 \
  --n-per-type 10 \
  --seed 42

python scripts/run_structure_verification.py \
  --benchmark data/generated/test_50.jsonl \
  --out runs/structure_check_test_50.jsonl

python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test.jsonl \
  --candidates data/candidates/demo_candidates.jsonl \
  --out_dir runs/smoke_literature_driven \
  --k_values 1,2,4 \
  --timeout 30
```

Synthetic/demo smoke 只用于验证 pipeline，不要写成正式论文结果。

### 真实 LLM 实验流程

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

如果使用本地模型，把 `--model` 改成本地模型目录。`--use_objective_consensus` 是可选 appendix ablation，只使用候选之间的 objective clustering，不使用 reference objective。

### Repair 与 preference 数据

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

python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_50.jsonl \
  --candidates data/candidates/qwen3_8b_k4_50_repaired.jsonl \
  --out_dir runs/qwen3_8b_k4_50_repaired \
  --k_values 1,2,4 \
  --timeout 30

python -m replenishverifier.experiments.compare_repair_results \
  --before runs/qwen3_8b_k4_50/candidate_evaluations.jsonl \
  --after runs/qwen3_8b_k4_50_repaired/candidate_evaluations.jsonl

python -m replenishverifier.experiments.build_preference_data \
  --exp_dir runs/qwen3_8b_k4_50 \
  --out runs/qwen3_8b_k4_50/preference_pairs.jsonl \
  --min_score_gap 0.10 \
  --max_pairs_per_problem 3
```

只有实际生成并重新评估 repaired candidates 后，才能称为二轮 LLM repair 结果；否则只能称为 repair prompt generation。

## 高层架构

整体 pipeline：LLM 生成 PuLP 候选代码 → 执行候选并导出 `.lp` → 解析 LP artifact → 检查补货结构证据 → 用 no-reference 策略选择候选 → 输出实验表格、case studies、repair prompts 和 preference pairs。

主要分层：

- `replenishverifier/benchmark/`：benchmark schema、模板和生成器；支持 `single_period_newsvendor`、`single_item_multi_period`、`single_item_multi_period_shortage`、`multi_item_capacity`、`fixed_order_cost_big_m`。
- `replenishverifier/solver/`：PuLP runner 和生成代码执行器。`code_executor.py` 会执行候选 Python 代码，处理外部不可信候选时需要沙箱。
- `replenishverifier/verifier/`：LP parser、弱 LP graph 证据、结构规则和自然语言反馈。`structure_rules.py` 产出 per-rule certificates；主 `structure_score` 只基于 required structures。
- `replenishverifier/data/structure_schema.py`：`EXPECTED_STRUCTURES_BY_TYPE` 是 required/optional/forbidden 结构定义中心。若 benchmark instance 有 truthy `expected_structures`，它会覆盖默认 required set；否则使用 schema fallback。
- `replenishverifier/pipeline/`：candidate scoring 和 selection utilities；保持 selection score 与 evaluation metrics 分离。
- `replenishverifier/experiments/`：run-all-methods、baseline 定义、evaluation、leakage audit、error analysis、case study、paper table、repair comparison、preference data。
- `replenishverifier/llm/`：prompt building、code extraction、candidate generation、repair generation。
- `scripts/`：较早/轻量的命令入口；正式论文式实验主要走 `python -m replenishverifier.experiments.*`。

## 论文与实验约束

- Formal candidate selection 绝不能使用 `reference_objective`；它只用于最终 evaluation metrics，例如 objective accuracy 和 relative error。每次实验后运行 `audit_leakage`，失败则不要使用结果。
- `Solver-Filter` 只使用 candidate 自身 executable、Optimal status、objective presence。
- `OR-R1-like Voting` 使用 executable、Optimal、代码/LP 有效性和候选间 objective consensus；不使用 reference objective 或补货结构。
- `SIRL-like LP-Stats` 只使用 generic LP artifact statistics。
- `OptArgus-like Audit` 只做 generic objective/variables/constraints audit，不检查 inventory balance、Big-M 等补货语义。
- `OptiRepair-like Repair-Prompt` 只生成 generic repair feedback；ReplenishVerifier repair prompts 才包含补货结构反馈。
- `*-like` baseline 是 lightweight signal-isolation baselines，不要声称完整复现原论文系统。
- 主论文结论必须基于真实 LLM candidates；synthetic/demo 结果只能作为 sanity check 或 appendix illustration。
- LP parser/structure rules 是原型启发式方法，依赖 PuLP LP 格式和部分命名/表达式证据，不保证完整数学正确性、系数正确性或索引边界证明。

## 输出目录约定

- `data/generated/`：生成的 benchmark split。
- `data/candidates/`：LLM/demo candidate JSONL。
- `runs/<exp_dir>/`：`run_all_methods` 输出，包括 `candidate_evaluations.*`、`main_results.*`、`ablation_results.*`、`low_resource_results.*`、`difficulty_results.*`、`benchmark_summary.*`、`repair_prompts.*`、`summary.md`、`manifest.json`。
- `runs/paper_tables_*`：paper-style Markdown/CSV/JSON 表格。
- `outputs/`：较早脚本和 reference/structure check 输出。
- `docs/` 和 `papers/`：论文计划、风险审计、实验操作指南和中英文草稿；修改 claim 或实验解释前先读相关文档。
