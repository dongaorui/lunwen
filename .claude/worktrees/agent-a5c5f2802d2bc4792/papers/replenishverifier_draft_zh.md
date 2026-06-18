# ReplenishVerifier：面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证方法

## 摘要

大语言模型（LLM）可以从自然语言业务描述生成可执行的求解器代码，但代码可执行、求解器返回 `Optimal`，并不等价于优化建模正确。在供应链补货优化中，LLM 生成的 PuLP 模型即使能够成功求解，也可能缺失定义问题语义的关键约束结构，例如库存平衡、仓储容量、缺货/积压变量、固定订货成本、二元 setup 变量或 Big-M linking constraint。多个候选之间 objective consensus 很高也并不可靠，因为多个候选可能共享同一个错误 formulation。

本文提出 **ReplenishVerifier**，一个面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证原型。给定 LLM 生成的 PuLP 代码，ReplenishVerifier 执行候选代码，导出其诱导出的 LP artifact，解析 variables、objective、constraints、binary declarations 和 bounds，并依据问题类型检查补货优化所需结构。当前 schema 区分 single-period newsvendor、多周期库存、缺货/积压、多品容量约束、固定订货成本 Big-M 等问题中的 required、optional 和 forbidden structures。系统输出 rule-level structure certificates、required-structure coverage、missing-structure feedback 和 no-reference selection signals。

本文将 ReplenishVerifier 定位为 replenishment-specific supervision layer，而不是通用 LLM-for-OR agent，也不声称 faithful reproduction 任何已有系统。本文使用受 solver filtering、OR-R1-style voting、SIRL-style LP statistics、OptArgus-style generic audit 和 OptiRepair-style generic repair prompting 启发的 lightweight signal-isolation baselines，用于区分通用 execution / artifact signals 与补货领域结构证据。正式 candidate selection 不使用 `reference_objective`；reference objective 仅在选择后用于最终 evaluation metrics。本文草稿中的所有实证结果均保留为 `[TO FILL AFTER REAL LLM EXPERIMENT]`。

**关键词：** 大语言模型优化建模；供应链补货；LP artifact；约束级验证；库存平衡；Big-M linking；候选选择

---

## 1. 引言

LLM 正在被用于从自然语言问题生成优化 formulation 和 solver code。对于运筹优化建模而言，这一能力很有前景，但也很脆弱。一个正确的求解器程序不仅要语法正确，还必须定义正确的决策变量、目标函数和约束条件。LLM 生成的 Python/PuLP 程序可能可以运行并被求解器求到最优，但它仍然可能表达的是另一个数学模型。

供应链补货优化适合作为研究场景，因为补货模型具有强结构性。单周期 newsvendor 需要需求满足关系、订货量、期末库存和缺货变量。多周期库存模型需要跨期库存平衡。缺货/积压模型需要 backlog 变量和惩罚项。多品仓储模型需要容量约束。固定订货成本模型需要二元 setup 变量和 Big-M linking constraint。缺失这些结构会使 solver-optimal 解失去业务语义。

通用执行信号无法稳定发现这些错误。Solver status 只能说明生成出的数学程序可求解，而不能说明它是目标问题。候选之间 objective consensus 也可能失败，因为多个候选可能共同遗漏同一个约束。通用 LP statistics 或 audit signals 可以识别空模型或显著畸形模型，但它们并不知道某个补货问题必须包含 inventory balance、capacity、shortage、setup 或 Big-M 结构。

ReplenishVerifier 通过验证生成代码诱导出的 LP artifact 来补充这一缺口。系统执行候选 PuLP 程序，导出 `.lp` 文件，解析 LP section，并检查其中是否有足够证据表明所需补货结构存在。验证证书可用于 candidate selection、error analysis、structure-aware repair prompts 和 future verifier-guided preference data。核心思想不是替代求解器或 objective evaluation，而是在代码生成和最终评估之间加入一个约束级语义检查层。

本文贡献包括：

