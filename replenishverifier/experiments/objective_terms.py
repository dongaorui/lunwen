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


def expected_objective_terms(problem_type):
    return list(EXPECTED_OBJECTIVE_TERMS_BY_TYPE.get(problem_type or "", []))


def _haystack(row, parsed=None, generated_code=None):
    parts = [generated_code or row.get("generated_code", "") or row.get("generated_text", "") or ""]
    if parsed is not None:
        objective = getattr(parsed, "objective", None)
        variable_names = getattr(parsed, "variable_names", None)
        parts.append(str(objective or ""))
        if variable_names:
            parts.append(" ".join(str(name) for name in variable_names))
    lp_stats = row.get("lp_stats") or {}
    parts.append(str(lp_stats.get("objective", "")))
    return "\n".join(parts).lower()


def _detect(term, text):
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in TERM_PATTERNS.get(term, []))


def evaluate_objective_terms(row, parsed=None, generated_code=None):
    expected = expected_objective_terms(row.get("problem_type"))
    if not expected:
        return {
            "expected_objective_terms": [],
            "detected_objective_terms": [],
            "missing_objective_terms": [],
            "objective_term_coverage": None,
            "uses_reference_objective_for_objective_term_coverage": False,
        }
    text = _haystack(row, parsed=parsed, generated_code=generated_code)
    detected = [term for term in expected if _detect(term, text)]
    missing = [term for term in expected if term not in detected]
    return {
        "expected_objective_terms": expected,
        "detected_objective_terms": detected,
        "missing_objective_terms": missing,
        "objective_term_coverage": float(len(detected) / len(expected)),
        "uses_reference_objective_for_objective_term_coverage": False,
    }
