# Pre-Experiment Enhancement Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not use subagent-driven development because the user explicitly requested no multi-agent work.

**Goal:** Verify and patch ReplenishVerifier's pre-experiment code/documentation enhancements for prompt leakage control, fair repair prompts, runtime overhead analysis, naming robustness, no-reference preference metadata, and synchronized README/docs/papers.

**Architecture:** Use a verification-and-gap-filling pass over the existing repository rather than rewriting features that already exist. Keep all candidate selection and preference construction no-reference; `reference_objective` remains evaluation-only. Add or adjust tests before code changes when a real gap is found, then run targeted tests and the full suite.

**Tech Stack:** Python 3.10+, pytest, JSONL experiment artifacts, PuLP candidate execution, existing `replenishverifier` modules.

## Global Constraints

- Communicate with the user in Chinese.
- Do not use Explore subagents or any multi-agent orchestration.
- Do not create a git worktree.
- Do not run real LLM generation.
- Do not run large-scale benchmarks.
- Do not fill any `[TO FILL]` result numbers.
- Do not claim SFT, TGRPO, DPO, RL, PRM, or LoRA training has been completed.
- Formal candidate selection must not use `reference_objective`.
- `reference_objective` may be used only for final evaluation metrics.
- Follow project planning-with-files: read and update `task_plan.md`, `findings.md`, and `progress.md` for phase completion or key facts.

---

### Task 1: Verify Current Implementation Surface

**Files:**
- Read: `replenishverifier/llm/prompt_builder.py`
- Read: `replenishverifier/llm/run_generation.py`
- Read: `replenishverifier/llm/run_repair_generation.py`
- Read: `replenishverifier/experiments/run_all_methods.py`
- Read: `replenishverifier/experiments/methods.py`
- Read: `replenishverifier/experiments/analyze_runtime_overhead.py`
- Read: `replenishverifier/experiments/rename_variables_for_robustness.py`
- Read: `replenishverifier/experiments/build_preference_data.py`
- Read: relevant tests under `tests/`

**Interfaces:**
- Consumes: existing CLI/function names.
- Produces: a gap list for Tasks 2-7.

- [ ] **Step 1: Confirm prompt modes exist**

Check that `PROMPT_TYPES = {"structured", "plain", "hidden_verifier"}` exists, that `run_generation.py` exposes `--prompt_type`, and that default is `hidden_verifier`.

- [ ] **Step 2: Confirm repair prompt split exists**

Check that `run_all_methods.py` writes `repair_prompts.jsonl` and `generic_repair_prompts.jsonl`, and that `methods.py` has `build_structure_aware_repair_prompts()` and `build_generic_repair_prompts()`.

- [ ] **Step 3: Confirm runtime fields and analyzer exist**

Check that candidate evaluations include `code_execution_time`, `solver_lp_export_time`, `solver_time`, `lp_parse_time`, `structure_check_time`, and `total_candidate_evaluation_time`, and that analyzer writes JSONL/CSV/MD.

- [ ] **Step 4: Confirm renaming and preference utilities exist**

Check that `rename_variables_for_robustness.py` supports `--mode random` and `--mode descriptive_to_anonymous`, and that preference pairs include no-reference metadata.

### Task 2: Patch Prompt Leakage Gaps If Found

**Files:**
- Modify if needed: `replenishverifier/llm/prompt_builder.py`
- Modify if needed: `replenishverifier/llm/run_generation.py`
- Test: `tests/test_prompt_modes.py`

**Interfaces:**
- Consumes: `build_prompt(sample: dict, prompt_type: str) -> str`, `build_chat_messages(sample: dict, prompt_type: str) -> list[dict]`, `render_prompt(tokenizer, sample, use_chat_template=True, prompt_type="hidden_verifier") -> str`.
- Produces: prompt modes with no expected-structure leakage for `plain` and `hidden_verifier`.

- [ ] **Step 1: Add or adjust failing tests for any leakage gap**

If `plain` or `hidden_verifier` contains required structure labels from `expected_structures`, add assertions to `tests/test_prompt_modes.py` that fail on those labels.

- [ ] **Step 2: Patch prompt builder only if tests expose a gap**

Ensure `structured` is the only prompt mode that serializes `expected_structures`; ensure default CLI prompt type is `hidden_verifier`.

- [ ] **Step 3: Run prompt tests**

Run: `python -m pytest tests/test_prompt_modes.py -q`
Expected: all prompt-mode tests pass.

### Task 3: Patch Repair Prompt Fairness Gaps If Found

**Files:**
- Modify if needed: `replenishverifier/experiments/methods.py`
- Modify if needed: `replenishverifier/llm/prompt_builder.py`
- Modify if needed: `replenishverifier/llm/run_repair_generation.py`
- Test: `tests/test_repair_prompt_fairness.py`
- Test: `tests/test_repair_generation_dry_run.py`

**Interfaces:**
- Consumes: `build_structure_aware_repair_prompts(rows) -> list[dict]`, `build_generic_repair_prompts(rows) -> list[dict]`, `build_generic_repair_prompt(sample, repair_row, original_code="") -> str`.
- Produces: structure-aware prompts that may include replenishment labels, and generic prompts that do not include missing replenishment structure labels.

- [ ] **Step 1: Add or adjust failing tests for generic leakage**

If the generic LLM repair prompt can leak domain labels via `problem_type`, `feedback`, or `repair_prompt`, add a test using problem type `fixed_order_cost_big_m` and feedback containing `inventory_balance`/`big_m_constraint` to ensure generic repair output excludes those labels.