1. **约束级补货 LP 结构验证。** 将 inventory balance、demand satisfaction、shortage/backlog、capacity、fixed ordering cost、binary setup/order trigger、Big-M linking、nonnegative bounds 和 objective minimization 表述为问题类型感知的 LP artifact checks。
2. **面向候选选择与反馈的 LP artifact certificates。** ReplenishVerifier 导出并解析 LLM-generated PuLP code 诱导的 LP artifact，生成 rule-level certificates、required-structure coverage、missing reasons 和 repair hints。
3. **问题类型感知 benchmark schema。** Benchmark generator 包含 replenishment-specific `semantic_frame`、`replenishment_entities` 和 labeled `replenishment_modeling_steps`，同时保持 unlabeled prompt export 和固定 seed 可复现性。
4. **结构增强一致性候选选择。** 已实现的 selector 结合 code executability、solver status、LP artifact structure coverage、required replenishment structure coverage 和可选 candidate objective consensus，且不使用 `reference_objective`。
5. **Leakage-aware 实验协议与 signal-isolation baselines。** Direct、Solver-Filter、OR-R1-like Voting、SIRL-like LP-Stats、OptArgus-like Audit 和 OptiRepair-like Repair-Prompt 都是 lightweight signal-isolation baselines，不是 faithful reproduction。

Benchmark 扩展、真实 repair 效果、DPO/PRM training 不作为本文当前已完成贡献，除非后续实际运行并通过审计。

---

## 2. 相关工作

### 2.1 LLMs for Optimization Modeling

已有 LLM-for-OR 系统研究如何让语言模型生成数学规划、编写 solver code、调试失败并与优化求解器交互。OptiMUS、Chain-of-Experts、ORLM 和 LLMOPT 等工作代表了更广义的自动优化建模方向，重点包括通用 OR 建模、agentic decomposition、solver feedback 或面向多类 OR 任务的 instruction tuning。

ReplenishVerifier 的范围不同。本文不试图构建通用 optimization-modeling agent，而是关注一个更窄但实际重要的验证问题：给定 LLM 为供应链补货问题生成的 solver code，能否检查其诱导出的 LP 是否包含该补货问题需要的约束级结构？这种垂直化设置使 verifier 可以查找 inventory balance、capacity、backlog、setup variables 和 Big-M links 等领域结构，而不是只检查 generic solver success。

### 2.2 Solver-Informed Verification and Test-Time Learning

Solver-informed learning 与 verification 方法利用 execution result、feasibility、solution quality、LP artifacts 或 verifiable rewards 来指导 LLM 优化建模。SIRL-style 方法启发了使用 solver execution 和 LP artifact 作为可观测信号。OR-R1-style 工作强调 valid-code rewards、executable rewards、objective / answer voting 和 test-time reinforcement learning。

ReplenishVerifier 继承“通过生成代码诱导的 solver artifact 检查模型”的原则，但进一步区分 generic solver/artifact signals 与 replenishment-specific structure evidence。因此，仓库中实现了 `SIRL-like LP-Stats` 作为 generic LP statistics baseline，实现了 `OR-R1-like Voting` 作为 executable / valid-code / objective-consensus baseline。这些都是 lightweight signal-isolation baselines，不是原系统的 faithful reproduction。

### 2.3 Data Synthesis and Validation for Optimization Modeling

Step-Opt、OptMATH、ORLM 等 benchmark-building 工作说明，结构化数据合成、rejection checks 和 validated optimization instances 对自动优化建模评估非常重要。

ReplenishVerifier 使用 deterministic replenishment templates 和 validation checks，但当前 benchmark 不应被描述为完整通用 OR benchmark。它的目的在于支持约束级补货结构验证。Generator 生成 problem-type-aware semantic frames 和 entity fields，验证 labeled/unlabeled rows，并保持 parameter sampling 与 language-template selection 分离。更大规模、更高多样性的数据构造仍是后续工作。

### 2.4 Audit and Repair of Generated Optimization Models

通用 audit 和 repair 系统研究 generated optimization models 中的 hallucination、malformed formulation 和 repair feedback。OptArgus-like audit 启发了检查 objective、variables、constraints 和 implementation consistency。OptiRepair-like repair 启发了基于反馈修复生成模型。

本仓库明确区分 generic 与 replenishment-specific signals。`OptArgus-like Audit` 只检查 generic objective/variable/constraint properties 和 placeholder names，故意不检查 inventory balance 或 Big-M structure。`OptiRepair-like Repair-Prompt` 只给出关于 execution、objective、variables、constraints 和 bounds 的 generic repair feedback。ReplenishVerifier-specific repair prompts 则额外指出缺失的 required replenishment structures。真实 repair 效果必须等待 repaired candidates 生成和重新评估。

