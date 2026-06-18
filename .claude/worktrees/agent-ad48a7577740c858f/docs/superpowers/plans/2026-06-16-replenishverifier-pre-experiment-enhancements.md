# ReplenishVerifier Pre-Experiment Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pre-experiment safeguards and metadata for prompt leakage control, fair repair baselines, runtime overhead analysis, naming robustness, preference data provenance, and synchronized paper/docs claims.

**Architecture:** Use a lightweight unified schema refactor: keep existing module boundaries and CLIs, add consistent prompt/repair/runtime/preference metadata fields, and preserve backward-compatible aliases. Candidate selection and preference construction remain no-reference; `reference_objective` stays evaluation-only.

**Tech Stack:** Python 3.10+, PuLP, pytest, repository-local JSONL utilities in `replenishverifier.utils.io`, existing Markdown documentation.

---

## Global Constraints for Implementation

- Do not use Explore subagents.
- Do not create a git worktree.
- Do not run real LLM generation.
- Do not run large benchmark experiments.
- Do not fill any paper or doc result number.
- Do not claim SFT, DPO, PRM, RL, LoRA, TGRPO, or repair training was completed.
- Do not use `reference_objective` for formal selection or preference construction.
- Do not commit unless the user explicitly asks; use verification checkpoints instead of commit steps.

## File Structure

### Files to modify

- `replenishverifier/llm/prompt_builder.py`
  - Owns prompt mode rendering and repair prompt text.
  - Add `PROMPT_TYPES`, `build_prompt(..., prompt_type=...)`, generic naming guidance, and fair generic repair prompt behavior.

- `replenishverifier/llm/run_generation.py`
  - Owns candidate-generation CLI.
  - Add `--prompt_type`, `--seed`, prompt-mode routing, seed setup, and generation metadata.

- `replenishverifier/llm/run_repair_generation.py`
  - Owns second-round repair generation CLI.
  - Preserve `--repair_type`; ensure it can consume either structure-aware or generic prompt rows and preserve prompt metadata.

- `replenishverifier/solver/code_executor.py`
  - Owns subprocess execution and LP export.
  - Add parent execution timing and runner-side LP export / solve timing.

- `replenishverifier/experiments/methods.py`
  - Owns candidate evaluation, method selection, and repair prompt row creation.
  - Add unified runtime fields and split repair prompt builders.

- `replenishverifier/experiments/run_all_methods.py`
  - Owns experiment output bundle.
  - Write both structure-aware and generic repair prompt files and update manifest.

- `replenishverifier/experiments/rename_variables_for_robustness.py`
  - Owns naming perturbation CLI.
  - Add `descriptive_to_anonymous` mode and explicit text-level warning metadata.

- `replenishverifier/experiments/build_preference_data.py`
  - Owns future preference-pair export.
  - Add rich no-reference metadata and certificate summaries.

- `README.md`
- `docs/experiment_operation_guide.md`
- `docs/real_llm_experiment_checklist.md`
- `docs/code_and_claim_risk_audit.md`
- `docs/ccfa_revision_roadmap.md`
- `docs/submit_readiness_checklist.md`
- `papers/replenishverifier_draft_zh.md`
- `papers/replenishverifier_draft_en.md`
  - Synchronize protocol and claim boundaries.

- `progress.md`
  - Record completed implementation and verification at the end.

### Files to create

- `replenishverifier/experiments/analyze_runtime_overhead.py`
  - Runtime overhead CLI.

- `tests/test_prompt_modes.py`
  - Prompt mode leakage and metadata tests.

- `tests/test_repair_prompt_fairness.py`
  - Generic vs structure-aware repair prompt schema/fairness tests.

- `tests/test_runtime_overhead.py`
  - Runtime analyzer and missing-field handling tests.

- `tests/test_renaming_robustness.py`
  - Renaming CLI/function tests.

- `tests/test_preference_metadata.py`
  - Preference metadata and no-reference construction tests.

---

## Task 1: Prompt Modes and Generation Metadata

**Files:**
- Modify: `replenishverifier/llm/prompt_builder.py`
- Modify: `replenishverifier/llm/run_generation.py`
- Create: `tests/test_prompt_modes.py`
- Update if needed: `tests/test_repair_generation_dry_run.py`

- [ ] **Step 1: Write failing prompt-mode tests**

Create `tests/test_prompt_modes.py` with these tests:

```python
from replenishverifier.llm.prompt_builder import build_chat_messages, build_prompt
from replenishverifier.llm.run_generation import render_prompt


class DummyTokenizer:
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        assert tokenize is False
        assert add_generation_prompt is True
        return "\n".join(message["content"] for message in messages)


def _sample():
    return {
        "id": "p0",
        "problem_type": "fixed_order_cost_big_m",
        "difficulty": "hard",
        "natural_language": "Plan replenishment with setup decisions.",
        "parameters": {"periods": 2, "demand": [3, 4]},
        "expected_structures": {"inventory_balance": True, "big_m_constraint": True, "fixed_order_cost": True},
    }


def test_structured_prompt_exposes_expected_structures_for_guided_ablation():
    prompt = build_prompt(_sample(), prompt_type="structured")
    assert "Expected high-level modeling structures as JSON" in prompt
    assert "inventory_balance" in prompt
    assert "big_m_constraint" in prompt
    assert "fixed_order_cost" in prompt


def test_plain_prompt_hides_expected_structures_and_specific_structure_labels():
    prompt = build_prompt(_sample(), prompt_type="plain")
    assert "Expected high-level modeling structures" not in prompt
    assert "inventory_balance" not in prompt
    assert "big_m_constraint" not in prompt
    assert "fixed_order_cost" not in prompt
    assert "Parameters as JSON" in prompt
    assert "Plan replenishment with setup decisions." in prompt


def test_hidden_verifier_prompt_hides_expected_structures_but_keeps_io_contract():
    prompt = build_prompt(_sample(), prompt_type="hidden_verifier")
    assert "Expected high-level modeling structures" not in prompt
    assert "inventory_balance" not in prompt
    assert "big_m_constraint" not in prompt
    assert "fixed_order_cost" not in prompt
    assert "OUTPUT_LP_PATH" in prompt
    assert "build_model()" in prompt
    assert "explicitly name every PuLP constraint" in prompt


def test_build_chat_messages_passes_prompt_type():
    messages = build_chat_messages(_sample(), prompt_type="plain")
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Expected high-level modeling structures" not in messages[1]["content"]


def test_render_prompt_uses_prompt_type_with_chat_template():
    rendered = render_prompt(DummyTokenizer(), _sample(), use_chat_template=True, prompt_type="hidden_verifier")
    assert "OUTPUT_LP_PATH" in rendered
    assert "Expected high-level modeling structures" not in rendered
    assert "big_m_constraint" not in rendered


def test_unknown_prompt_type_raises_value_error():
    try:
        build_prompt(_sample(), prompt_type="unknown")
    except ValueError as exc:
        assert "prompt_type" in str(exc)
    else:
        raise AssertionError("build_prompt should reject unknown prompt_type")
```

- [ ] **Step 2: Run prompt-mode tests and verify failure**

Run:

```bash
python -m pytest tests/test_prompt_modes.py -q
```

Expected before implementation: failures mentioning unexpected keyword argument `prompt_type` or missing `render_prompt` support.

- [ ] **Step 3: Implement prompt modes in `prompt_builder.py`**

Edit `replenishverifier/llm/prompt_builder.py` to add these top-level constants and helper functions near the current prompt constants:

```python
PROMPT_TYPES = {"structured", "plain", "hidden_verifier"}

GENERIC_CONSTRAINT_NAMING_GUIDANCE = """Modeling clarity guidance:
- Give decision variables meaningful names that reflect their optimization role.
- Explicitly name every PuLP constraint with a short descriptive string.
- Do NOT rely on anonymous PuLP constraints such as _C1/_C2.
- Do not include explanations outside the requested Python code block.
"""

PULP_INTERFACE_REQUIREMENTS = """Hard requirements:
1. Use PuLP for modeling and solving.
2. The code must contain:
   - import pulp
   - import os
   - prob = pulp.LpProblem(...)
   - prob.solve(pulp.PULP_CBC_CMD(msg=False))
   - print("STATUS:", pulp.LpStatus[prob.status])
   - print("OBJECTIVE:", pulp.value(prob.objective))
   - if environment variable OUTPUT_LP_PATH exists, run prob.writeLP(os.environ["OUTPUT_LP_PATH"])
3. Define a function build_model() that returns the PuLP LpProblem object named prob.
4. In the main block, call build_model(), optionally write the LP using OUTPUT_LP_PATH, solve, and print STATUS and OBJECTIVE.
5. Only output one complete Python code block. Do not output explanations or multiple code blocks.
"""
```

Replace `build_prompt(sample)` with this signature and branch behavior:

```python
def _validate_prompt_type(prompt_type):
    if prompt_type not in PROMPT_TYPES:
        raise ValueError(f"prompt_type must be one of {sorted(PROMPT_TYPES)}, got {prompt_type!r}")


def _common_problem_header(sample):
    return f"""Problem ID: {sample.get('id')}
Problem type: {sample.get('problem_type')}
Difficulty: {sample.get('difficulty')}

Natural language problem:
{sample.get('natural_language')}
"""


def _parameters_block(sample):
    params = json.dumps(sample.get("parameters", {}), ensure_ascii=False, indent=2)
    return f"""Parameters as JSON:
{params}
"""


def build_prompt(sample, prompt_type="hidden_verifier"):
    _validate_prompt_type(prompt_type)
    header = _common_problem_header(sample)
    params = _parameters_block(sample)

    if prompt_type == "structured":
        expected = json.dumps(sample.get("expected_structures", {}), ensure_ascii=False, indent=2)
        return f'''Given the following inventory replenishment optimization problem, write one complete Python program using PuLP.

{header}
{params}
Expected high-level modeling structures as JSON:
{expected}

{CONSTRAINT_NAMING_REGULATION}
{PULP_INTERFACE_REQUIREMENTS}'''

    if prompt_type == "plain":
        return f'''Given the following inventory replenishment optimization problem, write one complete Python program using PuLP.

{header}
{params}
{PULP_INTERFACE_REQUIREMENTS}'''

    return f'''Given the following inventory replenishment optimization problem, write one complete Python program using PuLP.

{header}
{params}
{GENERIC_CONSTRAINT_NAMING_GUIDANCE}
{PULP_INTERFACE_REQUIREMENTS}'''
```

Update `build_chat_messages`:

```python
def build_chat_messages(sample, prompt_type="hidden_verifier"):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(sample, prompt_type=prompt_type)},
    ]
```

- [ ] **Step 4: Implement generation CLI metadata in `run_generation.py`**

Update imports:

```python
import random
```

Update `render_prompt` signature and calls:

```python
def render_prompt(tokenizer, sample, use_chat_template=True, prompt_type="hidden_verifier"):
    messages = build_chat_messages(sample, prompt_type=prompt_type)
    if use_chat_template and hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            LOGGER.warning("Tokenizer chat template failed; falling back to plain prompt.")
    return build_prompt(sample, prompt_type=prompt_type)
```

Add seed helper:

```python
def set_generation_seed(seed):
    if seed is None:
        return
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass
```

Update `run_generation(...)` signature with `prompt_type="hidden_verifier", seed=None`, call `set_generation_seed(seed)` before loading model, and render prompts with `prompt_type=prompt_type`.

When building each candidate row, add:

```python
"prompt_type": prompt_type,
"generation_config": {
    "prompt_type": prompt_type,
    "seed": seed,
    "max_new_tokens": max_new_tokens,
    "temperature": temperature,
    "top_p": top_p,
    "use_chat_template": use_chat_template,
    "trust_remote_code": trust_remote_code,
},
"seed": seed,
"reproducibility_note": (
    "Seed improves reproducibility, but exact determinism is not guaranteed across GPU sampling, "
    "Transformers versions, CUDA kernels, hardware, and model backends."
),
```

Update `main()` parser:

```python
parser.add_argument("--prompt_type", choices=["hidden_verifier", "plain", "structured"], default="hidden_verifier")
parser.add_argument("--seed", type=int, default=None)
```

Pass both into `run_generation(...)`.

- [ ] **Step 5: Run prompt-mode tests and existing repair dry-run tests**

Run:

```bash
python -m pytest tests/test_prompt_modes.py tests/test_repair_generation_dry_run.py -q
```

Expected: all selected tests pass.

---

## Task 2: Fair Generic and Structure-Aware Repair Prompt Rows

**Files:**
- Modify: `replenishverifier/llm/prompt_builder.py`
- Modify: `replenishverifier/experiments/methods.py`
- Modify: `replenishverifier/experiments/run_all_methods.py`
- Modify: `replenishverifier/llm/run_repair_generation.py`
- Create: `tests/test_repair_prompt_fairness.py`
- Update: `tests/test_repair_generation_dry_run.py`

- [ ] **Step 1: Write failing repair fairness tests**

Create `tests/test_repair_prompt_fairness.py`:

```python
from replenishverifier.experiments.methods import (
    build_generic_repair_prompts,
    build_structure_aware_repair_prompts,
)
from replenishverifier.llm.prompt_builder import build_generic_repair_prompt, build_repair_prompt


DOMAIN_LABELS = [
    "inventory_balance",
    "capacity_constraint",
    "shortage_variable",
    "binary_order_variable",
    "big_m_constraint",
    "fixed_order_cost",
    "Big-M",
]


def _evaluated_row():
    return {
        "problem_id": "p0",
        "candidate_id": "c0",
        "candidate_method": "llm_generation",
        "generated_text": "text",
        "generated_code": "import pulp\n# candidate code\n",
        "prompt_type": "hidden_verifier",
        "execution": {"executable": True, "status": "Optimal", "objective": 1.0, "lp_path": "c0.lp"},
        "generic_repair_feedback": "- Add constraints that define the feasible region.",
        "feedback": "Missing or weak inventory balance constraints.",
        "structure_verification": {
            "missing": ["inventory_balance", "big_m_constraint"],
            "low_score_required": [
                {"rule_name": "inventory_balance", "score": 0.4, "repair_hint": "Add inventory-flow constraints."},
                {"rule_name": "big_m_constraint", "score": 0.0, "repair_hint": "Add linking constraints."},
            ],
            "certificates": [
                {"rule_name": "inventory_balance", "required": True, "passed": False, "score": 0.4, "evidence_strength": "name_only"},
                {"rule_name": "big_m_constraint", "required": True, "passed": False, "score": 0.0, "evidence_strength": "none"},
            ],
        },
    }


def test_structure_aware_repair_prompt_contains_missing_structure_feedback():
    rows = build_structure_aware_repair_prompts([_evaluated_row()])
    assert len(rows) == 1
    row = rows[0]
    assert row["repair_type"] == "structure_aware"
    assert row["missing_structures"] == ["inventory_balance", "big_m_constraint"]
    assert "inventory_balance" in row["repair_prompt"]
    assert "big_m_constraint" in row["repair_prompt"]
    assert row["original_candidate_code"].startswith("import pulp")
    assert row["uses_reference_objective_for_repair"] is False


def test_generic_repair_prompt_hides_replenishment_specific_missing_labels():
    rows = build_generic_repair_prompts([_evaluated_row()])
    assert len(rows) == 1
    row = rows[0]
    assert row["repair_type"] == "generic"
    assert row["missing_structures"] == []
    assert row["original_candidate_code"].startswith("import pulp")
    text = row["repair_prompt"] + "\n" + row["feedback"]
    for label in DOMAIN_LABELS:
        assert label not in text
    assert "generic" in row["feedback"].lower() or "constraints" in row["feedback"].lower()
    assert row["uses_reference_objective_for_repair"] is False


def test_repair_prompt_row_schemas_are_compatible():
    structure_row = build_structure_aware_repair_prompts([_evaluated_row()])[0]
    generic_row = build_generic_repair_prompts([_evaluated_row()])[0]
    assert set(structure_row.keys()) == set(generic_row.keys())
    for key in ["problem_id", "candidate_id", "candidate_method", "execution", "original_candidate_text", "original_candidate_code", "prompt_type"]:
        assert structure_row[key] == generic_row[key]


def test_prompt_builder_generic_repair_prompt_does_not_leak_domain_labels():
    sample = {"id": "p0", "natural_language": "Minimize total cost.", "parameters": {}}
    repair_row = {
        "generic_repair_feedback": "- Add a clear objective and constraints.",
        "feedback": "Missing inventory_balance",
        "repair_prompt": "Missing big_m_constraint",
    }
    prompt = build_generic_repair_prompt(sample, repair_row, original_code="import pulp\n")
    for label in DOMAIN_LABELS:
        assert label not in prompt
    assert "Generic feedback" in prompt


def test_prompt_builder_structure_aware_repair_prompt_can_use_domain_feedback():
    sample = {"id": "p0", "natural_language": "Minimize total cost.", "parameters": {}}
    prompt = build_repair_prompt(sample, {"feedback": "Missing inventory_balance and big_m_constraint."}, original_code="import pulp\n")
    assert "inventory_balance" in prompt
    assert "big_m_constraint" in prompt
```

- [ ] **Step 2: Run repair fairness tests and verify failure**

Run:

```bash
python -m pytest tests/test_repair_prompt_fairness.py -q
```

Expected before implementation: import errors for new functions and/or failures because generic prompts leak domain labels.

- [ ] **Step 3: Fix generic repair prompt text in `prompt_builder.py`**

Add a generic repair naming block:

```python
GENERIC_REPAIR_NAMING_GUIDANCE = """Generic modeling clarity guidance:
- Use meaningful decision-variable names, but do not rely on task-specific verifier labels.
- Explicitly name every PuLP constraint with a short descriptive string.
- Do NOT write anonymous constraints such as prob += expression without a name.
"""
```

Update `build_generic_repair_prompt` so feedback never falls back to structure-aware feedback:

```python
def build_generic_repair_prompt(sample, repair_row, original_code=""):
    params = json.dumps(sample.get("parameters", {}), ensure_ascii=False, indent=2)
    feedback = repair_row.get("generic_repair_feedback") or repair_row.get("feedback") or "- Inspect generic execution, objective, variable, constraint, and solver issues."
    return f'''You are repairing Python PuLP code for an optimization problem using only generic execution, solver, and LP-artifact feedback.
Do not use task-specific verifier labels or missing-structure names.

Problem ID: {sample.get('id')}
Problem type: {sample.get('problem_type')}
Difficulty: {sample.get('difficulty')}

Natural language problem:
{sample.get('natural_language')}

Parameters as JSON:
{params}

Original candidate code:
```python
{original_code or repair_row.get('generated_code', '') or repair_row.get('original_candidate_code', '')}
```

Generic feedback:
{feedback}

{GENERIC_REPAIR_NAMING_GUIDANCE}
Hard requirements:
1. Return one complete corrected Python program using PuLP.
2. Preserve build_model(), optional OUTPUT_LP_PATH writeLP, solver call, STATUS and OBJECTIVE prints.
3. Focus on generic modeling/code validity: objective, variables, constraints, bounds, solver execution, and meaningful names.
4. Output only one Python code block.
'''
```

Keep `build_repair_prompt` structure-aware and allowed to use `CONSTRAINT_NAMING_REGULATION`.

- [ ] **Step 4: Implement split repair prompt builders in `methods.py`**

Add helper functions before the old `build_repair_prompts`:

```python
def _certificate_summary(certificates):
    return [
        {
            "rule_name": cert.get("rule_name"),
            "required": cert.get("required"),
            "passed": cert.get("passed"),
            "score": cert.get("score"),
            "evidence_strength": cert.get("evidence_strength"),
        }
        for cert in (certificates or [])
    ]


def _evidence_strength_by_rule(certificates):
    return {cert.get("rule_name"): cert.get("evidence_strength") for cert in (certificates or []) if cert.get("rule_name")}


def _base_repair_prompt_row(row, repair_type, missing_structures, feedback, repair_prompt):
    structure = row.get("structure_verification") or {}
    certificates = structure.get("certificates", [])
    return {
        "problem_id": row["problem_id"],
        "candidate_id": row["candidate_id"],
        "method_name": row.get("method_name", "candidate"),
        "candidate_method": row.get("candidate_method"),
        "repair_type": repair_type,
        "repair_feedback_count": len(missing_structures),
        "missing_structures": list(missing_structures),
        "low_score_required": structure.get("low_score_required", []) if repair_type == "structure_aware" else [],
        "structure_certificates": _certificate_summary(certificates) if repair_type == "structure_aware" else [],
        "evidence_strength_by_rule": _evidence_strength_by_rule(certificates) if repair_type == "structure_aware" else {},
        "execution": row.get("execution") or {},
        "generic_repair_feedback": row.get("generic_repair_feedback", ""),
        "feedback": feedback,
        "repair_prompt": repair_prompt,
        "original_candidate_text": row.get("generated_text", ""),
        "original_candidate_code": row.get("generated_code", ""),
        "prompt_type": row.get("prompt_type") or (row.get("generation_config") or {}).get("prompt_type"),
        "uses_reference_objective_for_repair": False,
    }
```

