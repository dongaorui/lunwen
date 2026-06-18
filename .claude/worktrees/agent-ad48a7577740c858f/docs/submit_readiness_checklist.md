# Submit Readiness Checklist

Status values:

- `done`: implemented or documented in the current repository.
- `TODO`: required work not yet completed.
- `blocked_by_experiment`: cannot be completed until real LLM experiments or repair experiments are run.

All result cells in paper-facing tables must remain `[TO FILL AFTER REAL LLM EXPERIMENT]` until real LLM experiments are completed and audited.

## Code readiness

| Item | Status | Evidence / next step |
|---|---|---|
| Benchmark generation for five replenishment families | done | `replenishverifier/benchmark/templates.py`, `generator.py`. |
| Replenishment-specific semantic metadata | done | `semantic_frame`, `replenishment_entities`, `replenishment_modeling_steps`. |
| Problem-type-aware required / optional schema | done | `replenishverifier/data/structure_schema.py`. |
| LP artifact parser | done | `replenishverifier/verifier/lp_parser.py`; prototype parser for PuLP LP format. |
| LP structure evidence and certificates | done | `replenishverifier/verifier/structure_rules.py`, `lp_graph.py`. |
| No-reference candidate scoring | done | `replenishverifier/pipeline/scoring.py`, `experiments/methods.py`. |
| Lightweight signal-isolation baselines | done | `experiments/baselines.py`, `experiments/methods.py`. |
| Structure-Grounded Consistency selector | done | Uses execution, solver status, LP artifact structure coverage, required structures, and candidate objective consensus. |
| Leakage audit | done | `experiments/audit_leakage.py`; must be run after real experiments. |
| Real LLM generation CLI | done | `replenishverifier/llm/run_generation.py` supports `--prompt_type hidden_verifier|plain|structured` and `--seed`; not run in this documentation pass. |
| Repair generation CLI | done | `replenishverifier/llm/run_repair_generation.py`; real repair experiment still TODO. |
| Generic and structure-aware repair prompt artifacts | done | `run_all_methods` writes `repair_prompts.*` and `generic_repair_prompts.*`; generic prompts exclude replenishment-specific missing labels. |
| Runtime overhead analyzer | done | `python -m replenishverifier.experiments.analyze_runtime_overhead --exp_dir <exp_dir>` reports missing fields as `NA`. |
| Preference-pair construction | done | `experiments/build_preference_data.py`; metadata marks no-reference construction and future training data only. |
| Variable naming robustness perturbation | done | `rename_variables_for_robustness.py --mode descriptive_to_anonymous`; lightweight text-level perturbation, not AST-safe. |
| Stronger coefficient/index verification | TODO | Needed to reduce false positives beyond high-level structure presence. |
| More replenishment families | TODO | Lead time, lost sales, service levels, supplier constraints, transportation, multi-echelon. |
| Sandboxing for untrusted external code | TODO | Current executor should be sandboxed before running untrusted candidates. |

## Documentation readiness

| Item | Status | Evidence / next step |
|---|---|---|
| README title and positioning aligned with current thesis | done | README uses constraint-level LP-structure verification positioning. |
| README warns against synthetic result overclaiming | done | Smoke/demo results are labeled sanity checks only. |
| `*-like` baselines described as lightweight signal-isolation baselines | done | README and paper drafts use this framing. |
| Real LLM experiment checklist | done | `docs/real_llm_experiment_checklist.md`. |
| Code/claim risk audit | done | `docs/code_and_claim_risk_audit.md`; may be updated again after real experiments. |
| CCF-A revision roadmap | done | `docs/ccfa_revision_roadmap.md`. |
| Submit readiness checklist | done | This file. |
| Experiment operation guide synchronized with prompt/repair/runtime safeguards | done | `docs/experiment_operation_guide.md` documents `hidden_verifier`, seed caveats, fair repair prompts, and runtime overhead. |
| All docs remove stale completed-result claims | TODO | Search before submission; keep real result slots as `[TO FILL AFTER REAL LLM EXPERIMENT]`. |

