# ReplenishVerifier：面向库存补货优化的大语言模型 LP 结构验证增强方法

## 摘要

大语言模型（LLM）已经能够从自然语言描述生成优化模型和求解器代码，但在库存补货优化任务中，代码可执行、求解器返回最优状态或多个候选目标值一致，并不一定意味着生成模型包含正确的补货语义结构。本文研究一个收窄但重要的问题：如何利用 LLM 生成的求解器代码所诱导出的 LP artifact，为库存补货优化建模提供结构化验证信号。

本文提出 **ReplenishVerifier**，一个面向库存补货优化的大语言模型 LP 结构验证增强方法。给定 LLM 生成的 PuLP 代码，ReplenishVerifier 执行代码并导出 `.lp` 文件，解析其中的 variables、constraints、objective、binary declarations 和 bounds，并检查 inventory balance、shortage/backlog、capacity、fixed ordering cost、binary setup/order trigger、Big-M linking 等补货结构是否存在。由此得到的结构证据可用于候选选择、结构化错误反馈、repair prompt 生成以及后续 preference data 构造。

本文不是通用 LLM-for-OR 框架，也不声称完整复现 SIRL、OptArgus、OptiRepair、OR-R1 或 StepORLM。我们将 ReplenishVerifier 定位为一个可插入的 replenishment-specific LP-structure supervision layer，并设计 Direct、Best-of-K、Solver-Filter、OR-R1-like Voting、SIRL-like LP-Stats、OptArgus-like Audit、OptiRepair-like Repair-Prompt 等轻量 baseline 来区分补货结构监督与通用 solver feedback、LP artifact statistics、objective consensus 和 hallucination audit 的差异。正式候选选择阶段不使用 `reference_objective`；reference objective 仅用于最终 evaluation metrics。真实 LLM candidate 实验和二轮 repair 实验的结果将在完成后回填。当前 synthetic smoke test 仅作为流程 sanity check，不作为主实验结论。`[TO FILL: real LLM main findings]`

**关键词：** LLM for optimization modeling；inventory replenishment；LP artifact；structure verification；candidate selection；repair feedback

---

## 1. 引言

自然语言到优化模型的自动建模是 LLM-for-OR 研究中的重要方向。给定业务问题描述，模型需要识别决策变量、目标函数、约束条件，并输出可被求解器执行的代码。已有工作已经表明，LLM 可以通过 prompt、agentic debugging、solver execution、verifiable reward、process supervision 或 preference/RL training 等方式提升优化建模能力。

然而，库存补货优化中的错误常常不是简单的语法错误或求解失败。一个 LLM 生成的 PuLP 程序可能可以运行，求解器也可能返回 `Optimal`，但模型仍然不是目标问题的正确数学表达。例如，多周期补货模型可能遗漏 inventory balance；固定订货成本模型可能包含 binary variable，却没有 Big-M linking constraint；容量受限多品类补货模型可能忽略 warehouse capacity。此类错误会改变补货决策的语义，但仅依赖 executable rate、solver status、objective value 或候选间 majority voting 并不总能识别。

本文聚焦库存补货这一垂直场景。库存补货模型具有较稳定的结构模式，包括订货变量、库存状态、缺货/回补变量、库存平衡、容量约束、固定订货成本、binary setup/order trigger 和 Big-M linking。这些结构通常会在求解器导出的 LP 文件中留下可解析痕迹。因此，与其只检查最终答案，本文尝试从 LLM 生成代码诱导出的 LP artifact 中提取结构证据，用于验证候选模型是否包含目标补货问题所需的语义结构。

我们提出 ReplenishVerifier。系统首先执行候选 PuLP 代码并导出 `.lp` 文件，然后解析 objective section、constraint section、bounds、binary declarations 和变量名集合，最后根据每个问题的 expected structures 检查补货结构是否存在。验证结果被转换为 ground-truth-free selection score、结构化反馈和 repair prompt。形式化候选选择阶段不使用 reference objective；reference objective 只在选择完成后用于 objective accuracy 和 relative error 等 evaluation metrics。

本文的贡献可以概括为：

