"""Strong non-domain-specific baselines for paper experiments.

These baselines intentionally avoid replenishment semantics and expected_structures.
They use only candidate-observable execution signals and generic LP artifacts.
"""


def code_output_format_valid(generated_code):
    """Generic code-format validity signal used by OR-R1-like voting.

    This intentionally checks only solver-code surface format. It does not inspect
    replenishment-specific structures such as inventory balance or Big-M links.
    """
    code = generated_code or ""
    if not code.strip():
        return False
    has_pulp = "import pulp" in code or "from pulp" in code or "pulp." in code
    has_model = "LpProblem" in code or "build_model" in code
    return bool(has_pulp and has_model)


def compute_objective_consensus_scores(rows, rel_tol=1e-4, abs_tol=1e-4):
    """Assign objective-consensus scores within one problem's candidate set.

    Scores are computed only from candidate-observable objective values. They do
    not use the reference objective. A candidate's score is the support of its
    objective-value cluster among valid candidates, so larger consensus clusters
    receive higher scores; candidates without an executable optimal objective
    receive 0.0.
    """
    valid = []
    for idx, row in enumerate(rows):
        execution = row.get("execution") or {}
        objective = execution.get("objective")
        if execution.get("executable") and execution.get("status") == "Optimal" and objective is not None:
            valid.append((idx, float(objective)))

    if not valid:
        return [0.0 for _ in rows]

    clusters = []
    for idx, objective in sorted(valid, key=lambda item: item[1]):
        placed = False
        for cluster in clusters:
            center = cluster["center"]
            tol = max(abs_tol, rel_tol * max(abs(center), abs(objective), 1.0))
            if abs(objective - center) <= tol:
                cluster["items"].append(idx)
                values = [value for _, value in valid if _ in cluster["items"]]
                cluster["center"] = sum(values) / len(values)
                placed = True
                break
        if not placed:
            clusters.append({"center": objective, "items": [idx]})

    valid_count = len(valid)
    scores = [0.0 for _ in rows]
    for cluster in clusters:
        support = len(cluster["items"]) / max(valid_count, 1)
        for idx in cluster["items"]:
            scores[idx] = float(support)
    return scores


def or_r1_like_voting_score(execution_result, consensus_score, code_format_valid=False):
    """Lightweight OR-R1-like test-time voting score.

    It mimics executable/valid-code/objective-consensus voting signals without
    reference objectives and without replenishment-specific structure rules.
    """
    executable = 1.0 if execution_result.get("executable") else 0.0
    optimal = 1.0 if execution_result.get("status") == "Optimal" else 0.0
    has_objective = 1.0 if execution_result.get("objective") is not None else 0.0
    lp_exported = 1.0 if execution_result.get("lp_path") else 0.0
    format_signal = 1.0 if code_format_valid else 0.0
    return float(
        0.25 * executable
        + 0.25 * optimal
        + 0.15 * has_objective
        + 0.15 * float(consensus_score or 0.0)
        + 0.10 * format_signal
        + 0.10 * lp_exported
    )


def compute_lp_stats(parsed):
    if parsed is None:
        return {
            "lp_exported": False,
            "objective_present": False,
            "constraints_present": False,
            "variables_count": 0,
            "constraints_count": 0,
            "binary_variables_count": 0,
            "bounds_count": 0,
            "bounds_present": False,
            "objective_terms_count": 0,
            "constraints_to_variables_ratio": 0.0,
        }

    objective_terms_count = _count_linear_terms(parsed.objective, parsed.variable_names)
    constraints_to_variables_ratio = len(parsed.constraint_names) / max(len(parsed.variable_names), 1)
    return {
        "lp_exported": True,
        "objective_present": bool(parsed.objective.strip()),
        "constraints_present": len(parsed.constraint_names) > 0,
        "variables_count": len(parsed.variable_names),
        "constraints_count": len(parsed.constraint_names),
        "binary_variables_count": len(parsed.binary_variables),
        "bounds_count": len(parsed.bounds),
        "bounds_present": len(parsed.bounds) > 0,
        "objective_terms_count": objective_terms_count,
        "constraints_to_variables_ratio": float(constraints_to_variables_ratio),
    }


def _cap_count(value, cap):
    if value <= 0:
        return 0.0
    return min(float(value) / float(cap), 1.0)


def _healthy_ratio(value, low, high):
    if value <= 0:
        return 0.0
    if low <= value <= high:
        return 1.0
    if value < low:
        return max(value / low, 0.0)
    return max(1.0 - ((value - high) / max(high, 1.0)), 0.0)


def _count_linear_terms(expr, variable_names):
    if not expr or not variable_names:
        return 0
    return sum(1 for name in variable_names if name in expr)


