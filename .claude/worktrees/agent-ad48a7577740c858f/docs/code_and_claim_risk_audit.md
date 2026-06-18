# Code and claim risk audit

This audit checks the repository against the literature-driven risks in the user request. It also records the changes made during this pass.

## Files inspected

Core code:
- `replenishverifier/experiments/methods.py`
- `replenishverifier/experiments/baselines.py`
- `replenishverifier/experiments/run_all_methods.py`
- `replenishverifier/experiments/evaluation.py`
- `replenishverifier/experiments/audit_leakage.py`
- `replenishverifier/experiments/extract_case_studies.py`
- `replenishverifier/pipeline/scoring.py`
- `replenishverifier/verifier/lp_parser.py`
- `replenishverifier/verifier/structure_rules.py`
- `replenishverifier/llm/code_extractor.py`
- `replenishverifier/llm/prompt_builder.py`
- `replenishverifier/llm/run_generation.py`

Docs/paper:
- `README.md`
- `papers/replenishverifier_draft_zh.md`

References read-only:
- `references_merged_for_claude/extra_paper_notes/*.txt`
- `references_merged_for_claude/matrices/*.txt`
- `references_merged_for_claude/project_drafts/ReplenishVerifier_draft_zh.txt`

## Risk checklist

| Risk | Status | Evidence / fix |
|---|---|---|
| 1. Selection uses `reference_objective`. | No leakage found in current scoring code; older reference draft text was risky. | `compute_score()` reports objective metrics but selection score uses `solver_selection_score()` or `full_selection_score()` without reference objective. `audit_leakage.py` checks selected rows. Paper and README now emphasize evaluation-only reference objectives. |
| 2. Solver-Filter uses reference objective. | No leakage found. | `solver_selection_score()` uses executable, optimal status, and objective presence only. Selection policy says no reference objective. |
| 3. ReplenishVerifier-Full score inconsistent with paper formula. | Fixed/updated. | Code formula is `0.25 executable + 0.25 optimal + 0.35 structure + 0.15 semantic`, no objective closeness. Live paper already mostly matched; revision plan and docs reinforce it. Optional objective consensus is explicitly separate and reference-free. |
| 4. SIRL-like / OptArgus-like baseline uses replenishment-specific `expected_structures`. | No leakage found; strengthened. | Baseline code only uses execution and generic LP/audit stats. Added OR-R1-like baseline with candidate consensus and code/LP validity only. |
| 5. OptiRepair-like baseline generates inventory_balance / Big-M semantic feedback. | No leakage found. | `generic_repair_feedback()` only mentions Python/PuLP execution, objective, variables, constraints, empty/underspecified model, placeholder names. It does not mention inventory balance, Big-M, fixed costs, or shortage. |
| 6. Repair prompt mixes generic solver repair and replenishment-specific repair. | Clarified. | `OptiRepair-like Repair-Prompt` uses `generic_repair_feedback`; ReplenishVerifier repair prompts intentionally use replenishment-specific feedback. Added minimal second-round repair generator so real repair can be evaluated separately. |
| 7. Synthetic candidates make Direct too bad/unfair. | Risk remains for smoke tests; documented. | Demo candidates start with syntax/error and weak candidates, so they are good for pipeline stress testing but not fair main-paper evidence. Main claims must use real LLM candidates with natural ordering/decoding. |
| 8. Case study only synthetic; may not hold on real LLM outputs. | Risk documented. | `extract_case_studies.py` can run on real LLM experiments; docs recommend main-paper case studies from real LLM candidates and synthetic only in appendix/smoke. |
| 9. LP parser/structure rules over-rely on variable names. | Partially fixed. | Added lightweight role aliases in `structure_rules.py` for descriptive variable names (`order_qty`, `ending_inventory`, `setup`, `backlog`, etc.) and constraint hints (`flow`, `balance`, `link`, `capacity`). This is still a prototype and not full coefficient/index verification. |
| 10. README/paper overclaim. | Reduced. | The paper/README should describe baselines as `*-like`, not full reproductions, and state ReplenishVerifier is complementary to OptiMUS/SIRL/OR-R1/StepORLM/OptArgus/OptiRepair. |

## Code changes made

- Added `OR-R1-like Voting` baseline:
  - `code_output_format_valid()`
  - `compute_objective_consensus_scores()`
  - `or_r1_like_voting_score()`
  - experiment method plumbing and audit inclusion.
- Added optional `--use_objective_consensus` for ReplenishVerifier-Full:
  - disabled by default;
  - blends candidate objective consensus only when explicitly enabled;
  - does not use reference objective.
- Added LP-structure role aliases:
  - keeps `Q/I/B/Y` support;
  - adds descriptive-name fallback for common LLM outputs.
- Added minimal repair generation path:
  - `build_repair_prompt()` / `build_repair_chat_messages()`;
  - `python -m replenishverifier.llm.run_repair_generation`.
- Added tests for OR-R1-like consensus and descriptive variable-name detection.

## Remaining limitations / honest claims

1. `OR-R1-like Voting`, `SIRL-like LP-Stats`, `OptArgus-like Audit`, and `OptiRepair-like Repair-Prompt` are lightweight analogues, not faithful reproductions.
2. `ReplenishVerifier-Repair` is still prompt-generation unless repaired candidates are generated and evaluated with `run_repair_generation.py`.
3. Structure detection is more robust than before but still heuristic. It does not validate exact coefficients, indexing, or boundary conditions.
4. Synthetic demo candidates are smoke tests only. Real LLM candidates are required for main-table claims.
5. Objective consensus is useful as a generic test-time baseline/optional signal, but it can converge on a shared wrong objective. It should not replace structure verification.

## Pre-experiment protocol additions

- Prompt leakage risk is controlled by making `hidden_verifier` and `plain` hide `expected_structures`; `structured` is guided/appendix-only because it exposes expected structures.
- Generic repair is a fair control only when it excludes replenishment-specific missing labels, avoids falling back to structure-aware feedback, and uses generic execution/solver/audit feedback.
- Runtime overhead must be reported from real evaluated candidates using the runtime analyzer; missing values are `NA`, not estimated.
- Naming robustness is currently a lightweight text-level perturbation, not an AST-safe transformation.
- Preference data is a future learning signal and cannot be described as DPO/PRM/LoRA improvement until training and evaluation are actually run.
- Formal selection and preference construction do not use `reference_objective`; `reference_objective` remains evaluation-only.

## Formal selection leakage conclusion

The formal selection code is designed not to use `reference_objective`. `reference_objective` is passed into `compute_score()` only to populate evaluation metrics (`objective_score`, `objective_correct`, `relative_error`) after selection. Selection policies and the leakage audit explicitly mark no-reference selection.