1. **补货结构验证视角。** 本文将库存补货建模中的 inventory balance、capacity、shortage、fixed ordering cost、binary setup 和 Big-M 等结构作为可验证 LP artifact signals，用于补充通用 solver feedback。
2. **ReplenishVerifier 方法。** 本文实现一个从 PuLP code execution 到 LP export、LP parsing、structure checking、candidate scoring 和 repair feedback 的完整原型流程。
3. **文献驱动的 baseline 设计。** 为避免将通用 solver-in-the-loop、LP artifact reward、objective consensus、hallucination audit 或 repair prompt 误认为本文增量，我们实现 SIRL-like、OptArgus-like、OptiRepair-like 和 OR-R1-like 轻量 baseline。
4. **实验协议与风险控制。** 本文明确区分 formal selection 与 final evaluation：candidate selection 不使用 `reference_objective`；synthetic smoke test 仅用于 sanity check；主实验需要真实 LLM candidates 和二轮 repair 结果。

---

## 2. 相关工作

### 2.1 LLM for Optimization Modeling

OptiMUS 等 LLM-for-OR 系统关注从自然语言生成优化模型、求解器代码和调试流程。此类系统证明了 LLM 与求解器结合可以提升自动建模能力。ReplenishVerifier 与该方向共享 solver-in-the-loop 场景，但目标更窄：它不是通用建模 agent，而是库存补货场景中的 LP 结构验证层。

### 2.2 Solver-informed Learning 与 LP Artifact Feedback

SIRL 等工作使用 solver execution、solution quality、LP artifact 或 verifiable reward 来训练或选择优化建模模型。OR-R1 / SolveOR-R1 类方法强调 valid-code reward、executable reward、test-time RL 和 majority voting。ReplenishVerifier 不声称首次使用 solver 或 LP artifact；相反，它将这些通用反馈与 replenishment-specific structure verification 区分开来。为此，实验中加入 `SIRL-like LP-Stats` 和 `OR-R1-like Voting`，分别模拟 generic LP artifact statistics 与 test-time objective consensus / valid-code voting。

### 2.3 Process Supervision 与 PRM

StepORLM / GenPRM 等工作指出 outcome reward 在优化建模中存在 credit assignment 问题，并通过 process reward model 或 generative process supervision 改善训练。ReplenishVerifier 的过程信号不是自由文本 reasoning trace，也不是训练出的 PRM，而是来自 solver-exported LP artifact 的结构标签。因此，本文更适合被描述为可验证过程证据来源，可为未来 PRM、DPO 或 RL-style training 提供偏好数据，而不是替代 StepORLM / GenPRM。

### 2.4 Hallucination Audit 与 Model Repair

OptArgus 关注 LLM 优化建模中的 hallucination detection 和 structural consistency audit，OptiRepair 关注 supply-chain optimization model 的诊断与修复。ReplenishVerifier 与二者有明显重叠，因此本文不声称替代通用 hallucination detector 或 repair system。区别在于：OptArgus-like baseline 只检查 generic objective/variable/constraint/implementation signals；OptiRepair-like baseline 只使用 generic execution/audit repair feedback；ReplenishVerifier 则额外检查库存补货结构，并用于候选排序和结构反馈。

### 2.5 OR Benchmark 与数据构造

ORLM / OR-Instruct / IndustryOR、OptMATH、NL4Opt、MAMO 等工作提供了自动优化建模的数据、benchmark 和评估框架。ReplenishVerifier 的 benchmark 不是通用工业 OR benchmark，而是面向 replenishment 的结构标注评估集。OptMATH 的 bidirectional data synthesis 和 rejection sampling 思路可为 benchmark quality control 提供参考；IndustryOR 和 MAMO 中的 inventory / production planning 子集可作为未来外部验证。

### 2.6 库存补货与 Inventory RL

Inventory RL、MARLIM、MABIM 以及多产品多节点库存管理研究说明了补货问题的实际复杂性，包括随机需求、提前期、多 echelon、多 agent 和共享资源。但这些工作主要学习补货策略或仿真环境中的 policy，而本文验证的是 LLM 生成的优化建模 formulation。它们提供领域背景，不是直接 baseline。

---

## 3. 问题定义

给定一个库存补货问题实例：

\[
x = (d, \theta, s^*)
\]

其中，\(d\) 是自然语言问题描述，\(\theta\) 是结构化参数（如 demand、cost、capacity、periods、items 等），\(s^*\) 是该问题需要包含的补货结构标签。LLM 生成一个候选 PuLP 程序：