def sirl_like_lp_stats_score(execution_result, lp_stats):
    """Generic solver + LP artifact score, with no replenishment semantics."""
    executable = 1.0 if execution_result.get("executable") else 0.0
    optimal = 1.0 if execution_result.get("status") == "Optimal" else 0.0
    lp_exported = 1.0 if lp_stats.get("lp_exported") else 0.0
    objective_present = 1.0 if lp_stats.get("objective_present") else 0.0
    constraints_present = 1.0 if lp_stats.get("constraints_present") else 0.0
    variable_signal = _cap_count(lp_stats.get("variables_count", 0), cap=5)
    constraint_signal = _cap_count(lp_stats.get("constraints_count", 0), cap=5)
    objective_signal = _cap_count(lp_stats.get("objective_terms_count", 0), cap=3)
    ratio_signal = _healthy_ratio(lp_stats.get("constraints_to_variables_ratio", 0.0), low=0.3, high=6.0)
    binary_signal = 1.0 if lp_stats.get("binary_variables_count", 0) > 0 else 0.0
    bounds_signal = 1.0 if lp_stats.get("bounds_present") else 0.0

    return float(
        0.20 * executable
        + 0.20 * optimal
        + 0.10 * lp_exported
        + 0.10 * objective_present
        + 0.10 * constraints_present
        + 0.08 * variable_signal
        + 0.08 * constraint_signal
        + 0.06 * objective_signal
        + 0.04 * ratio_signal
        + 0.02 * binary_signal
        + 0.02 * bounds_signal
    )


def _name_is_suspicious(name):
    lowered = name.lower()
    if lowered in {"x", "x_0", "var", "var_0", "dummy", "dummy_0"}:
        return True
    return any(term in lowered for term in {"dummy", "foo", "bar", "test"})


def _constraint_name_is_suspicious(name):
    lowered = name.lower()
    if lowered in {"c", "c0", "c_0", "constraint", "constraint_0"}:
        return True
    return any(term in lowered for term in {"dummy", "placeholder", "test"})


def compute_optargus_audit(parsed, execution_result=None):
    lp_stats = compute_lp_stats(parsed)
    variable_names = parsed.variable_names if parsed is not None else []
    constraint_names = parsed.constraint_names if parsed is not None else []
    objective = parsed.objective if parsed is not None else ""

    suspicious_names = [name for name in variable_names if _name_is_suspicious(name)]
    suspicious_constraint_names = [name for name in constraint_names if _constraint_name_is_suspicious(name)]
    empty_model = not lp_stats["objective_present"] or not lp_stats["variables_count"] or not lp_stats["constraints_count"]
    objective_has_variable = any(name in objective for name in variable_names)
    objective_variable_coverage = 0.0
    if variable_names:
        objective_variable_coverage = _count_linear_terms(objective, variable_names) / max(len(variable_names), 1)

    bounded_ratio = 1.0 if lp_stats["bounds_present"] else 0.0
    if variable_names:
        bounded_names = set()
        for bound in (parsed.bounds if parsed is not None else []):
            for name in variable_names:
                if name in bound:
                    bounded_names.add(name)
        # PuLP often omits default nonnegative bounds, so do not over-penalize missing bounds.
        bounded_ratio = max(bounded_ratio, len(bounded_names) / max(len(variable_names), 1))

    issues = []
    if execution_result and execution_result.get("status") in {"Error", "Timeout", "Missing"}:
        issues.append("solver_error")
    if not lp_stats["objective_present"]:
        issues.append("missing_objective")
    if not lp_stats["variables_count"]:
        issues.append("missing_variables")
    if not lp_stats["constraints_count"]:
        issues.append("missing_constraints")
    if empty_model:
        issues.append("empty_or_underspecified_model")
    if lp_stats["objective_present"] and not objective_has_variable:
        issues.append("objective_without_decision_variable")
    if suspicious_names:
        issues.append("placeholder_variable_names")
    if suspicious_constraint_names:
        issues.append("placeholder_constraint_names")

    audit = {
        "objective_present": lp_stats["objective_present"],
        "variables_present": lp_stats["variables_count"] > 0,
        "constraints_present": lp_stats["constraints_count"] > 0,
        "empty_model": empty_model,
        "objective_has_variable": objective_has_variable,
        "objective_variable_coverage": float(objective_variable_coverage),
        "constraints_to_variables_ratio": lp_stats["constraints_to_variables_ratio"],
        "bounded_variables_ratio": float(bounded_ratio),
        "suspicious_variable_names": suspicious_names,
        "suspicious_variable_name_count": len(suspicious_names),
        "suspicious_constraint_names": suspicious_constraint_names,
        "suspicious_constraint_name_count": len(suspicious_constraint_names),
        "generic_issues": issues,
        "generic_issue_count": len(issues),
        "solver_error": bool(execution_result and execution_result.get("status") in {"Error", "Timeout", "Missing"}),
    }
    return audit


