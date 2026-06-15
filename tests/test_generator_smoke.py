import random
import subprocess
import sys
from pathlib import Path

from replenishverifier.benchmark.generator import generate_benchmark
from replenishverifier.benchmark.schemas import PROBLEM_TYPES
from replenishverifier.benchmark.templates import build_model, natural_language, natural_language_variants, sample_params
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
        assert "reference_objective" not in row
        assert "reference_code" not in row
        assert "expected_structures" not in row
        assert "reference_lp_path" not in row
        assert "parameters" not in row


def test_generate_unlabeled_prompts_can_include_parameters(tmp_path):
    rows = generate_benchmark(tmp_path / "unlabeled.jsonl", tmp_path / "lp", n_per_type=1, seed=3, include_labels=False, include_parameters=True)

    assert "parameters" in rows[0]


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