\[
c = \mathcal{M}(d, \theta)
\]

执行候选程序会诱导出优化模型 \(P_c\)、solver status \(z_c\)、candidate objective value \(v_c\)，以及可选的 LP artifact \(\ell_c\)。ReplenishVerifier 的目标是在不使用 reference objective 进行选择的前提下，从 \(\ell_c\) 和 execution signals 中判断候选是否更可能包含目标补货模型的关键结构。

### 3.1 结构标签

当前原型支持如下结构：

| Structure | 含义 |
|---|---|
| `order_variable` | 订货量变量，例如 \(Q\) |
| `inventory_variable` | 库存状态变量，例如 \(I\) |
| `shortage_variable` | 缺货/回补变量，例如 \(B\) |
| `inventory_balance` | 跨周期/品类的库存平衡约束 |
| `capacity_constraint` | 容量约束 |
| `binary_order_variable` | binary setup / order trigger 变量，例如 \(Y\) |
| `big_m_constraint` | 连续订货量与 binary trigger 的 Big-M linking |
| `holding_cost` | 持有成本项 |
| `shortage_cost` | 缺货成本项 |
| `fixed_order_cost` | 固定订货成本项 |
| `lead_time` | 提前期相关结构 |

### 3.2 Selection 与 Evaluation 的区别

正式 candidate selection 可以使用：

- candidate code format validity；
- executable / timeout / runtime error；
- solver status；
- candidate objective 是否存在；
- 同一问题候选之间的 objective consensus；
- generic LP artifact statistics；
- generic audit issues；
- ReplenishVerifier variants 中的 replenishment-specific expected structures。

正式 candidate selection 禁止使用：

- `reference_objective`；
- candidate objective 与 reference objective 的距离；
- 以 reference objective 最近为标准进行排序。

`reference_objective` 仅用于最终 evaluation metrics，例如 objective accuracy 和 relative error。

---

## 4. 方法

### 4.1 Method Pipeline

ReplenishVerifier 包含七个步骤：

1. **Candidate generation.** LLM 为每个补货问题生成一个或多个 PuLP 代码候选。
2. **Code execution.** 系统在受控工作目录中执行候选代码，记录 executable、solver status、objective、错误信息和运行时间。
3. **LP export.** 如果候选代码成功构造模型，则导出 `.lp` 文件。
4. **LP parsing.** 解析 objective、constraints、constraint names、variables、binary variables 和 bounds。
5. **LP structure graph construction.** 构造变量—约束 incidence 视角的弱结构图，用于辅助发现 Big-M-like、inventory recurrence 和 binary fixed-cost evidence。
6. **Structure certificate generation.** 对每条结构规则生成 rule-level certificate，而不仅是总分。
7. **Scoring, feedback, and preference signals.** 生成 no-reference selection score、结构反馈、repair prompt 和 preference pair candidates。

### 4.2 LP Parser 与 LP Structure Graph

LP parser 采用轻量 section-level parsing，而不是完整 LP grammar。它面向 PuLP 导出的 LP 格式，解析 optimization sense、objective section、subject-to constraints、bounds、binary declarations 和 variable names。

在 parser 之上，系统新增 `LPStructureGraph`，以变量—约束 incidence 的方式组织 LP artifact，并提供三个 weak-evidence detector：

1. **`detect_big_m_like_constraints`**：寻找 binary variable 与 continuous order-like variable 同时出现的 upper-bound constraint，用于辅助 Big-M linking 检测。
2. **`detect_inventory_recurrence_candidates`**：寻找类似库存递推的约束，例如同一变量族跨时间重复出现、或 constraint name 含 `balance/flow/inventory` 的 equality constraint。变量名无法完全识别时也可返回 weak evidence。
3. **`detect_fixed_cost_binary_terms`**：寻找 binary variable 是否出现在 objective 中，用于辅助 fixed ordering cost 检测。

这些 graph-based detectors 只提供 weak evidence，不替代原有结构规则；它们用于增强 certificate 的 evidence 字段和提高真实 LLM 输出中的弱鲁棒性。当前 LPStructureGraph 只提供变量—约束关联层面的弱证据，尚不能完成完整的变量角色识别和代数等价验证。更强的 graph matching 和 coefficient-pattern verification 是后续工作。PuLP 未显式命名的约束会导出为 `_C1/_C2`，parser 会保留这些约束用于表达式检查，但不会把 `_C1/_C2` 当作语义名称证据。

