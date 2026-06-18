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
