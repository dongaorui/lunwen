# ReplenishVerifier 静态代码清理审计报告

生成日期：2026-06-14

本报告只基于静态目录和文本检查生成，没有运行真实 LLM 实验、没有运行大模型、没有执行耗时实验，也没有删除任何文件。`references/`、`references_merged_for_claude/`、已有 `runs/` 实验结果均未修改。

## 审计范围与限制

本次检查覆盖：

- 顶层 Python 包与 `pyproject.toml`；
- `replenishverifier/`、`replenish/`、`scripts/`、`tests/`；
- `README.md` 与 `docs/` 中和命令/包名相关的内容；
- 可见的缓存文件和已有实验输出目录。

限制：

- 未运行 `pytest`、未运行实验脚本、未执行候选代码；
- “是否被 import / 是否被命令调用”是静态文本搜索结论，不等价于完整动态依赖分析；
- `runs/` 和 `outputs/` 中已有结果默认视为实验产物，不建议本次清理直接删除。

---

## 1. 当前主包名判断

当前主包名应该是：

- `replenishverifier`

依据：

- `pyproject.toml` 中项目名为 `replenishverifier`；
- `README.md` 项目结构、方法模块、正式实验命令均以 `replenishverifier` 为主；
- `scripts/` 和 `tests/` 当前均引用 `replenishverifier.*`；
- 主要实现代码都位于 `replenishverifier/`，包括 benchmark、solver、verifier、pipeline、experiments、llm、data 等模块。

项目中仍存在 `replenish/`。静态检查显示它不是独立实现，而是兼容旧命令的薄 alias：

- `replenish/__init__.py` 明确写着：`Compatibility package alias for command examples using python -m replenish...`；
- `replenish/experiments/run_all_methods.py` 仅转发到 `replenishverifier.experiments.run_all_methods.main`；
- `replenish/experiments/build_paper_tables.py` 仅转发到 `replenishverifier.experiments.build_paper_tables.main`；
- `replenish/llm/run_generation.py` 仅转发到 `replenishverifier.llm.run_generation.main`；
- `replenish/experiments/audit_leakage.py`、`analyze_error_types.py`、`extract_case_studies.py` 也是转发入口。

判断：`replenish/` 很可能是旧包名兼容层，不是当前主代码。短期可以保留，避免旧草稿或旧命令立刻失效；等 README、论文草稿、历史命令全部统一到 `replenishverifier` 并通过测试后，再考虑移入 `archive/legacy_unused/`。

---

## 2. 重复代码检查

| 模块类别 | 当前主要实现 | 可能重复/兼容文件 | 判断 | 建议处理方式 |
|---|---|---|---|---|
| parser | `replenishverifier/verifier/lp_parser.py` | 未发现另一个实际 `lp_parser.py` | 没有真实重复实现 | 保留 |
| scoring | `replenishverifier/pipeline/scoring.py` | 未发现另一个实际 `scoring.py` | 没有真实重复实现；但 `pipeline/run_candidate_selection.py` 是较早的单方法 selection 入口 | 保留 |
| experiment runner | `replenishverifier/experiments/run_all_methods.py` | `replenish/experiments/run_all_methods.py` | 后者只是旧包名 alias | 暂时保留 |
| baseline method | `replenishverifier/experiments/baselines.py`、`methods.py` | 未发现 `replenish/` 下真实 baseline 实现 | 没有真实重复实现 | 保留 |
| paper table builder | `replenishverifier/experiments/build_paper_tables.py` | `replenish/experiments/build_paper_tables.py` | 后者只是旧包名 alias | 暂时保留 |
| llm candidate generator | `replenishverifier/llm/run_generation.py` | `replenish/llm/run_generation.py` | 后者只是旧包名 alias；但旧文档中出现过 `generate_candidates` 入口名，当前未发现对应模块 | 暂时保留 |
| repair candidate generator | `replenishverifier/llm/run_repair_generation.py` | 未发现 `replenish/llm/run_repair_generation.py` alias | 当前主实现只有 `replenishverifier` 入口 | 保留 |
| old candidate selection | `replenishverifier/experiments/run_all_methods.py` | `scripts/run_candidate_selection.py` + `replenishverifier/pipeline/run_candidate_selection.py` | 可能是早期单方法候选选择入口；仍被脚本调用 | 暂时保留 |
| structure verification | `scripts/run_structure_verification.py` + `replenishverifier/verifier/*` | 无重复实现 | README 中仍推荐该脚本检查 reference LP | 保留 |

### README 中命令和实际包名一致性

当前 `README.md` 正文主命令使用 `python -m replenishverifier...`，与主包名一致。未在当前 README 正文中发现 `python -m replenish...`。

需要注意的命令名差异：