Add structure-aware builder:

```python
def build_structure_aware_repair_prompts(rows):
    prompts = []
    for row in rows:
        structure = row.get("structure_verification") or {}
        missing = structure.get("missing") or []
        if not missing:
            continue
        feedback = row.get("feedback", "")
        repair_prompt = (
            "You are fixing a PuLP optimization model for an inventory replenishment problem.\n"
            "Revise the generated code according to the replenishment structure feedback below.\n"
            "Keep variable names interpretable and explicitly name every PuLP constraint; do not rely on anonymous _C1/_C2 names.\n\n"
            f"Problem ID: {row.get('problem_id')}\n"
            f"Candidate ID: {row.get('candidate_id')}\n\n"
            f"Missing structures: {', '.join(missing)}\n\n"
            f"Feedback:\n{feedback}\n"
        )
        prompts.append(_base_repair_prompt_row(row, "structure_aware", missing, feedback, repair_prompt))
    return prompts
```

Add generic builder:

```python
def build_generic_repair_prompts(rows):
    prompts = []
    for row in rows:
        feedback = row.get("generic_repair_feedback", "")
        audit = row.get("optargus_audit") or {}
        execution = row.get("execution") or {}
        if not feedback and execution.get("executable") and not audit.get("generic_issue_count"):
            continue
        if not feedback:
            feedback = "- Inspect generic execution, objective, variables, constraints, bounds, and solver status."
        repair_prompt = (
            "You are fixing a PuLP optimization model using only generic execution, solver, and LP-artifact feedback.\n"
            "Do not use replenishment-specific missing-structure labels or verifier rule names.\n\n"
            f"Problem ID: {row.get('problem_id')}\n"
            f"Candidate ID: {row.get('candidate_id')}\n\n"
            f"Generic feedback:\n{feedback}\n"
        )
        prompts.append(_base_repair_prompt_row(row, "generic", [], feedback, repair_prompt))
    return prompts
```

Replace old `build_repair_prompts` body with:

```python
def build_repair_prompts(rows):
    """Backward-compatible alias for structure-aware repair prompts."""
    return build_structure_aware_repair_prompts(rows)
```

- [ ] **Step 5: Update `run_all_methods.py` to write both prompt bundles**

Update import:

```python
from replenishverifier.experiments.methods import (
    METHODS,
    build_generic_repair_prompts,
    build_repair_prompts,
    evaluate_all_candidates,
    select_for_method,
)
```

After writing `repair_prompts.*`, add:

```python
generic_repair_prompts = build_generic_repair_prompts(all_evaluated)
write_jsonl(out_dir / "generic_repair_prompts.jsonl", generic_repair_prompts)
save_summary_csv(out_dir / "generic_repair_prompts.csv", generic_repair_prompts)
save_markdown_table(out_dir / "generic_repair_prompts.md", generic_repair_prompts[:50], title="Generic Repair Prompts")
```

In `manifest["files"]`, add:

```python
"generic_repair_prompts": str(out_dir / "generic_repair_prompts.jsonl"),
```

- [ ] **Step 6: Preserve repair metadata in `run_repair_generation.py`**

When building `out` in `run_repair_generation`, add:

```python
"source_repair_type": repair_row.get("repair_type", repair_type),
"prompt_type": repair_row.get("prompt_type"),
"generation_config": {
    "repair_type": repair_type,
    "max_new_tokens": max_new_tokens,
    "temperature": temperature,
    "top_p": top_p,
    "use_chat_template": use_chat_template,
    "trust_remote_code": trust_remote_code,
},
```

- [ ] **Step 7: Run repair tests**

Run:

```bash
python -m pytest tests/test_repair_prompt_fairness.py tests/test_repair_generation_dry_run.py -q
```

Expected: all selected tests pass.

---

## Task 3: Runtime Timing and Overhead Analyzer

**Files:**
- Modify: `replenishverifier/solver/code_executor.py`
- Modify: `replenishverifier/experiments/methods.py`
- Create: `replenishverifier/experiments/analyze_runtime_overhead.py`
- Create: `tests/test_runtime_overhead.py`

- [ ] **Step 1: Write failing runtime analyzer tests**

Create `tests/test_runtime_overhead.py`:

```python
from pathlib import Path

from replenishverifier.experiments.analyze_runtime_overhead import analyze_runtime_overhead
from replenishverifier.experiments.methods import evaluate_candidate
from replenishverifier.utils.io import read_jsonl, write_jsonl


def test_runtime_overhead_analyzer_outputs_jsonl_csv_md_with_missing_fields(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [
        {
            "problem_id": "p0",
            "candidate_id": "c0",
            "total_candidate_evaluation_time": 1.2,
            "lp_parse_time": 0.2,
            "structure_check_time": 0.3,
        },
        {
            "problem_id": "p0",
            "candidate_id": "c1",
        },
    ])

    report = analyze_runtime_overhead(exp_dir)

    assert report["candidate_count"] == 2
    assert report["metrics"]["total_candidate_evaluation_time"]["mean"] == 1.2
    assert report["metrics"]["solver_time"]["mean"] is None
    assert (exp_dir / "runtime_overhead.jsonl").exists()
    assert (exp_dir / "runtime_overhead.csv").exists()
    assert (exp_dir / "runtime_overhead.md").exists()
    md = (exp_dir / "runtime_overhead.md").read_text(encoding="utf-8")
    assert "Candidate count" in md
    assert "NA" in md


def test_evaluate_candidate_records_runtime_fields(tmp_path):
    candidate = {
        "problem_id": "p0",
        "candidate_id": "c0",
        "method": "unit",
        "generated_code": """
import os
import pulp


def build_model():
    prob = pulp.LpProblem('unit', pulp.LpMinimize)
    x = pulp.LpVariable('x', lowBound=0)
    prob += x, 'objective'
    prob += x >= 1, 'minimum_x'
    return prob


if __name__ == '__main__':
    prob = build_model()
    if os.environ.get('OUTPUT_LP_PATH'):
        prob.writeLP(os.environ['OUTPUT_LP_PATH'])
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    print('STATUS:', pulp.LpStatus[prob.status])
    print('OBJECTIVE:', pulp.value(prob.objective))
""",
    }
    reference = {
        "problem_type": "single_period_newsvendor",
        "difficulty": "easy",
        "expected_structures": {},
        "reference_objective": 1.0,
        "reference_status": "Optimal",
    }

    row = evaluate_candidate(candidate, reference, work_dir=tmp_path, timeout=10)

    assert "runtime" in row
    assert row["code_execution_time"] is not None
    assert row["lp_parse_time"] is not None
    assert row["structure_check_time"] is not None
    assert row["total_candidate_evaluation_time"] is not None
    assert row["runtime_sec"] == row["total_candidate_evaluation_time"]
```

- [ ] **Step 2: Run runtime tests and verify failure**

Run:

```bash
python -m pytest tests/test_runtime_overhead.py -q
```

Expected before implementation: import error for `analyze_runtime_overhead` or missing runtime fields.

- [ ] **Step 3: Add runner timing to `code_executor.py`**