- [ ] **Step 2: Patch generic prompt construction**

Make generic repair prompt construction prefer `generic_repair_feedback`, avoid fallback to structure-aware `feedback` or `repair_prompt`, and avoid printing raw `problem_type` if it contains replenishment-specific labels.

- [ ] **Step 3: Run repair tests**

Run: `python -m pytest tests/test_repair_prompt_fairness.py tests/test_repair_generation_dry_run.py -q`
Expected: all repair prompt tests pass.

### Task 4: Verify Runtime Overhead Analyzer

**Files:**
- Modify if needed: `replenishverifier/experiments/analyze_runtime_overhead.py`
- Test: `tests/test_runtime_overhead.py`

**Interfaces:**
- Consumes: `candidate_evaluations.jsonl` in an experiment directory.
- Produces: `runtime_overhead.jsonl`, `runtime_overhead.csv`, `runtime_overhead.md`.

- [ ] **Step 1: Confirm missing fields do not crash analyzer**

Run: `python -m pytest tests/test_runtime_overhead.py -q`
Expected: tests pass and markdown reports `NA` for unavailable fields.

- [ ] **Step 2: Patch analyzer only if it crashes or fabricates values**

Keep missing values as `None` in JSONL/CSV and `NA` in Markdown.

### Task 5: Verify Renaming Robustness Utility

**Files:**
- Modify if needed: `replenishverifier/experiments/rename_variables_for_robustness.py`
- Test: `tests/test_renaming_robustness.py`

**Interfaces:**
- Consumes: candidate JSONL with `generated_code`.
- Produces: renamed candidate JSONL with changed `generated_code` and unchanged evaluation labels/reference fields.

- [ ] **Step 1: Run renaming tests**

Run: `python -m pytest tests/test_renaming_robustness.py -q`
Expected: tests pass for `random` and `descriptive_to_anonymous` behavior.

- [ ] **Step 2: Patch only if output code is unchanged or protected fields mutate**

Ensure `reference_objective` and evaluation labels are copied unchanged while `generated_code` changes when matching names exist.

### Task 6: Verify Preference Metadata and No-Reference Construction

**Files:**
- Modify if needed: `replenishverifier/experiments/build_preference_data.py`
- Test: `tests/test_preference_metadata.py`
- Test: `tests/test_strong_baselines.py`

**Interfaces:**
- Consumes: `build_preference_pairs(exp_dir, out_path, min_score_gap=0.10, max_pairs_per_problem=3) -> list[dict]`.
- Produces: chosen/rejected pairs with missing structures, statuses, certificate summaries, source/version metadata, problem metadata, prompt type, candidate IDs, and `uses_reference_objective_for_preference=False`.

- [ ] **Step 1: Run preference tests**

Run: `python -m pytest tests/test_preference_metadata.py tests/test_strong_baselines.py -q`
Expected: preference construction ignores changed `reference_objective` values and leakage audit tests pass.

- [ ] **Step 2: Patch only if preference scores depend on reference objective**

Keep `_preference_score()` based on executable status, optimality, structure score, and feedback count only.

### Task 7: Verify Documentation and Paper Synchronization

**Files:**
- Modify if needed: `README.md`
- Modify if needed: `docs/experiment_operation_guide.md`
- Modify if needed: `docs/real_llm_experiment_checklist.md`
- Modify if needed: `docs/code_and_claim_risk_audit.md`
- Modify if needed: `docs/ccfa_revision_roadmap.md`
- Modify if needed: `docs/submit_readiness_checklist.md`
- Modify if needed: `papers/replenishverifier_draft_zh.md`
- Modify if needed: `papers/replenishverifier_draft_en.md`

**Interfaces:**
- Consumes: current code/CLI reality.
- Produces: docs that explain prompt type, structured prompt leakage risk, fair repair comparison, runtime overhead, lightweight renaming perturbation, future-only preference learning, no-reference selection, and LP-artifact-grounded replenishment structure supervision.

- [ ] **Step 1: Search target docs for required terms**

Use content search for `prompt_type`, `generic_repair_prompts`, `runtime_overhead`, `rename_variables_for_robustness`, `uses_reference_objective_for_preference`, and `[TO FILL AFTER REAL LLM EXPERIMENT]`.

- [ ] **Step 2: Patch missing explanations only**

Add concise sections or bullets where a target file lacks the required explanation. Do not add result numbers.

### Task 8: Update Planning Files and Run Full Test Suite

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

**Interfaces:**
- Consumes: final changed-file list and test results.
- Produces: durable planning notes for future sessions.

- [ ] **Step 1: Run full tests**

Run: `python -m pytest`
Expected: all tests pass, or failures are reported faithfully with attempted fixes.

- [ ] **Step 2: Update planning files**

Append this session's final facts: what was verified, what was patched, test command/result, and remaining TODOs.

- [ ] **Step 3: Final report in Chinese**

Report modified files, CLI parameters, outputs, tests, test results, TODOs, and how changes answer SIRL / OR-R1 / Step-Opt / OptMATH / OptiMUS / OptiRepair / OptArgus review concerns.

## Self-Review

- Spec coverage: Each user requirement maps to one of Tasks 1-8.
- Placeholder scan: No `TBD` or unspecified implementation steps are used; patch steps are conditional because current repository already contains many requested features.
- Type consistency: Function and file names match the inspected repository surface.