- 当前代码实际 LLM 生成入口是 `python -m replenishverifier.llm.run_generation`；
- 用户需求中给出的目标命令示例使用 `python -m replenishverifier.llm.generate_candidates`；
- 静态检查未发现 `replenishverifier/llm/generate_candidates.py`。

建议：文档应优先写当前可用入口 `run_generation`；如果论文或后续指南坚持使用 `generate_candidates`，需要另行新增一个 alias 模块，而不是只改文档。

### tests 中旧包名引用

`tests/` 当前引用均为 `replenishverifier.*`，未发现 `from replenish...` 或 `import replenish...` 的测试引用。

### scripts 中旧包名引用

`scripts/` 当前引用均为 `replenishverifier.*`，未发现旧包名 `replenish.*` 引用。

---

## 3. 可疑无用文件列表

| 路径 | 可能原因 | 是否被 import | 是否被命令调用 | 建议 |
|---|---|---:|---:|---|
| `replenish/` | 旧包名兼容层，真实实现已迁移到 `replenishverifier/` | 是，作为 `python -m replenish...` 兼容入口间接导入主包 | 可能被旧草稿/旧命令调用；当前 README 不再主推 | 暂时保留 |
| `replenish/experiments/run_all_methods.py` | 仅转发到 `replenishverifier.experiments.run_all_methods` | 否，当前主代码未 import 它 | 仅当用户运行旧命令 `python -m replenish.experiments.run_all_methods` 时调用 | 暂时保留 |
| `replenish/experiments/build_paper_tables.py` | 仅转发到 `replenishverifier.experiments.build_paper_tables` | 否 | 仅旧命令调用 | 暂时保留 |
| `replenish/experiments/audit_leakage.py` | 仅转发到 `replenishverifier.experiments.audit_leakage` | 否 | 仅旧命令调用 | 暂时保留 |
| `replenish/experiments/analyze_error_types.py` | 仅转发到 `replenishverifier.experiments.analyze_error_types` | 否 | 仅旧命令调用 | 暂时保留 |
| `replenish/experiments/extract_case_studies.py` | 仅转发到 `replenishverifier.experiments.extract_case_studies` | 否 | 仅旧命令调用 | 暂时保留 |
| `replenish/llm/run_generation.py` | 仅转发到 `replenishverifier.llm.run_generation` | 否 | 仅旧命令调用 | 暂时保留 |
| `scripts/run_candidate_selection.py` | 早期单一 candidate-selection 脚本；正式实验已使用 `experiments/run_all_methods.py` | 否 | 是，作为脚本入口存在 | 暂时保留 |
| `replenishverifier/pipeline/run_candidate_selection.py` | 被 `scripts/run_candidate_selection.py` 调用，可能是旧 pipeline | 是，被脚本 import | 间接被脚本调用 | 暂时保留 |
| `scripts/evaluate_results.py` | 早期结果打印脚本；正式结果汇总已在 `experiments/evaluation.py` 和 `build_paper_tables.py` | 否 | 是，作为脚本入口存在 | 暂时保留 |
| `data/benchmark.jsonl` | 早期小 benchmark 输出，不是 `data/generated/` 规范路径 | 否 | 否，当前 README 不主推 | 暂时保留 |
| `data/benchmark_run.jsonl` | 早期运行输出，不是 `data/generated/` 规范路径 | 否 | 否，当前 README 不主推 | 暂时保留 |
| `outputs/reference_lp/` | 早期 reference LP 输出，README 当前更推荐 `runs/lp/...` | 否 | 否 | 暂时保留 |
| `outputs/run_reference_lp/` | 早期 reference solve 输出 | 否 | 否 | 暂时保留 |
| `outputs/structure_check.jsonl` | 早期 structure check 输出 | 否 | 否 | 暂时保留 |
| `outputs/structure_check_run.jsonl` | 早期 structure check 输出 | 否 | 否 | 暂时保留 |
| `runs/exp_demo/` | synthetic demo 运行结果；不是正式论文结果 | 否 | 否 | 暂时保留 |
| `runs/smoke/` | smoke run 运行结果；不是正式论文结果 | 否 | 否 | 暂时保留 |
| `**/__pycache__/` | Python 字节码缓存 | 否 | 否 | 可以删除缓存文件 |
| `.pytest_cache/` | pytest 缓存 | 否 | 否 | 可以删除缓存文件 |

> 注意：上表中的 `runs/` 和 `outputs/` 产物虽然可能不是正式结果，但用户明确要求不要修改已有 `runs/` 实验结果；因此本次只标记“暂时保留”，不建议直接删除。

---

## 4. 文件/目录清理建议表

