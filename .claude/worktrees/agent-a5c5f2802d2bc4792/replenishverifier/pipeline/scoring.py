def relative_error(candidate_obj, reference_obj):
    if candidate_obj is None or reference_obj is None:
        return None
    err = abs(candidate_obj - reference_obj)
    denom = max(abs(reference_obj), 1.0)
    return float(err / denom)


def strict_objective_correct(candidate_obj, reference_obj, rel_tol=1e-4, abs_tol=1e-4):
    if candidate_obj is None or reference_obj is None:
        return False
    err = abs(candidate_obj - reference_obj)
    if abs(reference_obj) <= abs_tol:
        return err <= abs_tol
    return err / abs(reference_obj) <= rel_tol


def objective_accuracy(candidate_obj, reference_obj, rel_tol=1e-4, abs_tol=1e-4):
    """Evaluation-only soft objective score in [0, 1].

    This function uses the reference objective and must not be used for formal
    candidate selection. It is only for reporting metrics after selection.
    """
    if candidate_obj is None or reference_obj is None:
        return 0.0
    err = abs(candidate_obj - reference_obj)
    denom = max(abs(reference_obj), 1.0)
    rel = err / denom
    if err <= abs_tol or rel <= rel_tol:
        return 1.0
    return max(0.0, 1.0 - rel)


def normalize_solver_status(status):
    text = str(status or "").strip().lower().replace(" ", "_").replace("-", "_")
    if text in {"optimal", "optimum"}:
        return "optimal"
    if text in {"feasible", "integer_feasible", "solution_found"}:
        return "feasible"
    if text in {"infeasible", "not_feasible"}:
        return "infeasible"
    if text in {"unbounded"}:
        return "unbounded"
    if text in {"timeout", "time_limit", "timelimit"}:
        return "timeout"
    if text in {"error", "missing", "notrun", "not_run"}:
        return text
    return text or "unknown"


def hard_selection_gate(execution_result, raw_score, allow_feasible_selection=False):
    """Gate formal selection scores.

    By default, only executable + Optimal candidates can receive non-zero
    selection scores. Structure certificates remain available for diagnosis and
    repair even when this gate returns zero.
    """
    executable = bool((execution_result or {}).get("executable"))
    status = normalize_solver_status((execution_result or {}).get("status"))
    allowed = status == "optimal" or (allow_feasible_selection and status == "feasible")
    if not executable or not allowed:
        return 0.0
    return float(raw_score or 0.0)


def semantic_consistency_score(structure_result):
    """Prototype semantic consistency: all required structures present => 1, else structure score."""
    if not structure_result:
        return 0.0
    missing = structure_result.get("missing", [])
    if not missing:
        return 1.0
    return float(structure_result.get("structure_score", 0.0))


def solver_selection_score(execution_result):
    """Ground-truth-free solver-only raw score before Hard Selection Gate."""
    executable = 1.0 if execution_result.get("executable") else 0.0
    optimal = 1.0 if normalize_solver_status(execution_result.get("status")) == "optimal" else 0.0
    has_objective = 1.0 if execution_result.get("objective") is not None else 0.0
    return float(0.45 * executable + 0.45 * optimal + 0.10 * has_objective)


def full_selection_score(execution_result, structure_result):
    """Ground-truth-free ReplenishVerifier raw score before Hard Selection Gate."""
    executable = 1.0 if execution_result.get("executable") else 0.0
    optimal = 1.0 if normalize_solver_status(execution_result.get("status")) == "optimal" else 0.0
    struct_score = structure_result.get("structure_score", 0.0) if structure_result else 0.0
    semantic_score = semantic_consistency_score(structure_result)
    return float(0.25 * executable + 0.25 * optimal + 0.35 * struct_score + 0.15 * semantic_score)


def compute_score(execution_result, structure_result, reference_objective=None, mode="full", allow_feasible_selection=False):
    """Compute formal gated selection scores and evaluation-only metrics.

    `structure_score` is diagnostic and is preserved for failed/infeasible
    candidates. `selection_score` and `score` are used for ranking and pass
    through the Hard Selection Gate by default.
    """
    status = normalize_solver_status(execution_result.get("status"))
    executable = 1.0 if execution_result.get("executable") else 0.0
    feasible = 1.0 if status in {"optimal", "feasible"} else 0.0
    optimal = 1.0 if status == "optimal" else 0.0
    obj_score = objective_accuracy(execution_result.get("objective"), reference_objective)
    obj_correct = 1.0 if strict_objective_correct(execution_result.get("objective"), reference_objective) else 0.0
    struct_score = structure_result.get("structure_score", 0.0) if structure_result else 0.0
    semantic_score = semantic_consistency_score(structure_result)

    if mode == "solver_only":
        raw_total = solver_selection_score(execution_result)
        policy = "Hard Selection Gate over executable > optimal > has_objective; no reference objective"
    elif mode == "structure_only":
        raw_total = struct_score
        policy = "Hard Selection Gate over LP structure completeness only; no reference objective"
    elif mode == "direct":
        raw_total = 1.0
        policy = "candidate order only, with Hard Selection Gate for formal score; no reference objective"
    else:
        raw_total = full_selection_score(execution_result, structure_result)
        policy = "Hard Selection Gate over executable + optimal + LP structure + semantic consistency; no reference objective"

    gated_total = hard_selection_gate(execution_result, raw_total, allow_feasible_selection=allow_feasible_selection)

    return {
        "score": float(gated_total),
        "selection_score": float(gated_total),
        "raw_inference_score": float(raw_total),
        "selection_policy": policy,
        "hard_selection_gate": {
            "enabled": True,
            "allow_feasible_selection": bool(allow_feasible_selection),
            "solver_status_normalized": status,
            "passed": gated_total > 0.0 or (float(raw_total or 0.0) == 0.0 and bool(execution_result.get("executable")) and status == "optimal"),
            "rule": "Only executable + Optimal candidates can be selected." if not allow_feasible_selection else "Executable + Optimal candidates can be selected; Feasible is allowed by explicit flag.",
        },
        "uses_reference_objective_for_selection": False,
        "executable_score": executable,
        "feasible_score": feasible,
        "optimal_score": optimal,
        "objective_score": float(obj_score),
        "objective_correct": obj_correct,
        "objective_accuracy": obj_correct,
        "relative_error": relative_error(execution_result.get("objective"), reference_objective),
        "structure_score": float(struct_score),
        "semantic_consistency_score": float(semantic_score),
    }