Add `import time` at top and inside `RUNNER_CODE` add `import time`.

In `RUNNER_CODE`, time LP export and solve:

```python
    export_start = time.perf_counter()
    model.writeLP(str(lp_path))
    solver_lp_export_time = time.perf_counter() - export_start

    solve_start = time.perf_counter()
    status_code = model.solve(pulp.PULP_CBC_CMD(msg=False))
    solver_time = time.perf_counter() - solve_start
```

Include fields in success JSON:

```python
        "solver_lp_export_time": float(solver_lp_export_time),
        "solver_time": float(solver_time),
```

Include `None` fields in exception JSON:

```python
        "solver_lp_export_time": None,
        "solver_time": None,
```

In parent `execute_generated_code`, start before `subprocess.run`:

```python
    start = time.perf_counter()
```

For timeout return include:

```python
"code_execution_time": float(time.perf_counter() - start),
"solver_lp_export_time": None,
"solver_time": None,
```

After parsing result, set:

```python
    result["code_execution_time"] = float(time.perf_counter() - start)
    result.setdefault("solver_lp_export_time", None)
    result.setdefault("solver_time", None)
```

Also include these fields in no-stdout and parse-error returns.

- [ ] **Step 4: Add runtime fields to `evaluate_candidate` in `methods.py`**

In `evaluate_candidate`, initialize:

```python
    lp_parse_time = None
    structure_check_time = None
```

When parsing LP:

```python
                parse_start = time.perf_counter()
                parsed = parse_lp_file(execution["lp_path"])
                lp_parse_time = time.perf_counter() - parse_start
                structure_start = time.perf_counter()
                structure_result = check_structures(parsed, reference["expected_structures"], problem_type=reference.get("problem_type"))
                structure_check_time = time.perf_counter() - structure_start
```

After total runtime:

```python
    total_runtime = time.perf_counter() - start
    runtime_fields = {
        "code_execution_time": execution.get("code_execution_time"),
        "solver_lp_export_time": execution.get("solver_lp_export_time"),
        "solver_time": execution.get("solver_time"),
        "lp_parse_time": None if lp_parse_time is None else float(lp_parse_time),
        "structure_check_time": None if structure_check_time is None else float(structure_check_time),
        "total_candidate_evaluation_time": float(total_runtime),
    }
```

Add to `base`:

```python
        "runtime": runtime_fields,
        "code_execution_time": runtime_fields["code_execution_time"],
        "solver_lp_export_time": runtime_fields["solver_lp_export_time"],
        "solver_time": runtime_fields["solver_time"],
        "lp_parse_time": runtime_fields["lp_parse_time"],
        "structure_check_time": runtime_fields["structure_check_time"],
        "total_candidate_evaluation_time": runtime_fields["total_candidate_evaluation_time"],
        "runtime_sec": runtime_fields["total_candidate_evaluation_time"],
```

Remove or replace the old `runtime_sec: float(runtime)` entry to avoid duplicate key confusion.

Update `_first_or_empty` with runtime fields set to `0.0` for total and `None` for unavailable subfields.

- [ ] **Step 5: Create runtime analyzer CLI**

Create `replenishverifier/experiments/analyze_runtime_overhead.py`:

```python
import argparse
import csv
import statistics
from pathlib import Path

from replenishverifier.utils.io import read_jsonl, write_jsonl

RUNTIME_FIELDS = [
    "code_execution_time",
    "solver_lp_export_time",
    "solver_time",
    "lp_parse_time",
    "structure_check_time",
    "total_candidate_evaluation_time",
]


def _coerce_number(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _field_value(row, field):
    if field in row:
        return _coerce_number(row.get(field))
    runtime = row.get("runtime") or {}
    return _coerce_number(runtime.get(field))


def _summary(values):
    present = [value for value in values if value is not None]
    missing = len(values) - len(present)
    if not present:
        return {"mean": None, "median": None, "count_present": 0, "count_missing": missing}
    return {
        "mean": float(sum(present) / len(present)),
        "median": float(statistics.median(present)),
        "count_present": len(present),
        "count_missing": missing,
    }


def _format(value):
    if value is None:
        return "NA"
    return f"{value:.6f}"


def _write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = ["problem_id", "candidate_id", *RUNTIME_FIELDS]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _write_markdown(path, report):
    lines = [
        "# Runtime Overhead Report",
        "",
        f"Candidate count: {report['candidate_count']}",
        "",
        "| Metric | Mean seconds | Median seconds | Present | Missing |",
        "|---|---:|---:|---:|---:|",
    ]
    labels = {
        "total_candidate_evaluation_time": "Total candidate evaluation time",
        "lp_parse_time": "LP parse time",
        "structure_check_time": "Structure check time",
        "code_execution_time": "Code execution time",
        "solver_lp_export_time": "Solver LP export time",
        "solver_time": "Solver time",
    }
    for field in ["total_candidate_evaluation_time", "lp_parse_time", "structure_check_time", "code_execution_time", "solver_lp_export_time", "solver_time"]:
        item = report["metrics"][field]
        lines.append(
            f"| {labels[field]} | {_format(item['mean'])} | {_format(item['median'])} | {item['count_present']} | {item['count_missing']} |"
        )
    lines.extend([
        "",
        "Missing or unavailable fields are reported as NA. No runtime values are inferred or fabricated.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_runtime_overhead(exp_dir):
    exp_dir = Path(exp_dir)
    rows = read_jsonl(exp_dir / "candidate_evaluations.jsonl")
    normalized = []
    for row in rows:
        out = {"problem_id": row.get("problem_id"), "candidate_id": row.get("candidate_id")}
        for field in RUNTIME_FIELDS:
            out[field] = _field_value(row, field)
        normalized.append(out)

    metrics = {field: _summary([row[field] for row in normalized]) for field in RUNTIME_FIELDS}
    report = {"exp_dir": str(exp_dir), "candidate_count": len(normalized), "metrics": metrics}

    write_jsonl(exp_dir / "runtime_overhead.jsonl", normalized)
    _write_csv(exp_dir / "runtime_overhead.csv", normalized)
    _write_markdown(exp_dir / "runtime_overhead.md", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Analyze runtime overhead from candidate_evaluations.jsonl.")
    parser.add_argument("--exp_dir", required=True)
    args = parser.parse_args()
    report = analyze_runtime_overhead(args.exp_dir)
    print(f"Wrote runtime overhead report for {report['candidate_count']} candidates to {args.exp_dir}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run runtime tests**

Run:

```bash
python -m pytest tests/test_runtime_overhead.py -q
```

Expected: all selected tests pass.

---

## Task 4: Variable Renaming Robustness Mode

**Files:**
- Modify: `replenishverifier/experiments/rename_variables_for_robustness.py`
- Create: `tests/test_renaming_robustness.py`

- [ ] **Step 1: Write failing renaming tests**

Create `tests/test_renaming_robustness.py`:

```python
from replenishverifier.experiments.rename_variables_for_robustness import rename_candidates, rename_code
from replenishverifier.utils.io import read_jsonl, write_jsonl


