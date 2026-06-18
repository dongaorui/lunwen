# Paper and README synchronization report

## 1. Files read

Primary audit/protocol files:

- `docs/literature_audit.md`
- `docs/code_and_claim_risk_audit.md`
- `docs/paper_experiment_revision_plan.md`
- `docs/real_llm_experiment_checklist.md`

Requested but not present under the exact names:

- `docs/baseline_coverage_check.md`
- `docs/literature_driven_experiment_plan.md`
- `docs/final_real_llm_experiment_protocol.md`

Equivalent files used instead:

- `docs/paper_experiment_revision_plan.md`
- `docs/real_llm_experiment_checklist.md`

Experiment sanity-check outputs read:

- `runs/smoke_literature_driven/summary.md`
- `runs/smoke_literature_driven/case_studies.md`

Project documents read/updated:

- `README.md`
- `papers/replenishverifier_draft_zh.md`

## 2. Files updated or generated

Updated:

- `papers/replenishverifier_draft_zh.md`
- `README.md`

Generated:

- `papers/replenishverifier_draft_en.md`
- `docs/paper_readme_sync_report.md`

## 3. Chinese paper update summary

`papers/replenishverifier_draft_zh.md` was rewritten around the current project state:

- New title: **ReplenishVerifier：面向大语言模型供应链补货优化自动建模的约束级 LP 结构验证方法**.
- Structure now follows:
  1. 摘要
  2. 引言
  3. 相关工作
  4. 问题定义
  5. 方法
  6. 实验设计
  7. 实验结果
  8. 分析与案例研究
  9. 局限性
  10. 结论
- Clarifies that ReplenishVerifier is not a general LLM-for-OR framework.
- Emphasizes LP artifact export from LLM-generated PuLP code.
- Describes parsing of variables, constraints, objective, binary declarations, and bounds.
- Describes structure checks for inventory balance, shortage/backlog, capacity, fixed ordering cost, binary setup/order trigger, and Big-M.
- Separates formal selection from final evaluation.
- Uses `[TO FILL AFTER REAL LLM EXPERIMENT]` for all real LLM experiment results.
- Treats synthetic smoke tests only as sanity checks.

## 4. English paper generation summary

`papers/replenishverifier_draft_en.md` was generated with content aligned to the Chinese draft, but not as a mechanical sentence-by-sentence translation. It uses AI/OR paper style and preserves the same safety constraints:

- no fabricated real results;
- `[TO FILL AFTER REAL LLM EXPERIMENT]` placeholders for unfinished empirical sections;
- no first/SOTA/no-prior-work overclaim;
- `*-like` baseline names preserved;
- no reference-objective selection.

## 5. README update summary

`README.md` was rewritten to include:

1. project overview;
2. paper positioning;
3. differences from related work;
4. project structure;
5. installation;
6. benchmark generation;
7. synthetic smoke test;
8. strong baseline smoke test;
9. real LLM experiment;
10. repair experiment;
11. leakage audit;
12. output file explanations;
13. cautions and limitations.

It explicitly states:

- synthetic demo is not a formal result;
- real LLM candidates are required for the main experiment;
- formal selection does not use `reference_objective`;
- `SIRL-like`, `OptArgus-like`, `OptiRepair-like`, and `OR-R1-like` are lightweight baselines, not full reproductions;
- recommended workflow is 50 examples with K=4 first, then possibly 300;
- local model experiments do not require an API;
- local Qwen runs should pass a local model directory to `--model`.

## 6. Smoke-test handling

The following smoke outputs were acknowledged but not used as main results:

- `runs/smoke_literature_driven/summary.md`
- `runs/smoke_literature_driven/case_studies.md`

They are described only as sanity-check artifacts showing that the pipeline, baselines, case extraction, table generation, and leakage audit run end to end.

## 7. Overclaim prevention

The updated paper and README avoid:

- claiming to be the first solver-in-the-loop OR method;
- claiming to be the first LP-artifact supervision method;
- claiming full reproduction of SIRL, OptArgus, OptiRepair, OR-R1, or StepORLM;
- claiming real LLM results before they are run;
- treating smoke-test outputs as formal empirical evidence;
- describing ReplenishVerifier as a replacement for generic hallucination detectors, repair systems, solver validation, or objective evaluation.

The intended claim is restricted to:

> ReplenishVerifier provides replenishment-specific LP-structure evidence that complements generic solver execution, LP artifact statistics, objective consensus, hallucination auditing, and repair prompting.

## 8. Reference objective policy

The updated documents state that formal selection does not use `reference_objective`.

Allowed selection signals:

- executable / runtime error / timeout;
- solver status;
- candidate objective presence;
- objective consensus among candidates;
- generic LP artifact statistics;
- generic audit issues;
- replenishment structure labels for ReplenishVerifier variants.

Forbidden selection signals:

- distance to `reference_objective`;
- selecting the objective closest to the reference;
- using reference objective inside Solver-Filter or OR-R1-like Voting.

`reference_objective` is only for final evaluation metrics such as objective accuracy and relative error.

## 9. Remaining `[TO FILL AFTER REAL LLM EXPERIMENT]` items

The following sections require real experiments before completion:

- Chinese paper abstract empirical summary;
- English paper abstract empirical summary;
- dataset counts in main experiment;
- candidate-generation settings:
  - model name/path;
  - hardware;
  - temperature/top-p/max tokens;
  - prompt details;
- main result table;
- ablation table;
- low-resource K table;
- repair experiment table;
- real LLM case studies:
  - missing inventory balance;
  - missing Big-M;
  - missing capacity;
- final empirical conclusion.

## 10. What to update after real experiments

After real LLM candidates and repair experiments finish, update:

1. `papers/replenishverifier_draft_zh.md`
   - Abstract empirical sentence;
   - Section 6 main results;
   - Section 6 ablation;
   - Section 6 low-resource K;
   - Section 6 repair experiment;
   - Section 7 real case studies;
   - Conclusion empirical summary.
2. `papers/replenishverifier_draft_en.md`
   - same corresponding sections.
3. `README.md`
   - add links/paths to final experiment outputs if desired;
   - do not replace the caution that smoke tests are not main results.
4. `docs/paper_experiment_revision_plan.md` or a new final result note if the final method set changes.

Always run and report:

```bash
python -m replenishverifier.experiments.audit_leakage --exp_dir <real_exp_dir>
```

before using the results in the paper.
