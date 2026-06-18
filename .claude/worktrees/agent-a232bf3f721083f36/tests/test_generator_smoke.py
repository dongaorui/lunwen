import random
import subprocess
import sys
from pathlib import Path

import pytest

from replenishverifier.benchmark.generator import generate_benchmark
from replenishverifier.benchmark.schemas import PROBLEM_TYPES
from replenishverifier.benchmark.templates import (
    build_model,
    modeling_steps,
    natural_language,
    natural_language_variants,
    replenishment_entities,
    sample_params,
    semantic_frame,
    validate_replenishment_instance,
)
from replenishverifier.solver.pulp_runner import solve_pulp_model
from replenishverifier.utils.io import read_jsonl


def test_generate_benchmark_smoke(tmp_path):
    out = tmp_path / "benchmark.jsonl"
    lp_dir = tmp_path / "lp"
    rows = generate_benchmark(out, lp_dir, n_per_type=1, seed=1)
    assert len(rows) == 5
    loaded = read_jsonl(out)
    assert len(loaded) == 5
    for row in loaded:
        assert Path(row["reference_lp_path"]).exists()
        assert row["reference_status"] == "Optimal"
        assert row["language_style"]
        assert row["template_id"]
        assert row["semantic_frame"]
        assert row["replenishment_entities"]
        assert row["replenishment_modeling_steps"]


def test_semantic_frame_exists_for_each_problem_type():
    for problem_type in PROBLEM_TYPES:
        params = sample_params(problem_type, random.Random(13))
        frame = semantic_frame(problem_type, params)

        assert frame["decision_variables"]
        assert frame["objective_terms"]
        assert frame["constraints"]
        assert frame["replenishment_structures"]
        assert set(frame["required_structures"]) <= set(frame["replenishment_structures"])

    fixed = semantic_frame("fixed_order_cost_big_m", sample_params("fixed_order_cost_big_m", random.Random(3)))
    assert "binary_order_variable" in fixed["required_structures"]
    assert "big_m_constraint" in fixed["required_structures"]
    assert any("Big-M" in item for item in fixed["constraints"])


def test_replenishment_entities_include_problem_specific_core_fields():
    cases = {
        "single_period_newsvendor": {"demand", "unit_order_cost", "holding_cost", "shortage_cost"},
        "single_item_multi_period": {"periods", "initial_inventory", "demand", "unit_order_cost", "holding_cost"},
        "single_item_multi_period_shortage": {"shortage_or_backlog", "shortage_cost"},
        "multi_item_capacity": {"items", "item_volume", "volume", "storage_capacity"},
        "fixed_order_cost_big_m": {"fixed_order_cost", "big_m"},
    }
    for problem_type, required in cases.items():
        entities = replenishment_entities(problem_type, sample_params(problem_type, random.Random(5)))
        assert required <= set(entities)


def test_modeling_steps_cover_key_lp_structures():
    assert any("inventory balance" in step for step in modeling_steps("single_item_multi_period", sample_params("single_item_multi_period")))
    assert any("shortage" in step and "penalt" in step for step in modeling_steps("single_item_multi_period_shortage", sample_params("single_item_multi_period_shortage")))
    assert any("capacity constraint" in step for step in modeling_steps("multi_item_capacity", sample_params("multi_item_capacity")))
    fixed_steps = modeling_steps("fixed_order_cost_big_m", sample_params("fixed_order_cost_big_m"))
    assert any("binary order trigger" in step for step in fixed_steps)
    assert any("Big-M linking" in step for step in fixed_steps)


def test_natural_language_variants_are_diverse_and_seed_reproducible():
    params = sample_params("single_period_newsvendor", random.Random(7))
    variants = natural_language_variants("single_period_newsvendor", params)

    assert len(variants) >= 4
    assert {variant["style"] for variant in variants} >= {"math", "business", "verbose", "table"}
    assert len({variant["text"] for variant in variants}) == len(variants)
    assert natural_language("single_period_newsvendor", params, style="table").startswith("Problem data")

    rng_a = random.Random(123)
    rng_b = random.Random(123)
    assert natural_language("single_period_newsvendor", params, rng=rng_a) == natural_language("single_period_newsvendor", params, rng=rng_b)