def test_descriptive_to_anonymous_changes_code_text():
    code = "order_qty = 1\nending_inventory = order_qty\nsetup_trigger = 0\n"
    renamed, mapping = rename_code(code, mode="descriptive_to_anonymous", seed=0)
    assert renamed != code
    assert "order_qty" not in renamed
    assert "ending_inventory" not in renamed
    assert mapping["order_qty"].startswith("x_")


def test_rename_candidates_preserves_reference_and_evaluation_labels(tmp_path):
    candidates = tmp_path / "candidates.jsonl"
    out = tmp_path / "renamed.jsonl"
    write_jsonl(candidates, [
        {
            "problem_id": "p0",
            "candidate_id": "c0",
            "method": "llm_generation",
            "generated_code": "order_qty = 1\nending_inventory = order_qty\n",
            "reference_objective": 123.0,
            "objective_correct": 1.0,
            "structure_verification": {"missing": ["inventory_balance"]},
        }
    ])

    rows = rename_candidates(candidates, out, mode="descriptive_to_anonymous", seed=0)
    saved = read_jsonl(out)

    assert rows[0]["generated_code"] != "order_qty = 1\nending_inventory = order_qty\n"
    assert saved[0]["reference_objective"] == 123.0
    assert saved[0]["objective_correct"] == 1.0
    assert saved[0]["structure_verification"] == {"missing": ["inventory_balance"]}
    assert saved[0]["source_candidate_id"] == "c0"
    assert saved[0]["renaming_mode"] == "descriptive_to_anonymous"
    assert "not AST-safe" in saved[0]["renaming_warning"]
```

- [ ] **Step 2: Run renaming tests and verify failure**

Run:

```bash
python -m pytest tests/test_renaming_robustness.py -q
```

Expected before implementation: ValueError for unsupported mode.

- [ ] **Step 3: Implement `descriptive_to_anonymous` mode**

In `rename_variables_for_robustness.py`, add:

```python
DESCRIPTIVE_TO_ANONYMOUS_MAP = {
    "order_qty": "x_order",
    "order_quantity": "x_order",
    "ending_inventory": "x_inventory",
    "inventory": "x_inventory",
    "stock": "x_inventory",
    "backlog_qty": "x_shortage",
    "shortage": "x_shortage",
    "setup_trigger": "x_binary",
    "order_flag": "x_binary",
}
```

Update `_replacement_map`:

```python
    if mode == "descriptive_to_anonymous":
        return dict(DESCRIPTIVE_TO_ANONYMOUS_MAP)
```

Update the error message:

```python
    raise ValueError("mode must be random, descriptive_to_anonymous, semantic, or adversarial")
```

Update `main()` choices:

```python
parser.add_argument("--mode", choices=["random", "descriptive_to_anonymous", "semantic", "adversarial"], default="random")
```

In `rename_candidates`, add warning metadata:

```python
        out["renaming_warning"] = "lightweight text-level perturbation; not AST-safe; manually inspect samples before formal experiments"
```

- [ ] **Step 4: Run renaming tests**

Run:

```bash
python -m pytest tests/test_renaming_robustness.py -q
```

Expected: all selected tests pass.

---

## Task 5: Preference Data Metadata and No-Reference Invariance

**Files:**
- Modify: `replenishverifier/experiments/build_preference_data.py`
- Create: `tests/test_preference_metadata.py`

- [ ] **Step 1: Write failing preference metadata tests**

Create `tests/test_preference_metadata.py`:

```python
from replenishverifier.experiments.audit_leakage import _audit_rows
from replenishverifier.experiments.build_preference_data import build_preference_pairs
from replenishverifier.utils.io import read_jsonl, write_jsonl


def _row(candidate_id, reference_objective, structure_score, missing, executable=True, status="Optimal"):
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "generated_code": f"# {candidate_id}",
        "generated_text": f"text {candidate_id}",
        "prompt_type": "hidden_verifier",
        "problem_type": "fixed_order_cost_big_m",
        "difficulty": "hard",
        "reference_objective": reference_objective,
        "execution": {"executable": executable, "status": status, "objective": 10.0},
        "structure_score": structure_score,
        "structure_verification": {
            "missing": missing,
            "certificates": [
                {"rule_name": "inventory_balance", "required": True, "passed": "inventory_balance" not in missing, "score": structure_score, "evidence_strength": "strong" if structure_score == 1.0 else "none"}
            ],
        },
    }


def test_preference_pairs_include_metadata_and_no_reference_flag(tmp_path):
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    write_jsonl(exp_dir / "candidate_evaluations.jsonl", [
        _row("good", reference_objective=999.0, structure_score=1.0, missing=[]),
        _row("bad", reference_objective=1.0, structure_score=0.0, missing=["inventory_balance"]),
    ])
    out = exp_dir / "preference_pairs.jsonl"

    pairs = build_preference_pairs(exp_dir, out, min_score_gap=0.01, max_pairs_per_problem=1)

    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["chosen_candidate_id"] == "good"
    assert pair["rejected_candidate_id"] == "bad"
    assert pair["uses_reference_objective_for_preference"] is False
    assert pair["preference_source"] == "replenishment_structure_verifier"
    assert pair["metadata"]["uses_reference_objective_for_preference"] is False
    assert pair["metadata"]["candidate_ids"] == {"chosen": "good", "rejected": "bad"}
    assert pair["chosen_missing_structures"] == []
    assert pair["rejected_missing_structures"] == ["inventory_balance"]
    assert pair["chosen_execution_status"] == "Optimal"
    assert pair["rejected_execution_status"] == "Optimal"
    assert pair["chosen_structure_certificate_summary"]
    assert pair["rejected_structure_certificate_summary"]
    saved = read_jsonl(out)
    assert saved[0]["metadata"]["problem_type"] == "fixed_order_cost_big_m"


def test_preference_construction_ignores_reference_objective_values(tmp_path):
    exp_a = tmp_path / "a"
    exp_b = tmp_path / "b"
    exp_a.mkdir()
    exp_b.mkdir()
    rows_a = [
        _row("good", reference_objective=999.0, structure_score=1.0, missing=[]),
        _row("bad", reference_objective=1.0, structure_score=0.0, missing=["inventory_balance"]),
    ]
    rows_b = [
        _row("good", reference_objective=1.0, structure_score=1.0, missing=[]),
        _row("bad", reference_objective=999.0, structure_score=0.0, missing=["inventory_balance"]),
    ]
    write_jsonl(exp_a / "candidate_evaluations.jsonl", rows_a)
    write_jsonl(exp_b / "candidate_evaluations.jsonl", rows_b)

    pairs_a = build_preference_pairs(exp_a, exp_a / "pairs.jsonl", min_score_gap=0.01, max_pairs_per_problem=1)
    pairs_b = build_preference_pairs(exp_b, exp_b / "pairs.jsonl", min_score_gap=0.01, max_pairs_per_problem=1)

    assert [(p["chosen_candidate_id"], p["rejected_candidate_id"]) for p in pairs_a] == [("good", "bad")]
    assert [(p["chosen_candidate_id"], p["rejected_candidate_id"]) for p in pairs_b] == [("good", "bad")]