### 2.5 Inventory Replenishment and Predict-Then-Optimize

库存与补货优化包括 classic newsvendor、多周期 inventory control、capacity-constrained ordering、lead times、fixed ordering costs、service-level constraints、lost sales 和 multi-echelon supply chains。Predict-then-optimize 与 end-to-end inventory-control 研究也说明，结构建模假设会显著影响下游决策。

本文使用 replenishment optimization 不是为了学习补货 policy，而是因为它是高度结构化的建模场景。本文目标是验证 LLM-generated optimization formulation 是否包含使补货决策有意义的领域约束。

---

## 3. 问题设定

输入是一个自然语言补货问题描述，可附带 demand、periods、items、initial inventory、costs、item volumes、capacity 和 Big-M values 等结构化参数。LLM 为同一问题生成一个或多个 PuLP/Python 候选程序。记实例 \(i\) 的候选集合为 \(C_i=\{c_{i1},\ldots,c_{iK}\}\)。

执行候选程序会得到：

- executable status；
- solver status；
- candidate objective value（如果存在）；
- 成功构造模型时导出的 LP artifact；
- runtime 和 error information。

正式 selection 的目标是在只使用 candidate-observable signals 的前提下选择结构更可靠的候选。`reference_objective` 禁止用于 formal selection，只允许在选择后用于 objective accuracy 和 relative error 等 evaluation metrics。

---

## 4. 方法

### 4.1 Benchmark Schema

代码在 `EXPECTED_STRUCTURES_BY_TYPE` 中集中定义补货结构期望。每个 problem type 有三类结构：

- **required:** 必须存在，并进入主 `structure_score`；
- **optional:** 用于诊断报告，但不进入 score denominator；
- **forbidden:** 为未来诊断保留的显式 metadata。

required/optional 区分非常重要。单周期 newsvendor 不应因缺少 Big-M linking constraint 被惩罚，而 fixed-order-cost Big-M 问题缺少 binary trigger 或 Big-M link 则必须被惩罚。

Benchmark generator 还输出三个 replenishment-specific metadata fields：

- `semantic_frame`：领域专用 sets、parameters、decision variables、objective terms、constraints、solver type、replenishment structures、required structures 和 optional structures；
- `replenishment_entities`：抽取 demand、periods、items、order quantity、inventory level、shortage/backlog、costs、storage capacity、item volume、Big-M 等实体；
- `replenishment_modeling_steps`：用于 labeled rows 的 deterministic LP-structure-grounded modeling steps。Unlabeled rows 默认不输出该字段。

Validation function 检查 natural-language text、合法 problem type、必要 semantic fields、labeled/unlabeled 模式下 label presence/absence、核心实体和 required-structure coverage。

### 4.2 Candidate Execution and LP Artifact Export

候选代码通过 generated-code executor 执行。一个有效候选应定义 PuLP model、求解模型、打印 status/objective，并在提供 `OUTPUT_LP_PATH` 时导出 LP。Execution 记录代码是否运行、solver status、objective value、LP path、runtime 和 errors。

这一步只验证候选诱导出一个可求解数学程序，不证明该程序匹配目标补货模型。

### 4.3 LP Parser and LP Structure Graph

LP parser 是面向 PuLP-exported LP files 的轻量 parser。它抽取：

- optimization sense；
- objective expression；
- constraint names and expressions；
- bounds；
- binary variables；
- variable names。

LP structure graph 提供变量—约束 incidence 级别的 weak evidence，用于辅助检测 Big-M-like linking、inventory recurrence candidates 和 fixed-cost binary terms。该 graph 是辅助证据，不是完整 algebraic graph-matching proof。

Parser 依赖 PuLP LP format。Anonymous PuLP constraints 可能以 `_C1`、`_C2` 等名字出现；这些 constraints 可以被解析，但 autogenerated names 不应被当作 semantic evidence。因此 prompt 要求 generated code 显式命名 constraints。

### 4.4 Structure Rules and Certificates

ReplenishVerifier 通过分层证据检查结构：

