import re


EXPECTED_OBJECTIVE_TERMS_BY_TYPE = {
    "single_period_newsvendor": ["ordering_cost", "holding_cost", "shortage_cost"],
    "single_item_multi_period": ["ordering_cost", "holding_cost"],
    "single_item_multi_period_shortage": ["ordering_cost", "holding_cost", "shortage_cost"],
    "multi_item_capacity": ["ordering_cost", "holding_cost"],
    "fixed_order_cost_big_m": ["ordering_cost", "holding_cost", "fixed_order_cost"],
}

TERM_PATTERNS = {
    "ordering_cost": [r"unit[_ ]?order", r"order[_ ]?cost", r"ordering[_ ]?cost", r"purchase[_ ]?cost", r"\bQ\b", r"Q_"],
    "holding_cost": [r"holding[_ ]?cost", r"hold[_ ]?cost", r"inventory[_ ]?cost", r"\bI\b", r"I_"],
    "shortage_cost": [r"shortage[_ ]?cost", r"backorder[_ ]?cost", r"penalty[_ ]?cost", r"\bS\b", r"S_", r"short"],
    "fixed_order_cost": [r"fixed[_ ]?order", r"setup[_ ]?cost", r"fixed[_ ]?cost", r"\bY\b", r"Y_", r"binary"],
}

LP_VARIABLE_FAMILY_PATTERNS = {
    "ordering_cost": ["q", "order", "order_quantity", "quantity_ordered", "purchase", "replenish"],
    "holding_cost": ["i", "inventory", "stock", "onhand", "on_hand", "ending_inventory", "inv"],
    "shortage_cost": ["b", "s", "shortage", "backlog", "backorder", "unmet", "lost_sales", "deficit"],
    "fixed_order_cost": ["y", "binary", "setup", "open_order", "order_trigger", "trigger", "indicator", "is_order"],
}


def expected_objective_terms(problem_type):
    return list(EXPECTED_OBJECTIVE_TERMS_BY_TYPE.get(problem_type or "", []))


def _haystack(row, parsed=None, generated_code=None):
    parts = [generated_code or row.get("generated_code", "") or row.get("generated_text", "") or ""]
    if parsed is not None:
        objective = getattr(parsed, "objective", None)
        variable_names = getattr(parsed, "variable_names", None)
        if isinstance(parsed, dict):
            objective = parsed.get("objective", objective)
            variable_names = parsed.get("variable_names", variable_names)
        parts.append(str(objective or ""))
        if variable_names:
            parts.append(" ".join(str(name) for name in variable_names))
    lp_stats = row.get("lp_stats") or {}
    parts.append(str(lp_stats.get("objective", "")))
    return "\n".join(parts).lower()


def _detect(term, text):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in TERM_PATTERNS.get(term, []))


def _normalize_name(name):
    normalized = str(name or "").strip().lower()
    normalized = normalized.replace("-", "_")
    normalized = normalized.replace("[", "_").replace("]", "")
    normalized = normalized.replace("(", "_").replace(")", "")
    normalized = normalized.replace(",", "_").replace(" ", "_")
    normalized = re.sub(r"__+", "_", normalized)
    return normalized.strip("_")


def _term_matches_variable_family(term, variable_name):
    name = _normalize_name(variable_name)
    aliases = LP_VARIABLE_FAMILY_PATTERNS.get(term, [])
    for alias in aliases:
        alias = _normalize_name(alias)
        if name == alias or name.startswith(f"{alias}_") or f"_{alias}_" in f"_{name}_":
            return True
    return False


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coefficient_before_variable(objective_text, variable_name):
    pattern = re.compile(
        rf"(?P<prefix>(?:^|[+\-])\s*(?:\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?\s*(?:\*)?\s*)?)"
        rf"(?<![A-Za-z0-9_]){re.escape(variable_name)}(?![A-Za-z0-9_])"
    )
    match = pattern.search(objective_text or "")
    if not match:
        return None
    prefix = (match.group("prefix") or "").strip()
    sign = -1.0 if prefix.startswith("-") else 1.0
    number_match = re.search(r"\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?", prefix)
    if not number_match:
        return sign
    return sign * float(number_match.group(0))


def _parsed_objective_coefficients(parsed):
    if parsed is None:
        return None
    objective = getattr(parsed, "objective", None)
    variable_names = getattr(parsed, "variable_names", None)
    if isinstance(parsed, dict):
        objective = parsed.get("objective", objective)
        variable_names = parsed.get("variable_names", variable_names)

    if isinstance(objective, dict):
        return {str(name): float(coef) for name, coef in objective.items() if _as_float(coef) is not None}

    if isinstance(objective, (list, tuple)):
        out = {}
        for item in objective:
            if isinstance(item, (list, tuple)) and len(item) == 2 and _as_float(item[1]) is not None:
                out[str(item[0])] = float(item[1])
        if out:
            return out

    if isinstance(objective, str) and variable_names:
        out = {}
        for name in variable_names:
            coef = _coefficient_before_variable(objective, str(name))
            if coef is not None:
                out[str(name)] = float(coef)
        return out

    return None


def _lp_coefficient_term_detection(expected, parsed):
    coefficients = _parsed_objective_coefficients(parsed)
    if coefficients is None:
        return None, [], []
    nonzero_variables = [name for name, coef in coefficients.items() if abs(float(coef or 0.0)) > 1e-12]
    detected = [
        term for term in expected
        if any(_term_matches_variable_family(term, variable_name) for variable_name in nonzero_variables)
    ]
    missing = [term for term in expected if term not in detected]
    coverage = float(len(detected) / len(expected)) if expected else None
    return coverage, detected, missing


def evaluate_objective_terms(row, parsed=None, generated_code=None):
    expected = expected_objective_terms(row.get("problem_type"))
    if not expected:
        return {
            "expected_objective_terms": [],
            "detected_objective_terms": [],
            "missing_objective_terms": [],
            "surface_detected_objective_terms": [],
            "surface_missing_objective_terms": [],
            "lp_detected_objective_terms": [],
            "lp_missing_objective_terms": [],
            "objective_term_surface_coverage": None,
            "objective_term_lp_coefficient_coverage": None,
            "objective_term_coverage": None,
            "uses_reference_objective_for_objective_term_coverage": False,
        }
    text = _haystack(row, parsed=parsed, generated_code=generated_code)
    surface_detected = [term for term in expected if _detect(term, text)]
    surface_missing = [term for term in expected if term not in surface_detected]
    surface_coverage = float(len(surface_detected) / len(expected))

    lp_coverage, lp_detected, lp_missing = _lp_coefficient_term_detection(expected, parsed)
    final_coverage = surface_coverage if lp_coverage is None else min(surface_coverage, lp_coverage)
    final_detected = surface_detected if lp_coverage is None else [term for term in surface_detected if term in lp_detected]
    final_missing = [term for term in expected if term not in final_detected]

    return {
        "expected_objective_terms": expected,
        "detected_objective_terms": final_detected,
        "missing_objective_terms": final_missing,
        "surface_detected_objective_terms": surface_detected,
        "surface_missing_objective_terms": surface_missing,
        "lp_detected_objective_terms": lp_detected,
        "lp_missing_objective_terms": lp_missing,
        "objective_term_surface_coverage": surface_coverage,
        "objective_term_lp_coefficient_coverage": lp_coverage,
        "objective_term_coverage": final_coverage,
        "uses_reference_objective_for_objective_term_coverage": False,
    }