### 4.3 Problem-type-specific Required Structure Schema

系统新增 problem-type-specific schema（代码中为 `EXPECTED_STRUCTURES_BY_TYPE`），将结构分为 required、optional 与 forbidden。主 `structure_score` 只对 required structures 计算；optional structures 只报告，不进入主分数；forbidden 当前作为显式 schema 元数据保留，用于未来诊断。若 benchmark instance 自带 `expected_structures`，其 truthy keys 优先作为该 instance 的 required set；否则使用 problem-type schema fallback。例如：

| Problem type | Required structures | Optional examples |
|---|---|---|
| `single_period_newsvendor` | order, inventory, shortage, holding cost, shortage cost | inventory balance |
| `single_item_multi_period` | inventory balance, order, inventory, holding cost | capacity, lead time |
| `single_item_multi_period_shortage` | inventory balance, order, inventory, shortage, holding cost, shortage cost | lead time |
| `multi_item_capacity` | inventory balance, order, inventory, capacity, holding cost | shortage, lead time |
| `fixed_order_cost_big_m` | inventory balance, order, inventory, binary setup, Big-M, holding cost, fixed cost | capacity, lead time |

这一设计避免 optional structure 被误计入主分数，也避免把某类问题本来不需要的结构（例如 newsvendor 中的 Big-M）误判为缺失。

### 4.4 LP Structure Certificate

ReplenishVerifier 不再只输出 `structure_score`。每条规则都生成一个 certificate：

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

如果 required 规则未通过，certificate 会给出 `missing_reason` 与 `repair_hint`，并进入 `missing` / `low_score_required`。optional 或非该类型所需规则即使未通过也不会进入缺失列表。因此，结构验证结果既可用于 ranking，也可用于解释、case study、repair prompt 和 preference data construction。

### 4.5 Replenishment Structure Rules

结构检测结合分层证据：

1. **Variable-name hints.** 例如 `Q/I/B/Y`，以及 `order_qty`、`inventory`、`stock`、`backlog`、`setup` 等 descriptive names。
2. **Constraint-name hints.** 例如 `inventory_balance`、`flow`、`capacity`、`link`、`big_m`、`setup`。
3. **Expression-supported evidence.** 约束表达式中必须出现相应决策变量和关系模式，例如库存递推、Big-M linking、capacity aggregation 或 shortage participation。
4. **Index / incidence evidence.** 轻量 index-consistency 检查识别相邻或重复 inventory states；LPStructureGraph 只提供 incidence-based auxiliary evidence。
5. **Magnitude evidence.** Big-M 规则可选检查最大系数是否像 upper-bound linking coefficient，但 bound-aware Big-M validation 留作未来工作。

仅有结构名称相似只能作为弱证据。只有当名称信号得到约束表达式或变量—约束关联证据支持时，ReplenishVerifier 才赋予较高结构置信度。每条规则 certificate 记录 `evidence_strength`、matched names、matched expressions、index-consistency warnings、magnitude checks 和 repair hints。

这些规则是 heuristic structure checks，不保证完整数学正确性。它们用于识别 high-level replenishment structures，而不是验证所有系数、索引和边界条件。

### 4.6 No-leakage Selection Score

ReplenishVerifier-Full 使用 ground-truth-free score：

\[
S_{full}(c)=0.25E(c)+0.25Z(c)+0.35SC(c)+0.15Sem(c)
\]

其中，\(E(c)\) 表示代码可执行，\(Z(c)\) 表示 solver 返回 `Optimal`，\(SC(c)\) 是当前 problem type required structures 的 rule-level score 平均，\(Sem(c)\) 是根据 required-only 缺失结构得到的语义一致性信号。该 raw score 不使用 `reference_objective`。

Hard Selection Gate 防止形式完整但不可执行、不可求解或非最优的候选被正式选中，同时仍保留其结构证书用于诊断和修复。默认只有 executable + `Optimal` candidates 可以获得非零正式 `selection_score`；若要允许 feasible，必须显式开启参数。

可选地，系统支持 `--use_objective_consensus`，将同一问题候选之间的 objective consensus 作为一个小权重附加信号。该信号只使用候选之间的 objective clustering，不使用 reference objective，建议作为 appendix ablation。`audit_leakage.py` 会检查正式 selection rows 是否标记 no-reference policy，并拒绝包含 reference-objective ranking 的危险表述。