## Real LLM experiment readiness

| Item | Status | Evidence / next step |
|---|---|---|
| Decide model and local path | TODO | Record model name/path/version before running generation. |
| Decide benchmark size | TODO | Recommended first run: 50 instances, K=4. Larger run only after sanity check. |
| Generate real benchmark split | TODO | Use `scripts/generate_benchmark.py`; no large benchmark was run in this pass. |
| Generate real LLM candidates | TODO | Do not use demo candidates for main claims. |
| Run all-method evaluation | blocked_by_experiment | Requires real candidate JSONL. |
| Run leakage audit | blocked_by_experiment | Must pass before using results. |
| Analyze error types | blocked_by_experiment | Requires real run output. |
| Extract real case studies | blocked_by_experiment | Must use real LLM candidates for main paper cases. |
| Build paper tables | blocked_by_experiment | Every value remains `[TO FILL AFTER REAL LLM EXPERIMENT]`. |
| Run real repair generation | TODO | Required before reporting repair effectiveness. |
| Evaluate repaired candidates | blocked_by_experiment | Required after repair candidate generation. |
| Build preference data | optional | Future training data only unless training is run. |
| Train DPO/PRM/reranker | TODO | Future experiment; do not claim completed. |

## Paper readiness

| Item | Status | Evidence / next step |
|---|---|---|
| English title updated | done | `papers/replenishverifier_draft_en.md`. |
| Chinese title updated | done | `papers/replenishverifier_draft_zh.md`. |
| Abstract explains executable/Optimal is insufficient | done | Both drafts. |
| Contributions limited to current code capability | done | Benchmark/repair/training are not overclaimed as completed empirical contributions. |
| Related Work structured by required topics | done | Both drafts include LLMs for optimization, solver-informed verification, data synthesis, audit/repair, and inventory replenishment. |
| Method details include problem setting and benchmark schema | done | Both drafts. |
| Method details include LP parser / structure graph / certificates | done | Both drafts. |
| Method details include no-reference selection | done | Both drafts. |
| Experiment protocol uses placeholders | done | Tables use `[TO FILL AFTER REAL LLM EXPERIMENT]`. |
| Real results discussion | blocked_by_experiment | Must be written after audited real LLM run. |
| Real case studies | blocked_by_experiment | Must come from real LLM outputs. |
| Final conclusion with empirical claims | blocked_by_experiment | Keep empirical conclusion as placeholder until results exist. |

## CCF-A risk checklist

| Risk | Status | Mitigation |
|---|---|---|
| Overclaiming smoke/demo results | TODO | Before submission, verify all main empirical claims come from real LLM experiments. |
| Baselines perceived as weak | TODO | Use `*-like` only as signal-isolation baselines; add stronger real comparisons if feasible. |
| Verifier false positives due to heuristic parsing | TODO | Add coefficient/index/boundary diagnostics and transparent limitations. |
| Limited benchmark diversity | TODO | Add more replenishment families or external subsets if time permits. |
| No repair evidence | blocked_by_experiment | Run and evaluate real repaired candidates before claiming repair. |
| No training evidence | TODO | Do not claim DPO/PRM/RL gains unless training is implemented and evaluated. |
| Reference-objective leakage | done / ongoing | Run `audit_leakage` after each real experiment and report pass/fail. |
| Reproducibility gaps | TODO | Record model path, hardware, seed, K, prompt, extraction, timeout, solver version, and exact code commit. |
| Security risk from executing generated code | TODO | Use sandboxing for untrusted external candidates. |

## Submission gate

Do not submit a results-bearing version until the following are complete:

1. real LLM candidate generation;
2. all-method evaluation;
3. no-leakage audit;
4. paper tables populated from real run outputs;
5. real case studies extracted;
6. limitations updated with observed failure modes;
7. all synthetic/demo-only claims removed from main evidence.