1. variable-name hints，例如 `Q`、`I`、`B`、`Y`、`order_qty`、`inventory`、`backlog` 和 `setup`；
2. constraint-name hints，例如 `inventory_balance`、`flow`、`capacity`、`big_m` 和 `link`；
3. expression-supported evidence，即相关变量是否参与预期约束模式；
4. index and incidence evidence，用于识别重复或相邻 inventory states；
5. Big-M-like coefficients 的 magnitude hints。

每条规则产生 certificate，包括 rule name、是否 required、pass/fail、score、evidence、missing reason、repair hint 和可用的附加诊断。Aggregate `structure_score` 只对 required structures 取平均。

Certificate 设计同时支持 selection 和 explanation。例如，一个候选可以 executable 且 optimal，但仍因缺少 `inventory_balance` 或 `big_m_constraint` 被记录为结构缺失。

### 4.5 No-Reference Candidate Selection

`ReplenishVerifier-Full` 使用 ground-truth-free score：

\[
S(c)=0.25E(c)+0.25Z(c)+0.35SC(c)+0.15Sem(c),
\]

其中 \(E\) 是 executability，\(Z\) 是 optimal solver status，\(SC\) 是 required-structure score，\(Sem\) 是基于 missing required structures 的 semantic consistency。Hard selection gate 默认只给 executable + `Optimal` candidates 非零 formal selection score。

仓库还包含 `Structure-Grounded Consistency`，它结合 executable code、solver status、required-structure coverage、LP artifact structure coverage 和 candidate objective consensus。它与 `OR-R1-like Voting` 不同：OR-R1-like Voting 是 generic executable / valid-code / objective-consensus baseline，不使用 replenishment structures。

`reference_objective` 不被 formal ranking helpers 使用。它只用于最终 evaluation metrics。

### 4.6 Feedback, Repair Prompts, and Preference Data

缺失 required structures 会被转换成自然语言反馈和 repair prompts。ReplenishVerifier-specific repair prompts 可以提到 inventory balance、capacity、shortage/backlog、fixed cost、binary setup 或 Big-M links。Generic OptiRepair-like prompts 只使用 generic execution、solver 和 LP-artifact audit feedback，不包含 missing replenishment-structure labels。

Preference-data builder 可以使用 executable status、optimal status、structure completeness 和 repair-feedback counts 构造 chosen/rejected pairs。这些 pairs 是 DPO、PRM、reranking 或类似方法的 future training data，并不意味着 preference-learning experiment 已经完成。

### 4.7 Prompt Leakage Controls and Practical Diagnostics

为避免 prompt 侧泄漏，主实验使用不暴露 `expected_structures` 的 `hidden_verifier` 或 `plain` prompt；会显式暴露 expected structures 的 `structured` prompt 仅用于 guided generation 或 appendix ablation。本文区分 generic repair prompts 与 structure-aware repair prompts：前者只使用 execution/solver/audit 反馈，后者才允许使用 missing replenishment structures 和 rule-level certificates。Preference pairs 仅作为未来 DPO/PRM/LoRA 等训练的候选学习信号；除非实际训练并评估，否则不声称训练带来提升。Runtime overhead 和 variable naming robustness 是后续真实实验必须报告的指标，其中命名扰动只是 lightweight text-level rewriting，不是完整 AST-safe renaming。

---

## 5. 实验协议

### 5.1 研究问题

- **RQ1：** replenishment-specific LP-structure certificates 是否能发现 executable status 和 solver status 无法发现的错误？
- **RQ2：** structure-grounded candidate selection 在真实 LLM candidates 上是否优于 solver filtering、objective consensus、generic LP statistics 和 generic audit baselines？
- **RQ3：** 真实 LLM-generated replenishment models 中最常见的 missing structures 是什么？
- **RQ4：** 在 \(K=1,2,4\) 等低候选预算下，各方法如何变化？
- **RQ5：** 如果运行真实二轮 repair，structure-aware repair prompts 是否能提升 candidate structure completeness？

### 5.2 对比方法