### 4.7 Preference Pair Construction

系统新增 preference data builder。它从 candidate evaluations 中构造 chosen/rejected pairs，偏好分数使用 executable、Optimal、structure completeness 和更少 repair feedback，不使用 reference objective。输出字段包括 `chosen_candidate_id`、`rejected_candidate_id`、structure scores、feedback counts、score gap、chosen/rejected text/code，以及 `uses_reference_objective_for_preference=false`。

这些 preference pairs 可用于后续 DPO、PRM 或 reranker 训练，但本文在真实训练完成前不声称已经取得 preference learning 效果。

### 4.8 Repair Feedback

当候选缺失 required structures 时，ReplenishVerifier 生成结构化反馈；repair prompt 与 error analysis 也只消费 required-only `missing` 列表。例如：

- 缺少库存平衡：建议加入 \(I_t = I_{t-1}+Q_t-demand_t\) 类约束；
- 缺少 capacity constraint：建议加入容量限制；
- 缺少 Big-M：建议加入 \(Q_t \le M Y_t\)；
- 缺少 fixed ordering cost：建议在 objective 中加入 fixed cost 与 binary trigger。

当前代码已经准备了二轮 LLM repair candidate 生成入口，但 repair 的真实效果需要在实际 LLM repair 实验后报告。若只生成 prompt，不应声称完成 repair。

### 4.9 What ReplenishVerifier Can and Cannot Verify

ReplenishVerifier 可以验证 high-level replenishment structures 是否在 LP artifact 中出现，并能提供 evidence、missing reason 和 repair hint。它不能保证完整 mathematical correctness：即使所有结构都存在，候选仍可能有错误系数、错误索引、错误初始条件、错误需求边界或不合理的大 M 值。因此，它应与 solver validation、objective evaluation、generic audit 和人工/模型审查结合使用。

---

## 5. 实验设计

### 5.1 研究问题

**RQ1.** ReplenishVerifier 是否能在真实 LLM candidates 上提升结构完整性与约束覆盖率？

**RQ2.** 与 Solver-Filter、OR-R1-like Voting、SIRL-like LP-Stats、OptArgus-like Audit 等强 baseline 相比，补货结构监督是否仍然提供增量？

**RQ3.** generic objective consensus / LP artifact statistics / hallucination audit 与 replenishment-specific structure verification 捕捉的错误是否不同？

**RQ4.** 在低候选预算 \(K=1,2,4\) 下，各方法表现如何？

**RQ5.** 二轮 LLM repair 是否能修复 feasible-but-wrong 的补货结构错误？

### 5.2 数据集

主实验应使用真实 LLM candidates。建议先运行 50 条样本、每题 K=4 的实验，检查输出质量和 case studies，再决定是否扩大到 300 条或更多。

Benchmark problem families 包括：

| Problem type | 主要结构 | 主实验数量 |
|---|---|---:|
| `single_period_newsvendor` | order, inventory, shortage, holding cost, shortage cost | `[TO FILL]` |
| `single_item_multi_period` | inventory balance, order, inventory, holding cost | `[TO FILL]` |
| `single_item_multi_period_shortage` | inventory balance, shortage/backlog, shortage cost | `[TO FILL]` |
| `multi_item_capacity` | multi-item inventory balance, capacity | `[TO FILL]` |
| `fixed_order_cost_big_m` | binary setup, fixed ordering cost, Big-M | `[TO FILL]` |
| Total | — | `[TO FILL]` |

### 5.3 Candidate Generation

真实 LLM 实验需报告：

- 模型名称与路径；
- 是否为本地模型；
- 推理硬件；
- prompt 模板；
- 是否向 generator 展示 expected structures；
- K 值；
- temperature、top-p、max_new_tokens；
- code extraction 策略；
- timeout 与 solver backend。

当前 planned setting：

| Setting | Value |
|---|---|
| Model | `[TO FILL]` |
| Candidate budget K | 4 initially; larger K optional |
| Benchmark size | 50 first, then possible 300 |
| Temperature | `[TO FILL]` |
| Top-p | `[TO FILL]` |
| Max tokens | `[TO FILL]` |
| Hardware | `[TO FILL]` |

