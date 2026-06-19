# TypeAware-Consensus 与诊断报表设计

## 背景

`qwen3_8b_k4_50_v5_typeaware_selectionfix` 已经证明 selectionfix 能让部分方法选到不同候选，但也暴露出 TypeAware-first 的方向问题：它会过度优先结构 gate，导致更多 execution_error、结构/约束指标下降；同时很多方法主表结果重复，论文解释缺少 method redundancy、metric saturation、avoidable error 等诊断证据。

本轮不修改 LLM generation、不修改 `run_generation.py`、不重新生成 candidates、不做 generation-time TypeAware retry。所有 formal selection 必须继续不使用 `reference_objective`、`objective_correct`、reference LP 或 reference answer。reference/oracle 字段只允许出现在 post-hoc evaluation、diagnostics、paper metrics、error analysis 中。

## 设计目标

1. 保留全部旧方法，向后兼容已有实验输出与脚本。
2. 将主表方法与 appendix 方法分开，默认主表更精简；通过显式参数可恢复“全部方法进 main_results”。
3. 新增正式主方法 `ReplenishVerifier-TypeAware-Consensus`：Consensus-first，再做 TypeAware-safe reranking。
4. 保留旧 `ReplenishVerifier-TypeAware` 作为 TypeAware-first ablation。
5. 新增诊断报告解释方法重复、指标饱和、可避免错误。
6. 新增 paper metrics 表支持按题型解释提升和 selection collapse。
7. 新增测试覆盖 no-reference 选择、安全排序、诊断和表格输出。

## 方法分组

在 `replenishverifier/experiments/methods.py` 增加：

- `MAIN_METHODS`：`Direct`, `Best-of-K`, `Solver only`, `Structure only`, `Consensus only`, `ReplenishVerifier-Full`, `ReplenishVerifier-TypeAware`, `ReplenishVerifier-TypeAware-Consensus`。
- `APPENDIX_METHODS`：旧有方法中未进入主表的方法，包括 `Solver-Filter`, 组合 ablation、`OR-R1-like Voting`, `Structure-Grounded Consistency`, `SIRL-like LP-Stats`, `OptArgus-like Audit`, `OptiRepair-like Repair-Prompt`, `Structure-Only`, `ReplenishVerifier-Repair`, `ReplenishVerifier full` 等。
- `METHODS = MAIN_METHODS + APPENDIX_METHODS` 保持兼容。

`run_all_methods.py` 默认只把 `MAIN_METHODS` 写入 `main_results.*`；新增 `--appendix_methods_in_main` 后 main_results 恢复包含 `METHODS` 全量方法。`ablation_results` 继续覆盖旧方法和新方法。

## TypeAware-Consensus 选择器

新增函数 `type_aware_consensus_selection_components(row)` 与 `type_aware_consensus_selection_score(row)`。

排序原则：

1. executable 与 Optimal 是硬优先级，非 executable/非 Optimal 不能靠 consensus 反超 executable+Optimal。
2. consensus 是主要排序信号。
3. critical missing structures 只作为 safe penalty / tie-break，不做 TypeAware-first pool hard filter。
4. `structure_score`, `constraint_coverage`, `objective_term_coverage`, type-aware hard gate score 是辅助信号。
5. `critical_missing_count` 只有在 consensus 非常接近时才改变选择；实现上通过“consensus bucket”或小权重 penalty 表达。
6. selection components 中不包含 reference/oracle 字段。

旧 `ReplenishVerifier-TypeAware` 保留当前 TypeAware-first pool filtering 行为，作为 ablation。

## Diagnostics

在 `diagnose_selection_metrics.py` 中复用 `compute_selection_diagnostics()` 的 `same_selection_rate`，并新增报告函数：

- `method_redundancy_report.md`：diagnostic only；列出 same_selection_rate >= 0.95 的方法对、指标完全相同的方法组、objective_accuracy 相同但 selection 不同的方法组、建议合并展示的方法族。
- `metric_saturation_report.md`：diagnostic only；列出每个 metric 的 unique value count、是否 saturated、饱和指标列表、same_selection_rate >= 0.95 方法对，并解释高重合会造成主指标相同。
- `avoidable_error_summary.md`：post-hoc only；统计 `ReplenishVerifier-TypeAware`、`ReplenishVerifier-TypeAware-Consensus`、`Consensus only` 选中可避免错误的次数。该文件可读取 `objective_correct`、solver status 和 error taxonomy，但报告头必须声明不能用于 formal selection。

## Paper metrics

在 `paper_metrics.py` / `build_paper_metrics.py` 增加：

- `compute_metrics_by_problem_type(rows, methods=None)`：按 method + problem_type 汇总 objective、structure、constraint、executable、optimal。
- `compute_selection_collapse_summary(main_rows, candidate_rows, threshold=0.95)`：输出 high-overlap 方法对、候选 rank 分布、metric duplicate group 摘要，解释 selection collapse。
- `table_by_problem_type.*`
- `table_selection_collapse.*`

这些表默认聚焦 `Direct`, `Best-of-K`, `Consensus only`, `ReplenishVerifier-Full`, `ReplenishVerifier-TypeAware`, `ReplenishVerifier-TypeAware-Consensus`，但实现应能处理缺失方法。

## 测试策略

1. 选择器测试：覆盖 consensus-first、critical tie-break、non-executable consensus 不能反超、components 不含 reference/oracle 字段。
2. 方法分组测试：默认 main 只跑 `MAIN_METHODS`；`--appendix_methods_in_main` 或函数参数开启后 main 可跑全量 `METHODS`。
3. diagnostics 测试：fake same_selection_rate >= 0.95 出现在 redundancy report；完全相同 metrics 能归组；metric saturation 能识别 unique 值少；avoidable error 能统计 post-hoc 可避免错误。
4. paper metrics 测试：确认输出 `table_by_problem_type.*` 与 `table_selection_collapse.*`，并包含 TypeAware-Consensus。
5. 完整 pytest 必须通过。

## 非目标

- 不修改 LLM generation。
- 不修改 `run_generation.py`。
- 不重新生成 candidates。
- 不添加 generation-time TypeAware validation/retry。
- 不删除旧方法。
- 不自动 git push。