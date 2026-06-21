"""FullV2-specific feature extraction and conservative guarded selection.

This module is intentionally isolated: it is used only by the
``ReplenishVerifier-FullV2`` selector and by diagnostics.  It does not
provide features to ``Best-of-K``, ``ReplenishVerifier-Full``,
``Structure only``, or any other baseline.

All signals below are ground-truth-free and reference-free.  No
``reference_objective``, ``objective_correct``, oracle fields, reference LP,
or reference answer is read.
"""

import re


# ---------------------------------------------------------------------------
# Local copies of small helper functions to keep FullV2 isolated from the
# shared selector module.  These helpers intentionally mirror the ones in
# replenishverifier.experiments.methods but live here so FullV2 features do
# not leak into other methods.
# ---------------------------------------------------------------------------


def _row_problem_type(row):
    return row.get("problem_type") or ((row.get("reference") or {}).get("problem_type"))


def _structure_score(row):
    return float(row.get("structure_score", ((row.get("structure_verification") or {}).get("structure_score", 0.0))) or 0.0)


def _required_missing_for_row(row):
    structure = row.get("structure_verification") or {}
    missing = set(structure.get("missing") or [])
    required = structure.get("required_structures")
    if required is None:
        expected = structure.get("expected") or {}
        required = [key for key, value in expected.items() if value]
    if required:
        missing &= set(required)
    return missing


def _critical_structures_for_problem_type(problem_type):
    mapping = {
        "single_period_newsvendor": {"objective_term", "nonnegative_bounds"},
        "single_item_multi_period": {"inventory_balance", "order_variable", "inventory_variable", "holding_cost"},
        "multi_item_capacity": {"capacity_constraint", "item_indexed_order_variables", "nonnegative_bounds"},
        "fixed_order_cost_big_m": {"binary_order_variable", "big_m_constraint", "fixed_order_cost"},
        "single_item_multi_period_shortage": {"shortage_variable", "shortage_cost", "inventory_balance"},
    }
    return set(mapping.get(problem_type, {"inventory_balance"}))


def _critical_missing_structures(row):
    missing = _required_missing_for_row(row)
    problem_type = _row_problem_type(row)
    critical = _critical_structures_for_problem_type(problem_type)
    aliases = {
        "nonnegative_bounds": {"nonnegative_bounds", "bounds"},
        "objective_term": {"objective_term", "objective_terms"},
        "item_indexed_order_variables": {"item_indexed_order_variables", "order_variable"},
    }
    expanded = set(critical)
    for key in list(critical):
        expanded.update(aliases.get(key, set()))
    return sorted(missing & expanded)


def _constraint_coverage(row):
    structure = row.get("structure_verification") or {}
    required = structure.get("required_structures") or []
    missing = set(structure.get("missing") or [])
    if not required:
        return float(structure.get("structure_score", row.get("structure_score", 0.0)) or 0.0)
    return float(len([key for key in required if key not in missing]) / max(len(required), 1))


def _objective_term_coverage(row):
    value = row.get("objective_term_coverage")
    if value is None:
        value = (row.get("objective_term_verification") or {}).get("objective_term_coverage")
    return float(value or 0.0)


def _finite_objective_score(row):
    objective = (row.get("execution") or {}).get("objective")
    if objective is None:
        return 0.0
    try:
        value = float(objective)
    except (TypeError, ValueError):
        return 0.0
    if value != value or value in {float("inf"), float("-inf")}:
        return 0.0
    return 1.0


def _has_objective_score(row):
    return 1.0 if (row.get("execution") or {}).get("objective") is not None else 0.0


def _lp_health_score(row):
    stats = row.get("lp_stats") or {}
    if not stats.get("lp_exported"):
        return 0.0
    objective = 1.0 if stats.get("objective_present") else 0.0
    constraints = 1.0 if int(stats.get("constraints_count") or 0) > 0 else 0.0
    variables = 1.0 if int(stats.get("variables_count") or 0) > 0 else 0.0
    return float((objective + constraints + variables) / 3.0)


def _static_validation_score(row):
    return float(row.get("static_validation_score", ((row.get("static_validation") or {}).get("static_validation_score", 0.0))) or 0.0)


def _code_validity_score(row):
    return 1.0 if row.get("code_output_format_valid") else 0.0


def _type_aware_validation(row):
    return row.get("type_aware_static_validation") or ((row.get("static_validation") or {}).get("type_aware_static_validation")) or {}