def test_language_template_does_not_change_reference_model_objective(tmp_path):
    params = sample_params("single_item_multi_period", random.Random(11))
    objectives = []
    for style in ["math", "business", "verbose", "table"]:
        assert natural_language("single_item_multi_period", params, style=style)
        model = build_model("single_item_multi_period", params)
        result = solve_pulp_model(model, lp_path=tmp_path / f"{style}.lp", msg=False)
        objectives.append(result["objective"])

    assert len(set(objectives)) == 1


def test_generate_unlabeled_prompts_omit_labels_by_default(tmp_path):
    out = tmp_path / "unlabeled.jsonl"
    lp_dir = tmp_path / "lp"
    rows = generate_benchmark(out, lp_dir, n_per_type=1, seed=3, include_labels=False)

    assert len(rows) == 5
    for row in rows:
        assert {"id", "problem_type", "difficulty", "natural_language", "language_style", "template_id"} <= set(row)
        assert row["semantic_frame"]
        assert row["replenishment_entities"]
        assert "replenishment_modeling_steps" not in row
        assert "reference_objective" not in row
        assert "reference_code" not in row
        assert "expected_structures" not in row
        assert "reference_lp_path" not in row
        assert "parameters" not in row


def test_generate_unlabeled_prompts_can_include_parameters(tmp_path):
    rows = generate_benchmark(tmp_path / "unlabeled.jsonl", tmp_path / "lp", n_per_type=1, seed=3, include_labels=False, include_parameters=True)

    assert "parameters" in rows[0]


def test_unlabeled_modeling_steps_are_optional(tmp_path):
    rows = generate_benchmark(
        tmp_path / "unlabeled_steps.jsonl",
        tmp_path / "lp",
        n_per_type=1,
        seed=3,
        include_labels=False,
        include_modeling_steps=True,
    )

    assert "replenishment_modeling_steps" in rows[0]
    assert "reference_objective" not in rows[0]


def test_validate_replenishment_instance_rejects_invalid_rows(tmp_path):
    row = generate_benchmark(tmp_path / "benchmark.jsonl", tmp_path / "lp", n_per_type=1, seed=4, problem_types=["single_period_newsvendor"])[0]
    assert validate_replenishment_instance(row, include_labels=True) is True

    missing_language = dict(row)
    missing_language["natural_language"] = ""
    with pytest.raises(ValueError, match="natural_language"):
        validate_replenishment_instance(missing_language, include_labels=True)

    missing_frame = dict(row)
    missing_frame.pop("semantic_frame")
    with pytest.raises(ValueError, match="semantic_frame"):
        validate_replenishment_instance(missing_frame, include_labels=True)

    invalid_type = dict(row)
    invalid_type["problem_type"] = "not_a_problem"
    with pytest.raises(ValueError, match="unknown problem_type"):
        validate_replenishment_instance(invalid_type, include_labels=True)

    unlabeled_leak = {
        key: value
        for key, value in row.items()
        if key not in {"expected_structures", "reference_code", "reference_lp_path", "reference_status"}
    }
    with pytest.raises(ValueError, match="unlabeled row contains label fields"):
        validate_replenishment_instance(unlabeled_leak, include_labels=False)


def test_unlabeled_cli_does_not_require_lp_dir(tmp_path):
    out = tmp_path / "prompts.jsonl"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_benchmark.py",
            "--output",
            str(out),
            "--n-per-type",
            "1",
            "--seed",
            "5",
            "--unlabeled",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rows = read_jsonl(out)
    assert len(rows) == 5
    assert "reference_objective" not in rows[0]


def test_language_rng_does_not_change_parameter_sequence(tmp_path):
    seed = 9
    expected_rng = random.Random(seed)
    expected_params = []
    for problem_type in PROBLEM_TYPES:
        for _ in range(2):
            expected_params.append(sample_params(problem_type, expected_rng))

    rows = generate_benchmark(
        tmp_path / "prompts.jsonl",
        tmp_path / "lp",
        n_per_type=2,
        seed=seed,
        include_labels=False,
        include_parameters=True,
    )

    assert [row["parameters"] for row in rows] == expected_params
    assert [row["template_id"] for row in rows] == [
        row["template_id"]
        for row in generate_benchmark(
            tmp_path / "prompts_again.jsonl",
            tmp_path / "lp_again",
            n_per_type=2,
            seed=seed,
            include_labels=False,
            include_parameters=True,
        )
    ]