def test_no_reference_leakage_audit_still_passes_formal_selection_row():
    rows = [{
        "method_name": "ReplenishVerifier-Full",
        "selected": True,
        "uses_reference_objective_for_selection": False,
        "selection_policy": "Hard Selection Gate over structure signals; no reference objective",
        "score": 1.0,
        "selection_score": 1.0,
        "objective_correct": 0.0,
    }]
    assert _audit_rows(rows, "unit", require_selected=True) == []
```

- [ ] **Step 2: Run preference tests and verify failure**

Run:

```bash
python -m pytest tests/test_preference_metadata.py -q
```

Expected before implementation: missing metadata fields.

- [ ] **Step 3: Implement metadata helpers in `build_preference_data.py`**

Add version constant and helpers after imports:

```python
PREFERENCE_CONSTRUCTION_VERSION = "2026-06-16.no_reference_structure_v1"


def _missing_structures(row):
    return list((row.get("structure_verification") or {}).get("missing") or [])


def _execution_status(row):
    return (row.get("execution") or {}).get("status")


def _certificate_summary(row):
    certs = (row.get("structure_verification") or {}).get("certificates") or []
    return [
        {
            "rule_name": cert.get("rule_name"),
            "required": cert.get("required"),
            "passed": cert.get("passed"),
            "score": cert.get("score"),
            "evidence_strength": cert.get("evidence_strength"),
        }
        for cert in certs
    ]


def _prompt_type(row):
    return row.get("prompt_type") or (row.get("generation_config") or {}).get("prompt_type")
```

When building a pair, replace the current `pairs.append({...})` with an object that includes existing fields plus metadata:

```python
                pair = {
                    "problem_id": pid,
                    "chosen_candidate_id": chosen.get("candidate_id"),
                    "rejected_candidate_id": rejected.get("candidate_id"),
                    "chosen_score": _preference_score(chosen),
                    "rejected_score": _preference_score(rejected),
                    "score_gap": gap,
                    "chosen_structure_score": chosen.get("structure_score"),
                    "rejected_structure_score": rejected.get("structure_score"),
                    "chosen_feedback_count": _feedback_count(chosen),
                    "rejected_feedback_count": _feedback_count(rejected),
                    "chosen": _candidate_text(chosen),
                    "rejected": _candidate_text(rejected),
                    "chosen_missing_structures": _missing_structures(chosen),
                    "rejected_missing_structures": _missing_structures(rejected),
                    "chosen_execution_status": _execution_status(chosen),
                    "rejected_execution_status": _execution_status(rejected),
                    "chosen_structure_certificate_summary": _certificate_summary(chosen),
                    "rejected_structure_certificate_summary": _certificate_summary(rejected),
                    "selection_policy": "preference pairs from executable + optimal + structure completeness + lower repair feedback; no reference objective",
                    "uses_reference_objective_for_preference": False,
                    "preference_source": "replenishment_structure_verifier",
                    "preference_construction_version": PREFERENCE_CONSTRUCTION_VERSION,
                    "problem_type": chosen.get("problem_type") or rejected.get("problem_type"),
                    "difficulty": chosen.get("difficulty") or rejected.get("difficulty"),
                    "prompt_type": _prompt_type(chosen) or _prompt_type(rejected),
                    "candidate_ids": {"chosen": chosen.get("candidate_id"), "rejected": rejected.get("candidate_id")},
                }
                pair["metadata"] = {
                    "uses_reference_objective_for_preference": False,
                    "preference_source": pair["preference_source"],
                    "preference_construction_version": pair["preference_construction_version"],
                    "problem_type": pair["problem_type"],
                    "difficulty": pair["difficulty"],
                    "prompt_type": pair["prompt_type"],
                    "candidate_ids": pair["candidate_ids"],
                }
                pairs.append(pair)
```

Update CSV `fieldnames` to include the new scalar fields:

```python
        "chosen_missing_structures",
        "rejected_missing_structures",
        "chosen_execution_status",
        "rejected_execution_status",
        "preference_source",
        "preference_construction_version",
        "problem_type",
        "difficulty",
        "prompt_type",
```

`csv.DictWriter` can write lists as Python string representations; this is acceptable for a summary CSV because JSONL remains the canonical training artifact.

- [ ] **Step 4: Run preference tests**

Run:

```bash
python -m pytest tests/test_preference_metadata.py -q
```

Expected: all selected tests pass.

---

## Task 6: Documentation and Paper Synchronization

**Files:**
- Modify: `README.md`
- Modify: `docs/experiment_operation_guide.md`
- Modify: `docs/real_llm_experiment_checklist.md`
- Modify: `docs/code_and_claim_risk_audit.md`
- Modify: `docs/ccfa_revision_roadmap.md`
- Modify: `docs/submit_readiness_checklist.md`
- Modify: `papers/replenishverifier_draft_zh.md`
- Modify: `papers/replenishverifier_draft_en.md`
- Modify: `progress.md`

- [ ] **Step 1: Add README protocol section**

In `README.md`, add or update a section named `Pre-experiment protocol safeguards` containing these exact points in project style:

```markdown
### Pre-experiment protocol safeguards

Candidate generation supports `--prompt_type hidden_verifier|plain|structured`.

- `hidden_verifier` is the recommended main-experiment setting. It hides `expected_structures`, keeps the PuLP solve/export contract, and asks for clear variable/constraint names without exposing required replenishment structure labels.
- `plain` hides `expected_structures` and gives the natural-language problem plus JSON parameters. Parameters are provided so generated PuLP code can build an executable instance model.
- `structured` exposes expected structures and is only for guided generation or appendix ablations. It must not be used as the default main-experiment prompt.

Generation rows should save raw generations, `prompt_type`, seed, decoding parameters, and model path/version/hash where available. Seeds improve reproducibility, but exact determinism is not guaranteed across GPU sampling, Transformers backends, CUDA kernels, hardware, or model versions.

`run_all_methods` writes both structure-aware `repair_prompts.*` and generic `generic_repair_prompts.*`. Generic repair uses execution/solver/audit feedback only and intentionally avoids replenishment-specific missing-structure labels. Structure-aware repair may use missing required structures, rule certificates, and replenishment repair hints.

Runtime overhead is a required future reporting metric. Use `python -m replenishverifier.experiments.analyze_runtime_overhead --exp_dir <exp_dir>` after an evaluation run to summarize total candidate evaluation time, LP parse time, and structure-check time. Missing timing fields are reported as `NA`; no runtime numbers should be invented before real experiments.

Variable-renaming robustness uses `rename_variables_for_robustness.py` as a lightweight text-level perturbation. It is not AST-safe renaming and should be manually spot-checked before formal experiments.

Preference pairs exported by `build_preference_data.py` are future DPO/PRM/LoRA-style learning signals. They do not imply that any SFT, DPO, PRM, RL, LoRA, or TGRPO training has been completed. Formal selection and preference construction do not use `reference_objective`; reference objectives are evaluation-only.
```

- [ ] **Step 2: Update operation/checklist docs**

In `docs/experiment_operation_guide.md` and `docs/real_llm_experiment_checklist.md`, add the real experiment command shape without running it:

```markdown
Recommended main prompt mode:

```bash
python -m replenishverifier.llm.run_generation \
  --benchmark data/generated/test_50.jsonl \
  --out data/candidates/<model>_hidden_verifier_k4_50.jsonl \
  --model <MODEL_PATH_OR_NAME> \
  --k 4 \
  --prompt_type hidden_verifier \
  --seed 42 \
  --max_new_tokens 2048 \
  --temperature 0.2 \
  --top_p 0.95
```

Do not use `--prompt_type structured` for main results because it exposes `expected_structures`; reserve it for guided/appendix ablations.
```

Also add commands for later analysis:

```markdown
Runtime overhead after evaluation:

```bash
python -m replenishverifier.experiments.analyze_runtime_overhead --exp_dir runs/<exp_dir>
```

Generic repair generation should use `generic_repair_prompts.jsonl`; structure-aware repair should use `repair_prompts.jsonl`.
```

- [ ] **Step 3: Update risk/roadmap/readiness docs**

In `docs/code_and_claim_risk_audit.md`, `docs/ccfa_revision_roadmap.md`, and `docs/submit_readiness_checklist.md`, add bullets stating:

```markdown
- Prompt leakage risk is controlled by making `hidden_verifier`/`plain` hide `expected_structures`; `structured` is guided/appendix-only.
- Generic repair is a fair control only when it excludes replenishment-specific missing labels and uses generic execution/solver/audit feedback.
- Runtime overhead must be reported from real evaluated candidates using the runtime analyzer; missing values are `NA`, not estimated.
- Naming robustness is currently a lightweight text-level perturbation, not an AST-safe transformation.
- Preference data is a future learning signal and cannot be described as DPO/PRM/LoRA improvement until training and evaluation are actually run.
- Formal selection and preference construction do not use `reference_objective`; `reference_objective` remains evaluation-only.
```

- [ ] **Step 4: Update English and Chinese paper drafts without filling numbers**

In `papers/replenishverifier_draft_en.md`, add a short protocol paragraph to the methodology/experiment setup area:

```markdown
To avoid prompt-side leakage, main experiments use `hidden_verifier` or `plain` prompts that do not reveal `expected_structures`. The `structured` prompt exposes expected structures and is reserved for guided-generation or appendix ablations. We separately report generic repair prompts, which use execution/solver/audit feedback only, and structure-aware repair prompts, which may use missing replenishment structures and rule-level certificates. Preference pairs are exported only as future DPO/PRM/LoRA-style learning signals; no training benefit is claimed unless such training is actually performed and evaluated. Runtime overhead and naming-variation robustness are treated as required follow-up metrics, with naming perturbation implemented only as lightweight text-level rewriting.
```

In `papers/replenishverifier_draft_zh.md`, add the Chinese equivalent:

```markdown
为避免 prompt 侧泄漏，主实验使用不暴露 `expected_structures` 的 `hidden_verifier` 或 `plain` prompt；会显式暴露 expected structures 的 `structured` prompt 仅用于 guided generation 或 appendix ablation。本文区分 generic repair prompts 与 structure-aware repair prompts：前者只使用 execution/solver/audit 反馈，后者才允许使用 missing replenishment structures 和 rule-level certificates。Preference pairs 仅作为未来 DPO/PRM/LoRA 等训练的候选学习信号；除非实际训练并评估，否则不声称训练带来提升。Runtime overhead 和 variable naming robustness 是后续真实实验必须报告的指标，其中命名扰动只是 lightweight text-level rewriting，不是完整 AST-safe renaming。
```

Ensure all result tables still use `[TO FILL AFTER REAL LLM EXPERIMENT]` where they lack real results.

- [ ] **Step 5: Update planning progress log**

Append this entry to `progress.md`:

```markdown
## 2026-06-16 — Pre-experiment enhancement implementation

### User request

The user asked to implement pre-experiment code and documentation enhancements without running real LLM generation, without running large benchmarks, without filling paper result numbers, without using Explore subagents, and without creating a git worktree.

### Actions completed

- Added prompt modes for `structured`, `plain`, and `hidden_verifier` generation.
- Split structure-aware and generic repair prompt artifacts.
- Added candidate runtime timing fields and a runtime overhead analyzer.
- Extended variable-renaming robustness with `descriptive_to_anonymous` mode while documenting it as text-level perturbation.
- Enriched preference-pair metadata while preserving no-reference construction.
- Updated README, docs, and paper drafts to explain prompt leakage, fair repair controls, runtime overhead, naming robustness limits, preference data limits, and no-reference selection.

### Verification

- Full suite command: `python -m pytest`
- Result: record the actual result after running tests.

### Notes

No real LLM generation, large benchmark run, fake result number, or training claim was added.
```

After tests run, replace `record the actual result after running tests` with the actual pytest result line.

- [ ] **Step 6: Search for forbidden result filling or training claims**

Use Grep, not shell grep:

Search patterns:

- `TO FILL]` to ensure no malformed placeholder was introduced.
- `ReplenishVerifier-DPO|LoRA improves|PRM improves|training completed|SFT completed|RL completed|TGRPO completed` in `README.md`, `docs/*.md`, and `papers/*.md`.

Expected: no new claims of completed training and no filled fake numbers.

---

## Task 7: Integration Verification

**Files:**
- All modified code and docs.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
python -m pytest \
  tests/test_prompt_modes.py \
  tests/test_repair_prompt_fairness.py \
  tests/test_runtime_overhead.py \
  tests/test_renaming_robustness.py \
  tests/test_preference_metadata.py \
  tests/test_repair_generation_dry_run.py \
  tests/test_strong_baselines.py \
  -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest
```

Expected: full suite passes. Existing PuLP deprecation warnings are acceptable if tests pass.

- [ ] **Step 3: If tests fail, fix instead of bypassing**

If a test fails:

1. Read the failure traceback.
2. Identify whether it is a test expectation issue or implementation issue.
3. Fix the implementation if the test matches the approved spec.
4. Re-run the failing test.
5. Re-run full suite.

Do not skip tests, weaken no-reference assertions, or remove fairness checks.

- [ ] **Step 4: Summarize final diff and outputs for the user**

Report:

1. Modified file list.
2. New CLI parameters.
3. New output files.
4. New tests.
5. Test commands and results.
6. Remaining TODOs.
7. Which changes answer reviewer concerns related to SIRL / OR-R1 / Step-Opt / OptMATH / OptiMUS / OptiRepair / OptArgus.

## Self-Review of Plan

- Spec coverage: prompt modes, repair fairness, runtime analyzer, renaming robustness, preference metadata, documentation/paper sync, and tests are each covered by a dedicated task.
- Placeholder scan: the plan contains no implementation placeholders. The phrase `[TO FILL AFTER REAL LLM EXPERIMENT]` is intentionally preserved as a paper placeholder that must not be filled in this stage.
- Type consistency: function names introduced in tests match implementation steps: `build_structure_aware_repair_prompts`, `build_generic_repair_prompts`, `analyze_runtime_overhead`, `rename_code`, and `build_preference_pairs`.
- Constraint consistency: no task asks to run real LLM generation, run large benchmarks, use Explore, create worktrees, commit, or use `reference_objective` for selection/preference construction.
