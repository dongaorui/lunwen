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
    sample = {
        "id": "p0",
        "problem_type": "fixed_order_cost_big_m",
        "natural_language": "Minimize total cost.",
        "parameters": {},
    }
    repair_row = {
        "generic_repair_feedback": "- Add a clear objective and constraints.",
        "feedback": "Missing inventory_balance",
        "repair_prompt": "Missing big_m_constraint",
    }
    prompt = build_generic_repair_prompt(sample, repair_row, original_code="import pulp\n")
    for label in DOMAIN_LABELS:
        assert label not in prompt
    assert "Generic feedback" in prompt


def test_prompt_builder_generic_repair_prompt_does_not_fallback_to_structure_feedback():
    sample = {
        "id": "p0",
        "problem_type": "fixed_order_cost_big_m",
        "natural_language": "Minimize total cost.",
        "parameters": {},
    }
    repair_row = {
        "feedback": "Missing inventory_balance",
        "repair_prompt": "Missing big_m_constraint",
    }
    prompt = build_generic_repair_prompt(sample, repair_row, original_code="import pulp\n")
    for label in DOMAIN_LABELS:
        assert label not in prompt
    assert "Inspect generic execution" in prompt


def test_prompt_builder_structure_aware_repair_prompt_can_use_domain_feedback():
    sample = {"id": "p0", "natural_language": "Minimize total cost.", "parameters": {}}
    prompt = build_repair_prompt(sample, {"feedback": "Missing inventory_balance and big_m_constraint."}, original_code="import pulp\n")
    assert "inventory_balance" in prompt
    assert "big_m_constraint" in prompt