| 文件/目录 | 当前状态 | 是否建议删除 | 删除风险 | 建议处理方式 |
| ----- | ---- | -----: | ---- | ------ |
| `replenishverifier/` | 当前主包，包含核心实现 | 否 | 极高；删除会破坏项目 | 保留 |
| `replenish/` | 旧包名兼容层，薄转发到 `replenishverifier` | 否 | 中等；旧命令、旧草稿示例可能依赖 | 暂时保留 |
| `replenish/experiments/*.py` | 旧包名实验入口 alias | 否 | 中等；删除会破坏 `python -m replenish.experiments...` | 暂时保留 |
| `replenish/llm/run_generation.py` | 旧包名 LLM 生成入口 alias | 否 | 中等；删除会破坏旧生成命令 | 暂时保留 |
| `scripts/run_candidate_selection.py` | 早期单方法 selection CLI | 否 | 中等；可能仍用于轻量 debug | 暂时保留 |
| `replenishverifier/pipeline/run_candidate_selection.py` | 被早期脚本调用的单方法 pipeline | 否 | 中等；删除会破坏 `scripts/run_candidate_selection.py` | 暂时保留 |
| `scripts/evaluate_results.py` | 早期结果汇总脚本 | 否 | 低到中；可能用于快速打印旧结果 | 暂时保留 |
| `data/benchmark.jsonl` | 早期 benchmark 输出 | 否 | 中等；可能是已生成数据 | 暂时保留 |
| `data/benchmark_run.jsonl` | 早期 benchmark 输出 | 否 | 中等；可能是已生成数据 | 暂时保留 |
| `outputs/` | 旧/当前输出目录，含 LP 和 structure check 结果 | 否 | 中等；可能含可复现实验材料 | 暂时保留 |
| `runs/exp_demo/` | demo 实验结果 | 否 | 中等；用户要求不修改已有 `runs/` | 暂时保留 |
| `runs/smoke/` | smoke 实验结果 | 否 | 中等；用户要求不修改已有 `runs/` | 暂时保留 |
| `**/__pycache__/` | Python 缓存 | 是 | 低；可自动再生成 | 可以删除缓存文件 |
| `.pytest_cache/` | pytest 缓存 | 是 | 低；可自动再生成 | 可以删除缓存文件 |

---

## 5. 不建议删除的文件和目录

以下目录默认不要删：

- `references/`
- `references_merged_for_claude/`
- `papers/`
- `docs/`
- `data/generated/`
- `data/candidates/`
- `runs/`
- `outputs/`
- `tests/`

原因：

- `references/` / `references_merged_for_claude/`：外部参考资料或合并后的参考文本，不应在代码清理中改动；
- `papers/`：论文草稿与实验叙述来源；
- `docs/`：项目说明与审计记录；
- `data/generated/`、`data/candidates/`：benchmark 和候选数据，可能用于复现实验；
- `runs/`：实验结果，用户已明确要求不要修改；
- `outputs/`：历史输出和 LP artifact，可能用于排查；
- `tests/`：回归测试，不应作为无用文件删除。

---

## 6. 建议后续清理顺序

建议按以下顺序清理，避免误删或破坏可复现性：

1. 先统一包名：正式文档、README、论文草稿、命令示例都使用 `replenishverifier`。
2. 再修 README 命令：确认 LLM 生成入口是当前实际存在的 `replenishverifier.llm.run_generation`，或新增 `generate_candidates` alias 后再使用该命令名。
3. 再归档旧包：等旧命令不再需要后，把 `replenish/` 移入 `archive/legacy_unused/`。
4. 再运行 pytest：确认归档旧包不会破坏 `tests/` 和主流程。
5. 再检查 smoke 流程：只做小规模 CPU smoke，不跑真实 LLM 大实验。
6. 最后再删除缓存：清理 `__pycache__` 和 `.pytest_cache`。

---

## 7. 安全清理命令建议

正式删除前，请先确认 git 状态，并确保没有未提交的重要结果：

```bash
git status --short
```

只建议删除缓存文件，不建议直接删除代码、数据或实验结果：

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
```

如果未来决定归档旧兼容包，建议先做移动而不是删除，并在新分支上操作：

```bash
git status --short
mkdir -p archive/legacy_unused
mv replenish archive/legacy_unused/replenish
python -m pytest
```

只有在测试通过、README 和论文命令都不再引用旧包名后，才考虑进一步删除归档内容。

---

## 8. 本次审计结论

- 当前主包名清晰：`replenishverifier`。
- `replenish/` 很可能是旧包名兼容层，不是重复实现；短期建议暂时保留。
- 未发现 `tests/` 或 `scripts/` 仍引用旧包名。
- 当前 README 主命令与 `replenishverifier` 一致，但需要注意 `generate_candidates` 不是当前实际存在的模块名。
- `run_all_methods.py`、`build_paper_tables.py`、`analyze_error_types.py`、`extract_case_studies.py`、`audit_leakage.py` 等正式实验入口位于 `replenishverifier/experiments/`。
- 最安全的立即清理对象只有缓存文件：`__pycache__/` 和 `.pytest_cache/`。
