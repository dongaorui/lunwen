import random
from pathlib import Path

from tqdm import tqdm

from replenishverifier.benchmark.schemas import DIFFICULTY_BY_TYPE, PROBLEM_TYPES
from replenishverifier.benchmark.templates import (
    build_model,
    choose_natural_language_variant,
    expected_for,
    modeling_steps,
    reference_code,
    replenishment_entities,
    sample_params,
    semantic_frame,
    validate_replenishment_instance,
)
from replenishverifier.solver.pulp_runner import solve_pulp_model
from replenishverifier.utils.io import write_jsonl


def generate_benchmark(
    output,
    lp_dir=None,
    n_per_type=20,
    seed=42,
    problem_types=None,
    include_labels=True,
    include_parameters=None,
    include_modeling_steps=None,
):
    param_rng = random.Random(seed)
    language_rng = random.Random(seed)
    output = Path(output)
    if include_labels and lp_dir is None:
        raise ValueError("lp_dir is required when include_labels=True")
    lp_dir = Path(lp_dir) if lp_dir is not None else None
    problem_types = problem_types or PROBLEM_TYPES
    if include_parameters is None:
        include_parameters = bool(include_labels)
    if include_modeling_steps is None:
        include_modeling_steps = bool(include_labels)

    rows = []
    for problem_type in problem_types:
        for idx in tqdm(range(n_per_type), desc=f"generate:{problem_type}"):
            sample_id = f"{problem_type}_{idx:04d}"
            params = sample_params(problem_type, param_rng)
            language_variant = choose_natural_language_variant(problem_type, params, rng=language_rng)

            row = {
                "id": sample_id,
                "difficulty": DIFFICULTY_BY_TYPE[problem_type],
                "problem_type": problem_type,
                "natural_language": language_variant["text"],
                "language_style": language_variant["style"],
                "template_id": language_variant["template_id"],
                "semantic_frame": semantic_frame(problem_type, params),
                "replenishment_entities": replenishment_entities(problem_type, params),
            }
            if include_parameters:
                row["parameters"] = params
            if include_modeling_steps:
                row["replenishment_modeling_steps"] = modeling_steps(problem_type, params)

            if include_labels:
                model = build_model(problem_type, params)
                lp_path = lp_dir / f"{sample_id}.lp"
                solve_result = solve_pulp_model(model, lp_path=lp_path, msg=False)
                row.update({
                    "expected_structures": expected_for(problem_type),
                    "reference_code": reference_code(problem_type, params),
                    "reference_objective": solve_result["objective"],
                    "reference_status": solve_result["status"],
                    "reference_lp_path": str(lp_path),
                })
            validate_replenishment_instance(row, include_labels=include_labels)
            rows.append(row)

    write_jsonl(output, rows)
    return rows