### 5.4 Compared Methods

| Method | Uses execution | Uses objective consensus | Uses generic LP/audit | Uses replenishment structure | Uses reference objective for selection |
|---|---:|---:|---:|---:|---:|
| Direct | No | No | No | No | No |
| Best-of-K | Yes | No | No | No | No |
| Solver-Filter | Yes | No | No | No | No |
| OR-R1-like Voting | Yes | Yes | code/LP validity | No | No |
| SIRL-like LP-Stats | Yes | No | Yes | No | No |
| OptArgus-like Audit | Yes | No | Yes | No | No |
| OptiRepair-like Repair-Prompt | Yes | No | Yes | No | No |
| Structure-Only | LP export required | No | No | Yes | No |
| ReplenishVerifier-Full | Yes | Optional appendix | No | Yes | No |
| ReplenishVerifier-Repair | Yes | Optional appendix | No | Yes | No |

### 5.5 Metrics

主实验报告：

- executable rate；
- optimal rate；
- objective accuracy（evaluation-only）；
- relative error（evaluation-only）；
- structure completeness；
- inventory balance accuracy；
- constraint coverage；
- average runtime；
- repair feedback count；
- leakage audit result。

### 5.6 Synthetic Smoke Test

Synthetic smoke test 使用 demo candidates 验证 pipeline 是否能运行、强 baseline 是否接入、case-study 抽取是否正常、leakage audit 是否通过。它不是正式实验结果，不能用于主论文性能结论。

当前 smoke sanity check 路径：

- `runs/smoke_literature_driven/summary.md`
- `runs/smoke_literature_driven/case_studies.md`
- `runs/paper_tables_literature_driven/`

Smoke test 观察到的模式包括：generic baselines 可能选择缺少 Big-M 或 capacity 的候选，而 ReplenishVerifier-Full 在 synthetic setting 中选择结构完整候选。但这些现象需要在真实 LLM candidates 上验证。正式结果统一保留 `[TO FILL]`。

---

## 6. 实验结果

本节等待真实 LLM candidates 与二轮 repair 实验完成后回填。不要使用 synthetic smoke test 作为主实验结果。

### 6.1 Main Results

| Method | Executable Rate | Optimal Rate | Objective Accuracy | Structure Completeness | Constraint Coverage | Avg. Runtime |
|---|---:|---:|---:|---:|---:|---:|
| Direct | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| Best-of-K | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| Solver-Filter | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| OR-R1-like Voting | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| SIRL-like LP-Stats | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| OptArgus-like Audit | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| ReplenishVerifier-Full | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| ReplenishVerifier-Repair | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |

`[TO FILL: main result discussion after real LLM experiment]`

### 6.2 Ablation Study

| Variant | Purpose | Objective Accuracy | Structure Completeness | Constraint Coverage |
|---|---|---:|---:|---:|
| ReplenishVerifier-Full | full no-reference structure score | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| Solver-Filter | remove LP structure | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| OR-R1-like Voting | replace structure with objective consensus/voting | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| SIRL-like LP-Stats | replace structure with generic LP stats | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| OptArgus-like Audit | replace structure with generic audit | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| Structure-Only | remove solver-status weighting | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| Full + objective consensus | optional appendix | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |

### 6.3 Low-resource K Analysis

| K | Method | Objective Accuracy | Structure Completeness | Constraint Coverage |
|---:|---|---:|---:|---:|
| 1 | ReplenishVerifier-Full | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| 2 | ReplenishVerifier-Full | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| 4 | ReplenishVerifier-Full | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |

### 6.4 Repair Experiment

| Method | Repair type | Objective Accuracy | Structure Completeness | Constraint Coverage |
|---|---|---:|---:|---:|
| ReplenishVerifier-Full | no second-round repair | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| ReplenishVerifier-Repair | second-round LLM repair | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| OptiRepair-like Repair-Prompt | generic prompt baseline | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |

只有在真实 LLM repair candidates 已生成并重新评估后，才能将 ReplenishVerifier-Repair 写成真实 repair 结果。dry_run repair 输出只能检查流程和 JSONL schema，不能作为 repair 实验结果。

### 6.5 命名变化鲁棒性实验