def _type_aware_validation_score(row):
    validation = _type_aware_validation(row)
    return float(validation.get("score", 1.0) if validation else 1.0)


def _type_aware_hard_gate_score(row):
    validation = _type_aware_validation(row)
    return float(validation.get("hard_gate_score", 1.0) if validation else 1.0)


def _runtime_sec(row):
    return float(row.get("runtime_sec", row.get("total_candidate_evaluation_time", 0.0)) or 0.0)


def _candidate_index(row):
    if row.get("candidate_index") is not None:
        return int(row.get("candidate_index") or 0)
    cid = str(row.get("candidate_id", ""))
    match = re.search(r"(?:^|[_-])k(\d+)(?:\D|$)", cid, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    digits = "".join(ch for ch in cid if ch.isdigit())
    return int(digits) if digits else 0


def _normalized_cluster_distance(row):
    value = row.get("distance_to_cluster_median")
    if value is None:
        return 1.0
    try:
        objective = abs(float((row.get("execution") or {}).get("objective") or 0.0))
        return float(abs(float(value)) / max(objective, 1.0))
    except (TypeError, ValueError):
        return 1.0


def _fullv2_missing_critical_structures(row):
    """Critical-structure set used specifically by FullV2.

    Mirrors the behavior in methods.py but is kept local so FullV2
    diagnostics remain self-contained.
    """
    missing = set(_required_missing_for_row(row))
    critical = _critical_structures_for_problem_type(_row_problem_type(row))
    aliases = {
        "nonnegative_bounds": {"nonnegative_bounds", "bounds"},
        "objective_term": {"objective_term", "objective_terms"},
        "item_indexed_order_variables": {"item_indexed_order_variables", "order_variable"},
    }
    expanded = set(critical)
    for key in list(critical):
        expanded.update(aliases.get(key, set()))
    return sorted(missing & expanded)


def _solver_ok(row):
    execution = row.get("execution") or {}
    return bool(
        execution.get("executable")
        and str(execution.get("status") or "").strip().lower() == "optimal"
        and _finite_objective_score(row)
    )


# ---------------------------------------------------------------------------
# FullV2 feature extraction
# ---------------------------------------------------------------------------


def _fullv2_selection_score_values(row):
    """Return the raw tuple values without depending on selection_components."""
    missing_critical = _fullv2_missing_critical_structures(row)
    return (
        1.0 if _solver_ok(row) else 0.0,
        _has_objective_score(row),
        _finite_objective_score(row),
        _structure_score(row),
        _constraint_coverage(row),
        _objective_term_coverage(row),
        float(row.get("objective_term_lp_coefficient_coverage", 0.0) or 0.0),
        -float(len(missing_critical)),
        _type_aware_hard_gate_score(row),
        float(row.get("objective_consensus_score", 0.0) or 0.0),
        int(row.get("objective_cluster_size", 0) or 0),
        float(row.get("objective_density_score", 0.0) or 0.0),
        -_normalized_cluster_distance(row),
        _lp_health_score(row),
        _static_validation_score(row),
        _code_validity_score(row),
        _type_aware_validation_score(row),
        -_runtime_sec(row),
        -_candidate_index(row),
    )


def _fullv2_score_tuple_debug(row):
    """Named tuple debug matching the order in _fullv2_selection_score_values."""
    values = _fullv2_selection_score_values(row)
    names = [
        "solver_ok",
        "has_objective",
        "objective_finite",
        "structure_score",
        "constraint_coverage",
        "objective_term_coverage",
        "objective_term_lp_coefficient_coverage",
        "neg_critical_structure_penalty",
        "type_aware_hard_gate_score",
        "objective_consensus_score",
        "objective_cluster_size",
        "objective_density_score",
        "neg_distance_to_cluster_median_normalized",
        "lp_health_score",
        "static_validation_score",
        "code_validity_score",
        "type_aware_score",
        "neg_runtime",
        "neg_candidate_rank",
    ]
    return list(zip(names, values))


def fullv2_selection_components(row):
    """Return the FullV2 diagnostic component dict for a candidate row."""
    missing_critical = _fullv2_missing_critical_structures(row)
    execution = row.get("execution") or {}
    return {
        "selector_family": "fullv2",
        "solver_ok": 1.0 if _solver_ok(row) else 0.0,
        "execution_success": 1.0 if execution.get("executable") else 0.0,
        "solver_status": execution.get("status"),
        "has_objective": _has_objective_score(row),
        "objective_value": execution.get("objective"),
        "objective_finite": _finite_objective_score(row),
        "objective_consensus_score": float(row.get("objective_consensus_score", 0.0) or 0.0),
        "objective_cluster_size": int(row.get("objective_cluster_size", 0) or 0),
        "objective_density_score": float(row.get("objective_density_score", 0.0) or 0.0),
        "distance_to_cluster_median": row.get("distance_to_cluster_median"),
        "structure_score": _structure_score(row),
        "constraint_coverage": _constraint_coverage(row),
        "objective_term_coverage": _objective_term_coverage(row),
        "objective_term_lp_coefficient_coverage": float(row.get("objective_term_lp_coefficient_coverage", 0.0) or 0.0),
        "static_validation_score": _static_validation_score(row),
        "code_validity_score": _code_validity_score(row),
        "type_aware_score": _type_aware_validation_score(row),
        "type_aware_hard_gate_score": _type_aware_hard_gate_score(row),
        "type_aware_missing_critical_count": float(len(missing_critical)),
        "missing_critical_structures": missing_critical,
        "critical_structure_penalty": float(len(missing_critical)),
        "lp_health_score": _lp_health_score(row),
        "runtime": _runtime_sec(row),
        "candidate_rank": _candidate_index(row),
        "score_tuple_debug": _fullv2_score_tuple_debug(row),
    }


def fullv2_selection_score(row):
    """Backward-compatible tuple score used for tie-break key construction.

    The tuple is intentionally lexicographic, with high-weight no-reference
    signals first and runtime/candidate rank last.  It is used only for
    diagnostics and for any code that still calls the old ranking path.
    """
    return _fullv2_selection_score_values(row)


# ---------------------------------------------------------------------------
# Conservative guarded FullV2 selection
# ---------------------------------------------------------------------------


def _fullv2_challenger_score(row):
    """Ground-truth-free score used to pick a challenger against Full's base."""
    if not _solver_ok(row):
        return None
    if _fullv2_missing_critical_structures(row):
        return None
    return (
        1000.0 * _structure_score(row)
        + 500.0 * _constraint_coverage(row)
        + 300.0 * _objective_term_coverage(row)
        + 200.0 * _type_aware_hard_gate_score(row)
        + 150.0 * float(row.get("objective_consensus_score", 0.0) or 0.0)
        + 100.0 * _lp_health_score(row)
        + 80.0 * _code_validity_score(row)
        + 40.0 * _static_validation_score(row)
        + 20.0 * _type_aware_validation_score(row)
        - 0.001 * _runtime_sec(row)
    )


def _pick_fullv2_challenger(rows):
    """Return the strongest viable challenger, or None if none exists."""
    viable = []
    for row in rows:
        score = _fullv2_challenger_score(row)
        if score is not None:
            viable.append((row, score))
    if not viable:
        return None
    # Tie-breaker is intentionally dominated by the score; runtime and rank
    # are the very last resort and never override a structural advantage.
    return max(viable, key=lambda item: (
        item[1],
        _structure_score(item[0]),
        _constraint_coverage(item[0]),
        _objective_term_coverage(item[0]),
        _type_aware_hard_gate_score(item[0]),
        float(item[0].get("objective_consensus_score", 0.0) or 0.0),
        _lp_health_score(item[0]),
        _code_validity_score(item[0]),
        _static_validation_score(item[0]),
        -_runtime_sec(item[0]),
    ))[0]


def should_override_full_selection(full_row, challenger_row):
    """Decide whether a challenger should override Full's base selection.

    The decision is intentionally conservative and uses only no-reference
    signals.  It never overrides just because of runtime or candidate rank.
    """
    if challenger_row is None:
        return False, "no_viable_challenger"
    if full_row is None:
        return True, "full_base_missing"

    full_critical = _fullv2_missing_critical_structures(full_row)
    chal_critical = _fullv2_missing_critical_structures(challenger_row)

    # Case 1: Full chose a candidate with critical missing structures and the
    # challenger is clean — this is the strongest non-reference override signal.
    if full_critical and not chal_critical:
        return True, "full_has_critical_missing_challenger_clean"

    full_structure = _structure_score(full_row)
    chal_structure = _structure_score(challenger_row)
    full_constraint = _constraint_coverage(full_row)
    chal_constraint = _constraint_coverage(challenger_row)
    full_terms = _objective_term_coverage(full_row)
    chal_terms = _objective_term_coverage(challenger_row)

    # Case 2: Challenger is strictly better on the primary structure signal and
    # does not regress on constraint/objective-term coverage.
    if (
        chal_structure > full_structure + 1e-9
        and chal_constraint >= full_constraint - 1e-9
        and chal_terms >= full_terms - 1e-9
    ):
        return True, "challenger_strictly_better_structure_no_regression"

    # Case 3: Structure is equal.  Require improvement on at least two other
    # safety signals so that a single noisy dimension (e.g. consensus) cannot
    # override the stable Full base.
    if abs(chal_structure - full_structure) <= 1e-9:
        improvements = 0
        if chal_constraint > full_constraint + 1e-9:
            improvements += 1
        if chal_terms > full_terms + 1e-9:
            improvements += 1
        if float(challenger_row.get("objective_consensus_score", 0.0) or 0.0) > float(full_row.get("objective_consensus_score", 0.0) or 0.0) + 1e-9:
            improvements += 1
        if _lp_health_score(challenger_row) > _lp_health_score(full_row) + 1e-9:
            improvements += 1
        if _code_validity_score(challenger_row) > _code_validity_score(full_row) + 1e-9:
            improvements += 1
        if _static_validation_score(challenger_row) > _static_validation_score(full_row) + 1e-9:
            improvements += 1
        if _type_aware_hard_gate_score(challenger_row) > _type_aware_hard_gate_score(full_row) + 1e-9:
            improvements += 1
        if improvements >= 2:
            return True, "challenger_equal_structure_with_multiple_improvements"

    return False, "override_evidence_insufficient"


def compute_fullv2_guarded_selection(rows, full_selected_row, allow_feasible_selection=False):
    """Return (selected_row, decision_info) for FullV2.

    FullV2 is a conservative wrapper around ``ReplenishVerifier-Full``: it
    keeps Full's selected candidate unless a strong no-reference challenger
    justifies an override.
    """
    challenger = _pick_fullv2_challenger(rows)
    overridden, reason = should_override_full_selection(full_selected_row, challenger)

    selected = dict(challenger if overridden else (full_selected_row or challenger or rows[0]))

    decision_info = {
        "full_candidate_id": (full_selected_row or {}).get("candidate_id"),
        "challenger_candidate_id": (challenger or {}).get("candidate_id"),
        "overridden": bool(overridden),
        "override_reason": reason,
        "full_structure_score": _structure_score(full_selected_row) if full_selected_row else None,
        "challenger_structure_score": _structure_score(challenger) if challenger else None,
        "full_constraint_coverage": _constraint_coverage(full_selected_row) if full_selected_row else None,
        "challenger_constraint_coverage": _constraint_coverage(challenger) if challenger else None,
        "full_objective_term_coverage": _objective_term_coverage(full_selected_row) if full_selected_row else None,
        "challenger_objective_term_coverage": _objective_term_coverage(challenger) if challenger else None,
        "full_objective_consensus_score": float((full_selected_row or {}).get("objective_consensus_score", 0.0) or 0.0) if full_selected_row else None,
        "challenger_objective_consensus_score": float((challenger or {}).get("objective_consensus_score", 0.0) or 0.0) if challenger else None,
        "full_lp_health_score": _lp_health_score(full_selected_row) if full_selected_row else None,
        "challenger_lp_health_score": _lp_health_score(challenger) if challenger else None,
        "full_code_validity_score": _code_validity_score(full_selected_row) if full_selected_row else None,
        "challenger_code_validity_score": _code_validity_score(challenger) if challenger else None,
        "full_static_validation_score": _static_validation_score(full_selected_row) if full_selected_row else None,
        "challenger_static_validation_score": _static_validation_score(challenger) if challenger else None,
        "full_type_aware_hard_gate_score": _type_aware_hard_gate_score(full_selected_row) if full_selected_row else None,
        "challenger_type_aware_hard_gate_score": _type_aware_hard_gate_score(challenger) if challenger else None,
        "full_critical_missing_structures": _fullv2_missing_critical_structures(full_selected_row) if full_selected_row else [],
        "challenger_critical_missing_structures": _fullv2_missing_critical_structures(challenger) if challenger else [],
        "allow_feasible_selection": bool(allow_feasible_selection),
    }
    return selected, decision_info


def fullv2_guarded_decision_row(problem_id, full_selected_row, challenger_row, allow_feasible_selection=False):
    """Convenience wrapper that returns (selected_row, decision_info)."""
    return compute_fullv2_guarded_selection(
        [full_selected_row, challenger_row] if challenger_row is not None else [full_selected_row],
        full_selected_row,
        allow_feasible_selection=allow_feasible_selection,
    )