| Method | Purpose | Selection uses reference objective? |
|---|---|---|
| Direct | first candidate | No |
| Best-of-K | first viable candidate among K | No |
| Solver-Filter | executable / Optimal / objective-present signal | No |
| OR-R1-like Voting | lightweight executable / valid-code / objective-consensus signal-isolation baseline | No |
| SIRL-like LP-Stats | lightweight generic LP artifact statistics baseline | No |
| OptArgus-like Audit | lightweight generic optimization-model audit baseline | No |
| OptiRepair-like Repair-Prompt | lightweight generic repair-readiness baseline | No |
| Structure-Grounded Consistency | execution + solver + required structure + LP artifact structure + candidate consensus | No |
| ReplenishVerifier-Full | execution + solver + replenishment structure + semantic consistency | No |
| ReplenishVerifier-Repair | only after real repaired candidates are generated and evaluated | No |

所有 `*-like` 条目都是 lightweight signal-isolation baselines，不是 faithful reproduction。

### 5.3 主实验表

| Method | Executable Rate | Optimal Rate | Objective Accuracy | Relative Error | Structure Completeness | Constraint Coverage | Avg. Runtime |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Solver-Filter | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| OR-R1-like Voting | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| SIRL-like LP-Stats | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| OptArgus-like Audit | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| ReplenishVerifier-Full | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |

### 5.4 Ablations

| Variant | Purpose | Objective Accuracy | Structure Completeness | Constraint Coverage |
|---|---|---:|---:|---:|
| Structure-Only | remove solver-status weighting | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Structure-Grounded Consistency | add candidate objective consensus to structure evidence | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Full + objective consensus | optional appendix ablation | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Generic LP stats only | replace replenishment structures with LP statistics | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` | `[TO FILL AFTER REAL LLM EXPERIMENT]` |

### 5.5 Repair and Preference Data

| Experiment | Status | Result |
|---|---|---|
| Structure-aware repair prompt generation | available in code | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Real second-round repair generation | not yet claimed | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Re-evaluation of repaired candidates | not yet claimed | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| Verifier-guided preference data | available as future training data | `[TO FILL AFTER REAL LLM EXPERIMENT]` |
| DPO / PRM / reranker training | future work unless implemented | `[TO FILL AFTER REAL LLM EXPERIMENT]` |

---

## 6. 实验结果

所有定量结果都等待真实 LLM experiments。Synthetic smoke-test outputs 不能作为主实验证据。

`[TO FILL AFTER REAL LLM EXPERIMENT]`

---

## 7. 案例研究

真实 case studies 只能在 real LLM candidate generation 和 no-leakage evaluation 完成后选择。推荐案例包括：

1. executable/optimal 但缺少 inventory balance 的候选；
2. objective-consensus candidates 共同缺少 capacity 或 Big-M constraint；
3. generic LP-statistics baseline 选择结构不完整候选；
4. generic repair feedback 未指出 replenishment-specific missing structure；
5. ReplenishVerifier 选择 required-structure coverage 更强的候选。

`[TO FILL AFTER REAL LLM EXPERIMENT]`

---

## 8. 局限性

- LP parser 依赖 PuLP LP format，不是完整 solver-independent LP/MPS parser。
- Structure verification 是 heuristic，不是完整 mathematical-equivalence verification。
- 当前 verifier 可能漏掉错误系数、错误时间索引、错误初始/终止边界条件和不合适的 Big-M 数值。
- 当前 benchmark 覆盖的补货模型族有限。
- Selection weights 是人工设计的，需要后续校准或学习。
- Repair effectiveness 需要真实 LLM repaired candidates 和重新评估。
- Preference data 不等于 DPO、PRM、reranker 或 RL training 已经完成。
- 所有 `*-like` baselines 都是 lightweight signal-isolation baselines，不是 prior systems 的 faithful reproduction。
- 执行 generated code 有安全风险；不可信候选应在 sandbox 中执行。

---

## 9. 结论

ReplenishVerifier 将 LLM-based replenishment modeling evaluation 的重点转向约束级 LP structure。Executable code、solver optimality 和 objective consensus 都是有用但不充分的信号。通过导出并解析 generated PuLP code 诱导出的 LP artifact，verifier 检查 problem-type-required replenishment structures 是否存在，并生成可解释 certificates，用于 selection、feedback、repair prompting 和 future preference-data construction。

当前论文草稿在真实 LLM experiments 完成并通过审计前刻意避免定量 claim。最终实证结论保留为 `[TO FILL AFTER REAL LLM EXPERIMENT]`。