| Setting | Objective Accuracy | Structure Completeness | Inventory Balance Accuracy | Missing Big-M Rate | Missing Capacity Rate |
|---|---:|---:|---:|---:|---:|
| Original candidates | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |
| Renamed candidates | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` | `[TO FILL]` |

`[TO FILL: naming-variation robustness discussion after real renamed-candidate evaluation]`

---

## 7. 分析与案例研究

真实案例研究应从真实 LLM candidates 中抽取。推荐展示如下错误类型：

1. Solver-Filter 选择 executable/optimal 但缺少 inventory balance 的模型；
2. OR-R1-like Voting 因 objective consensus 选择共同错误的模型；
3. SIRL-like LP-Stats 偏好 generic LP artifact 完整但缺少 Big-M 或 capacity 的模型；
4. OptArgus-like Audit 认为模型通用结构完整，但无法发现补货语义结构缺失；
5. OptiRepair-like Repair-Prompt 对 feasible-but-wrong 的补货结构错误只给出 generic feedback；
6. ReplenishVerifier 给出具体结构反馈并选择结构更完整的候选。

### 7.1 Case Study: Missing Inventory Balance

`[TO FILL: real LLM case]`

### 7.2 Case Study: Missing Big-M Linking Constraint

`[TO FILL: real LLM case]`

### 7.3 Case Study: Missing Capacity Constraint

`[TO FILL: real LLM case]`

### 7.4 Synthetic Sanity-check Cases

Synthetic smoke test 中已经出现缺少 Big-M、capacity、binary setup / fixed cost 的可解释例子。这些例子说明 pipeline 可以抽取案例，但它们来自人工构造 demo candidates，只能放在 appendix 或方法说明中，不能作为主实验结论。

---

## 8. 局限性

1. **LP parser 对 LP 格式和命名有依赖。** 当前 parser 面向 PuLP 导出的 LP 文件，结构规则仍部分依赖变量名、约束名和 objective 中的变量出现。虽然已加入 descriptive variable names 的弱鲁棒识别，但还不是完整 LP/MPS parser。
2. **Structure correctness 不等于完整 mathematical correctness。** 候选模型可能包含所有 high-level structures，但仍然存在错误系数、错误索引、边界条件错误或初始库存处理错误。当前的 expression-supported 检查仍然不是完整的代数等价验证。它可以发现约束是否具有库存递推、Big-M linking 或 capacity aggregation 的基本形态，但无法完全保证所有系数、时间索引和边界条件正确。更严格的 coefficient-pattern verification 和 graph matching 是未来工作。
3. **Benchmark 覆盖有限。** 当前 benchmark 聚焦五类补货问题，尚未充分覆盖 stochastic demand、service level、lost sales、multi-echelon、supplier constraints、transportation cost 和 rolling horizon 等复杂场景。
4. **Scoring 权重是人工设计。** 当前 selection score 权重可解释，但不是从 validation data 学得。未来可以学习权重或训练 structure-aware PRM。
5. **Repair 效果依赖真实 LLM。** 如果只生成 repair prompt，不能说明模型已经被修复；必须生成 repaired candidates 并重新运行 evaluation。
6. **与通用 hallucination detector / repair system 是互补关系。** ReplenishVerifier 不替代 OptArgus-like audit、OptiRepair-like repair、solver validation 或 objective evaluation，而是提供补货结构证据作为额外监督信号。

---

## 9. 结论

本文提出 ReplenishVerifier，一个面向库存补货优化的大语言模型 LP 结构验证增强方法。它从 LLM 生成的 PuLP 代码中导出 LP artifact，解析 variables、constraints、objective、binary declarations 和 bounds，并检查 inventory balance、shortage/backlog、capacity、fixed ordering cost、binary setup/order trigger 和 Big-M linking 等补货结构。该结构证据可用于候选选择、错误反馈、repair prompt 和后续 preference data 构造。

本文将 ReplenishVerifier 定位为 replenishment-specific LP-structure supervision layer，而不是通用 LLM-for-OR 框架或已有系统的替代品。实验设计通过 OR-R1-like Voting、SIRL-like LP-Stats、OptArgus-like Audit、OptiRepair-like Repair-Prompt 等轻量 baseline，区分通用 solver/artifact/audit/voting signals 与补货结构监督的差异。真实 LLM candidate 实验、二轮 repair 实验和主表结果将在后续完成后回填。`[TO FILL: final empirical conclusion]`