def optargus_like_audit_score(execution_result, audit):
    executable = 1.0 if execution_result.get("executable") else 0.0
    optimal = 1.0 if execution_result.get("status") == "Optimal" else 0.0
    objective_present = 1.0 if audit.get("objective_present") else 0.0
    variables_present = 1.0 if audit.get("variables_present") else 0.0
    constraints_present = 1.0 if audit.get("constraints_present") else 0.0
    non_empty = 0.0 if audit.get("empty_model") else 1.0
    objective_has_variable = 1.0 if audit.get("objective_has_variable") else 0.0
    objective_coverage = float(audit.get("objective_variable_coverage", 0.0))
    ratio_signal = _healthy_ratio(audit.get("constraints_to_variables_ratio", 0.0), low=0.3, high=8.0)
    bounded_ratio = float(audit.get("bounded_variables_ratio", 0.0))
    name_penalty = min(
        audit.get("suspicious_variable_name_count", 0) * 0.08
        + audit.get("suspicious_constraint_name_count", 0) * 0.04,
        0.25,
    )
    issue_penalty = min(audit.get("generic_issue_count", 0) * 0.05, 0.30)

    score = (
        0.16 * executable
        + 0.14 * optimal
        + 0.12 * objective_present
        + 0.12 * variables_present
        + 0.12 * constraints_present
        + 0.10 * non_empty
        + 0.08 * objective_has_variable
        + 0.06 * objective_coverage
        + 0.05 * ratio_signal
        + 0.05 * bounded_ratio
        - name_penalty
        - issue_penalty
    )
    return float(max(score, 0.0))


def optirepair_like_score(execution_result, audit):
    """Generic repair-style baseline score.

    This imitates generic diagnosis/repair readiness: prefer executable/optimal
    candidates with fewer generic audit issues, but do not use replenishment
    semantics or expected structures.
    """
    executable = 1.0 if execution_result.get("executable") else 0.0
    optimal = 1.0 if execution_result.get("status") == "Optimal" else 0.0
    audit_score = optargus_like_audit_score(execution_result, audit)
    generic_issue_score = 1.0 - min(audit.get("generic_issue_count", 0) / 6.0, 1.0)
    return float(0.25 * executable + 0.20 * optimal + 0.40 * audit_score + 0.15 * generic_issue_score)


def generic_repair_feedback(execution_result, audit):
    messages = []
    if not execution_result.get("executable"):
        messages.append("Fix Python/PuLP execution errors so the model can be built and solved.")
    if not audit.get("objective_present"):
        messages.append("Add a clear optimization objective to the PuLP model.")
    if not audit.get("variables_present"):
        messages.append("Add decision variables to the model.")
    if not audit.get("constraints_present"):
        messages.append("Add constraints that define the feasible region.")
    if audit.get("empty_model"):
        messages.append("The model appears empty or underspecified; ensure objective, variables, and constraints are all present.")
    if audit.get("objective_present") and not audit.get("objective_has_variable"):
        messages.append("Ensure the objective contains decision variables rather than only constants.")
    if audit.get("suspicious_variable_names"):
        messages.append("Rename suspicious placeholder variables to meaningful decision-variable names.")
    if audit.get("suspicious_constraint_names"):
        messages.append("Rename placeholder constraints to describe the mathematical restriction they encode.")
    if not messages:
        messages.append("No generic optimization-model audit issue found; if the model is wrong, inspect task-specific requirements separately.")
    return "\n".join(f"- {message}" for message in messages)


def _required_missing_structures(structure):
    missing = set((structure or {}).get("missing") or [])
    required = (structure or {}).get("required_structures")
    if required is None:
        expected = (structure or {}).get("expected") or {}
        required = [key for key, value in expected.items() if value]
    if required:
        missing &= set(required)
    return sorted(missing)


def classify_error_type(row):
    execution = row.get("execution") or {}
    structure = row.get("structure_verification") or {}
    audit = row.get("optargus_audit") or {}
    missing = _required_missing_structures(structure)

    if not execution.get("executable"):
        status = execution.get("status")
        if status == "Timeout":
            return "execution_timeout"
        return "execution_error"
    if execution.get("status") != "Optimal":
        return "solver_not_optimal"
    if audit.get("empty_model"):
        return "generic_empty_or_underspecified_model"
    if "inventory_balance" in missing:
        return "missing_inventory_balance"
    if "capacity_constraint" in missing:
        return "missing_capacity_constraint"
    if "big_m_constraint" in missing:
        return "missing_big_m_constraint"
    if "binary_order_variable" in missing:
        return "missing_binary_order_variable"
    if "shortage_variable" in missing:
        return "missing_shortage_variable"
    if any(key in missing for key in ["holding_cost", "shortage_cost", "fixed_order_cost"]):
        return "missing_cost_term"
    if missing:
        return "other_missing_structure"
    if not row.get("objective_correct", 0.0):
        return "objective_mismatch_after_selection"
    return "no_error_detected"
