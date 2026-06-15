import re
from dataclasses import asdict, dataclass, field

from replenishverifier.benchmark.schemas import STRUCTURE_KEYS
from replenishverifier.data.structure_schema import split_expected_structures
from replenishverifier.verifier.lp_graph import LPStructureGraph
from replenishverifier.verifier.lp_parser import (
    expression_variables,
    is_auto_constraint_name,
    normalize_symbol_name,
    tag_symbol_concepts,
)


STRUCTURE_DESCRIPTIONS = {
    "inventory_balance": "inventory balance constraints",
    "order_variable": "order quantity variable Q",
    "inventory_variable": "inventory variable I",
    "shortage_variable": "shortage/backorder variable B",
    "capacity_constraint": "capacity constraint",
    "binary_order_variable": "binary order trigger variable Y",
    "big_m_constraint": "Big-M linking constraint Q <= M * Y",
    "lead_time": "lead-time structure",
    "holding_cost": "holding cost term",
    "shortage_cost": "shortage cost term",
    "fixed_order_cost": "fixed ordering cost term",
}


REPAIR_HINTS = {
    "inventory_balance": "Add inventory-flow constraints such as I[t] = I[t-1] + Q[t] - demand[t]; with backlogs, use net inventory I[t] - B[t]. Ensure the expression contains inventory state variables and order/demand terms, not only an inventory_balance name.",
    "order_variable": "Add nonnegative order quantity variables, e.g. Q[t] or Q[i,t].",
    "inventory_variable": "Add nonnegative inventory state variables, e.g. I[t] or I[i,t].",
    "shortage_variable": "Add shortage/backlog variables, e.g. B[t] or B[i,t], and use them in the objective or balance/demand constraints.",
    "capacity_constraint": "Add capacity constraints, e.g. sum_i volume[i] * I[i,t] <= capacity, with an inequality over real decision variables.",
    "binary_order_variable": "Add binary setup/order-trigger variables, e.g. Y[t] in {0,1}.",
    "big_m_constraint": "Add linking constraints such as Q[t] <= M * Y[t] with a numerically reasonable M derived from demand/capacity bounds when possible.",
    "lead_time": "Represent delayed arrivals in the inventory balance, e.g. Q[t-L].",
    "holding_cost": "Include holding_cost * I[t] terms in the objective.",
    "shortage_cost": "Include shortage_cost * B[t] terms in the objective.",
    "fixed_order_cost": "Include fixed_order_cost * Y[t] terms in the objective; declaring Y alone is not enough.",
}


RULE_SCORE_BY_EVIDENCE = {
    "none": 0.0,
    "name_only": 0.4,
    "graph_supported": 0.6,
    "expression_supported": 0.75,
    "expression_and_graph": 0.85,
    "strong": 1.0,
}

PASS_SCORE_THRESHOLD = 0.75


@dataclass
class RuleCertificate:
    rule_name: str
    required: bool
    passed: bool
    score: float
    evidence_strength: str
    matched_names: list = field(default_factory=list)
    matched_expressions: list = field(default_factory=list)
    index_consistency: dict = field(default_factory=dict)
    magnitude_check: dict = field(default_factory=dict)
    missing_reason: str = ""
    repair_hint: str = ""
    optional: bool = False
    evidence: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class StructureCheckResult:
    expected: dict
    detected: dict
    passed: dict
    missing: list
    extra_detected: list
    structure_score: float
    messages: list
    certificates: list
    optional_detected: dict
    weak_evidence: dict
    required_structures: list
    optional_structures: list
    forbidden_structures: list
    low_score_required: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


ROLE_ALIASES = {
    "order": ["Q", "order", "order_qty", "order_quantity", "purchase", "replenish", "replenishment"],
    "inventory": ["I", "inventory", "stock", "onhand", "on_hand", "ending_inventory", "inv"],
    "shortage": ["B", "shortage", "backlog", "backorder", "unmet", "lost_sales", "deficit"],
    "binary_order": ["Y", "setup", "order_flag", "order_indicator", "is_order", "open_order", "binary_order", "trigger"],
}


CONSTRAINT_NAME_TERMS = {
    "inventory_balance": ["inventory_balance", "balance", "flow", "recurrence", "conservation", "stock_flow"],
    "capacity_constraint": ["capacity", "cap_", "limit", "resource"],
    "big_m_constraint": ["big_m", "bigm", "link", "setup"],
    "lead_time": ["lead_time", "leadtime", "arrival"],
}


def _normalize(name):
    return normalize_symbol_name(name)


def _contains_var(expr, name):
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", expr or "") is not None


def _has_prefix(names, prefix):
    prefix_norm = _normalize(prefix)
    return any(_normalize(name) == prefix_norm or _normalize(name).startswith(prefix_norm + "_") for name in names)


def _has_role(names, role):
    role_tag = "binary_order" if role == "binary_order" else role
    aliases = ROLE_ALIASES[role]
    for name in names:
        tags = tag_symbol_concepts(name)
        if role_tag in tags:
            return True
        normalized = _normalize(name)
        for alias in aliases:
            alias_norm = _normalize(alias)
            if normalized == alias_norm or normalized.startswith(alias_norm + "_") or alias_norm in normalized:
                return True
    return False


def _objective_has_var(parsed, prefix):
    return any(_contains_var(parsed.objective, variable) for variable in parsed.variable_names if _has_prefix([variable], prefix))


def _objective_has_role(parsed, role):
    return any(_contains_var(parsed.objective, variable) for variable in parsed.variable_names if _has_role([variable], role))


def _matching_vars(names, role=None, prefix=None):
    out = []
    for name in names:
        if prefix and _has_prefix([name], prefix):
            out.append(name)
        elif role and _has_role([name], role):
            out.append(name)
    return out


def _semantic_constraint_names(parsed, terms):
    matched = []
    for cname in parsed.constraint_names:
        if is_auto_constraint_name(cname):
            continue
        normalized = _normalize(cname)
        if any(term in normalized for term in terms):
            matched.append(cname)
    return matched


def _constraint_evidence(parsed, terms, limit=5):
    evidence = []
    for cname, expr in parsed.constraints.items():
        haystack = f"{'' if is_auto_constraint_name(cname) else cname} {expr}".lower()
        if any(term in haystack for term in terms):
            evidence.append({"constraint": cname, "expr": expr})
    return evidence[:limit]


def _objective_evidence(parsed, variables, limit=8):
    return [{"variable": v, "objective_excerpt": parsed.objective[:300]} for v in variables if _contains_var(parsed.objective, v)][:limit]


def _expr_has_relation(expr, relation):
    expr = expr or ""
    if relation == "eq":
        return "=" in expr and "<=" not in expr and ">=" not in expr
    if relation == "ineq":
        return "<=" in expr or ">=" in expr
    return False


def _numbers_from_name(name):
    return [int(x) for x in re.findall(r"\d+", str(name))]


def _family_key(name):
    return re.sub(r"_?\d+", "", _normalize(name))


def _has_adjacent_period(vars_):
    by_family = {}
    for var in vars_:
        nums = _numbers_from_name(var)
        if not nums:
            continue
        by_family.setdefault(_family_key(var), set()).add(nums[-1])
    for values in by_family.values():
        if any((value - 1) in values or (value + 1) in values for value in values):
            return True
    return False


def _demand_like_terms(expr):
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", expr or "")
    return [tok for tok in tokens if "demand" in _normalize(tok) or _normalize(tok).startswith("d_") or _normalize(tok) == "d"]


def check_inventory_balance_index_consistency(expr: str, inventory_vars: list[str]) -> dict:
    """Lightweight inventory-balance index heuristic, not algebraic proof."""
    expr = expr or ""
    occurrences = []
    for var in inventory_vars:
        if _contains_var(expr, var):
            count = len(re.findall(rf"(?<![A-Za-z0-9_]){re.escape(var)}(?![A-Za-z0-9_])", expr))
            occurrences.extend([var] * count)
    unique_inventory = sorted(set(occurrences))
    order_terms = [tok for tok in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", expr) if _has_role([tok], "order")]
    shortage_terms = [tok for tok in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", expr) if _has_role([tok], "shortage")]
    demand_terms = _demand_like_terms(expr)

    evidence = []
    warnings = []
    confidence = 0.35

    if len(unique_inventory) >= 2:
        confidence += 0.25
        evidence.append("multiple_inventory_state_variables")
    elif len(unique_inventory) == 1:
        warnings.append("only_one_inventory_state_variable_in_balance_expression")
    else:
        warnings.append("no_inventory_state_variable_in_expression")

    if _has_adjacent_period(unique_inventory):
        confidence += 0.20
        evidence.append("adjacent_inventory_periods_detected")
    elif len(unique_inventory) >= 2:
        evidence.append("repeated_inventory_family_without_clear_adjacent_period")

    if len(occurrences) > len(unique_inventory):
        warnings.append("same_inventory_variable_repeated; possible self-cancellation such as I_t - I_t")
        confidence -= 0.20

    if order_terms:
        confidence += 0.10
        evidence.append("order_like_term_present")
    if demand_terms or shortage_terms:
        confidence += 0.10
        evidence.append("demand_or_shortage_like_term_present")

    if re.search(r"\+\s*(demand|D_|d_)\w*", expr):
        warnings.append("demand_like_term_has_positive_sign_in_normalized_zero-form; verify algebraic sign manually")

    confidence = max(0.0, min(confidence, 1.0))
    return {
        "passed": confidence >= 0.65,
        "confidence": float(confidence),
        "evidence": evidence,
        "warnings": warnings,
        "inventory_variables": unique_inventory,
        "order_terms": sorted(set(order_terms)),
        "demand_terms": sorted(set(demand_terms)),
        "shortage_terms": sorted(set(shortage_terms)),
    }


def _linear_coefficients(expr):
    cleaned = (expr or "").replace("-", "+-")
    coeffs = []
    for part in cleaned.split("+"):
        part = part.strip()
        if not part:
            continue
        if re.search(r"\b[A-Za-z_]", part):
            match = re.match(r"^([+-]?\s*\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*\*?\s*[A-Za-z_]", part)
            if match:
                coeffs.append(abs(float(match.group(1).replace(" ", ""))))
            else:
                coeffs.append(1.0)
    return [c for c in coeffs if c > 0]


def check_big_m_magnitude(expr: str, variable_bounds: dict | None = None) -> dict:
    """Optional weak Big-M magnitude check.

    TODO: replace this coefficient-ratio heuristic with bound-aware tightening when
    reliable variable bounds are available from richer LP/MPS parsing.
    """
    coeffs = _linear_coefficients(expr)
    if not coeffs:
        return {
            "has_large_coefficient": False,
            "candidate_M": None,
            "confidence": 0.0,
            "warning": "no_numeric_coefficients_found; magnitude evidence unavailable",
            "todo": "bound-aware Big-M validation is future work",
        }
    max_coeff = max(coeffs)
    others = [c for c in coeffs if c != max_coeff] or [1.0]
    baseline = max(max(others), 1.0)
    ratio = max_coeff / baseline
    warning = ""
    confidence = 0.35
    has_large = ratio >= 10.0
    if ratio >= 100.0:
        confidence = 0.85
    elif ratio >= 10.0:
        confidence = 0.70
    elif max_coeff < 10.0:
        warning = "candidate_M_is_small; verify that the link does not incorrectly cap feasible orders"
    else:
        warning = "largest_coefficient_not_much_larger_than_other_coefficients; Big-M magnitude evidence is weak"
    return {
        "has_large_coefficient": bool(has_large),
        "candidate_M": max_coeff,
        "coefficient_ratio": float(ratio),
        "confidence": float(confidence),
        "warning": warning,
        "todo": "bound-aware Big-M validation is future work",
    }


def _rule_score(strength):
    return RULE_SCORE_BY_EVIDENCE.get(strength, 0.0)


def _make_cert(rule_name, required=False, optional=False, strength="none", matched_names=None,
               matched_expressions=None, index_consistency=None, magnitude_check=None,
               missing_reason="", repair_hint=""):
    score = _rule_score(strength)
    passed = score >= PASS_SCORE_THRESHOLD
    evidence = []
    for name in matched_names or []:
        evidence.append({"name": name})
    evidence.extend(matched_expressions or [])
    if index_consistency:
        evidence.append({"index_consistency": index_consistency})
    if magnitude_check:
        evidence.append({"magnitude_check": magnitude_check})
    if not missing_reason and not passed:
        missing_reason = f"Required structure has insufficient evidence: {STRUCTURE_DESCRIPTIONS.get(rule_name, rule_name)}."
    if not repair_hint and not passed:
        repair_hint = REPAIR_HINTS.get(rule_name, f"Add missing structure: {rule_name}.")
    return RuleCertificate(
        rule_name=rule_name,
        required=required,
        optional=optional,
        passed=passed,
        score=float(score),
        evidence_strength=strength,
        matched_names=matched_names or [],
        matched_expressions=matched_expressions or [],
        index_consistency=index_consistency or {},
        magnitude_check=magnitude_check or {},
        missing_reason="" if passed else missing_reason,
        repair_hint="" if passed else repair_hint,
        evidence=evidence,
    )


def _vars_used_anywhere(parsed, vars_):
    text = "\n".join([parsed.objective or "", *parsed.constraints.values()])
    return [v for v in vars_ if _contains_var(text, v)]


def _constraint_vars(parsed, cname):
    return expression_variables(parsed.constraints.get(cname, ""), parsed.variable_names)


def _build_inventory_balance_cert(parsed, weak_evidence, required, optional):
    names = _semantic_constraint_names(parsed, CONSTRAINT_NAME_TERMS["inventory_balance"])
    inventory_vars = _matching_vars(parsed.variable_names, role="inventory", prefix="I")
    best_expr = None
    best_index = {}
    best_strength = "name_only" if names else "none"

    for cname, expr in parsed.constraints.items():
        vars_in_expr = _constraint_vars(parsed, cname)
        inv_in_expr = [v for v in vars_in_expr if _has_role([v], "inventory")]
        has_order = any(_has_role([v], "order") for v in vars_in_expr)
        has_shortage = any(_has_role([v], "shortage") for v in vars_in_expr)
        has_demand = bool(_demand_like_terms(expr))
        has_equal = _expr_has_relation(expr, "eq")
        if inv_in_expr and has_equal and (has_order or has_demand or has_shortage):
            idx = check_inventory_balance_index_consistency(expr, inventory_vars)
            expr_ev = {"constraint": cname, "expr": expr, "variables": vars_in_expr[:12]}
            strength = "expression_supported"
            if idx.get("passed"):
                strength = "expression_and_graph"
            if names and idx.get("passed") and (has_order or has_demand):
                strength = "strong"
            if _rule_score(strength) > _rule_score(best_strength):
                best_strength = strength
                best_expr = expr_ev
                best_index = idx

    graph = weak_evidence.get("inventory_recurrence_candidates", {})
    if best_strength == "none" and graph.get("found"):
        best_strength = "graph_supported"
    elif best_strength == "name_only" and graph.get("found"):
        best_strength = "graph_supported"
    matched = [best_expr] if best_expr else []
    if graph.get("found") and best_strength in {"graph_supported", "expression_and_graph", "strong"}:
        matched.append({"weak_detector": graph.get("detector"), "confidence": graph.get("confidence"), "evidence": graph.get("evidence")})
    return _make_cert("inventory_balance", required, optional, best_strength, names, matched, best_index)


def _build_big_m_cert(parsed, weak_evidence, required, optional):
    names = _semantic_constraint_names(parsed, CONSTRAINT_NAME_TERMS["big_m_constraint"])
    order_vars = set(_matching_vars(parsed.variable_names, role="order", prefix="Q")) - set(parsed.binary_variables)
    binary_vars = set(_matching_vars(parsed.binary_variables, role="binary_order", prefix="Y"))
    best_strength = "name_only" if names else "none"
    best_expr = None
    best_mag = {}

    for cname, expr in parsed.constraints.items():
        if "<=" not in expr:
            continue
        vars_in_expr = _constraint_vars(parsed, cname)
        has_order = any(v in order_vars for v in vars_in_expr)
        has_binary = any(v in binary_vars for v in vars_in_expr)
        if has_order and has_binary:
            mag = check_big_m_magnitude(expr)
            strength = "expression_supported"
            if mag.get("has_large_coefficient") or names:
                strength = "strong" if names else "expression_and_graph"
            if _rule_score(strength) > _rule_score(best_strength):
                best_strength = strength
                best_expr = {"constraint": cname, "expr": expr, "variables": vars_in_expr[:12]}
                best_mag = mag

    graph = weak_evidence.get("big_m_like_constraints", {})
    if best_strength == "none" and graph.get("found"):
        best_strength = "graph_supported"
    elif best_strength == "name_only" and graph.get("found"):
        best_strength = "graph_supported"
    matched = [best_expr] if best_expr else []
    if graph.get("found") and best_strength in {"graph_supported", "expression_and_graph", "strong"}:
        matched.append({"weak_detector": graph.get("detector"), "confidence": graph.get("confidence"), "evidence": graph.get("evidence")})
    return _make_cert("big_m_constraint", required, optional, best_strength, names, matched, magnitude_check=best_mag)


def _build_capacity_cert(parsed, required, optional):
    names = _semantic_constraint_names(parsed, CONSTRAINT_NAME_TERMS["capacity_constraint"])
    best_strength = "name_only" if names else "none"
    best_expr = None
    for cname, expr in parsed.constraints.items():
        vars_in_expr = _constraint_vars(parsed, cname)
        expr_tags = set(tag_symbol_concepts(cname)) if not is_auto_constraint_name(cname) else set()
        if any(term in _normalize(expr) for term in ["capacity", "cap", "limit", "resource"]):
            expr_tags.add("capacity")
        has_ineq = _expr_has_relation(expr, "ineq")
        decision_like = [v for v in vars_in_expr if any(tag in tag_symbol_concepts(v) for tag in ["order", "inventory", "shortage"])]
        if has_ineq and ("capacity" in expr_tags or cname in names) and decision_like:
            strength = "strong" if len(decision_like) >= 2 else "expression_supported"
            if _rule_score(strength) > _rule_score(best_strength):
                best_strength = strength
                best_expr = {"constraint": cname, "expr": expr, "variables": vars_in_expr[:12], "aggregation_count": len(decision_like)}
    return _make_cert("capacity_constraint", required, optional, best_strength, names, [best_expr] if best_expr else [])


def _build_fixed_order_cost_cert(parsed, weak_evidence, required, optional):
    binaries = _matching_vars(parsed.binary_variables, role="binary_order", prefix="Y")
    objective_vars = [v for v in binaries if _contains_var(parsed.objective, v)]
    names = objective_vars
    if not objective_vars:
        graph = weak_evidence.get("fixed_cost_binary_terms", {})
        strength = "graph_supported" if graph.get("found") else "none"
        matched = [{"weak_detector": graph.get("detector"), "confidence": graph.get("confidence"), "evidence": graph.get("evidence")}] if graph.get("found") else []
        return _make_cert("fixed_order_cost", required, optional, strength, names, matched)
    semantic = any("fixed_cost" in tag_symbol_concepts(v) or "binary_order" in tag_symbol_concepts(v) for v in objective_vars)
    objective_norm = _normalize(parsed.objective)
    semantic = semantic or any(term in objective_norm for term in ["fixed", "setup", "order"])
    strength = "strong" if semantic else "expression_supported"
    return _make_cert("fixed_order_cost", required, optional, strength, names, _objective_evidence(parsed, objective_vars))


def _build_shortage_variable_cert(parsed, required, optional):
    shortage_vars = _matching_vars(parsed.variable_names, role="shortage", prefix="B")
    used = _vars_used_anywhere(parsed, shortage_vars)
    if not shortage_vars:
        strength = "none"
    elif used:
        in_objective = any(_contains_var(parsed.objective, v) for v in shortage_vars)
        in_balance = any(any(_contains_var(expr, v) for v in shortage_vars) and any(term in _normalize(c) for term in ["balance", "demand", "flow", "satisfaction"]) for c, expr in parsed.constraints.items())
        strength = "strong" if in_objective or in_balance else "expression_supported"
    else:
        strength = "name_only"
    matched_exprs = []
    for cname, expr in parsed.constraints.items():
        if any(_contains_var(expr, v) for v in shortage_vars):
            matched_exprs.append({"constraint": cname, "expr": expr})
    matched_exprs.extend(_objective_evidence(parsed, shortage_vars))
    return _make_cert("shortage_variable", required, optional, strength, shortage_vars[:10], matched_exprs[:8])


def _build_simple_variable_cert(rule_name, parsed, required, optional, role, prefix, binary=False):
    names = _matching_vars(parsed.binary_variables if binary else parsed.variable_names, role=role, prefix=prefix)
    strength = "expression_supported" if names else "none"
    return _make_cert(rule_name, required, optional, strength, names[:10], [])


def _build_cost_cert(rule_name, parsed, required, optional, role, prefix):
    vars_ = _matching_vars(parsed.variable_names, role=role, prefix=prefix)
    objective_vars = [v for v in vars_ if _contains_var(parsed.objective, v)]
    strength = "expression_supported" if objective_vars else ("name_only" if vars_ else "none")
    return _make_cert(rule_name, required, optional, strength, objective_vars or vars_[:10], _objective_evidence(parsed, objective_vars))


def _build_lead_time_cert(parsed, required, optional):
    names = _semantic_constraint_names(parsed, CONSTRAINT_NAME_TERMS["lead_time"])
    exprs = _constraint_evidence(parsed, ["lead_time", "leadtime", "arrival"])
    strength = "expression_supported" if exprs else ("name_only" if names else "none")
    return _make_cert("lead_time", required, optional, strength, names, exprs)


def build_rule_certificates(parsed, expected, required_structures, optional_structures, weak_evidence):
    required_set = set(required_structures)
    optional_set = set(optional_structures)
    certs = []
    for rule_name in STRUCTURE_KEYS:
        required = rule_name in required_set
        optional = rule_name in optional_set and not required
        if rule_name == "inventory_balance":
            cert = _build_inventory_balance_cert(parsed, weak_evidence, required, optional)
        elif rule_name == "big_m_constraint":
            cert = _build_big_m_cert(parsed, weak_evidence, required, optional)
        elif rule_name == "capacity_constraint":
            cert = _build_capacity_cert(parsed, required, optional)
        elif rule_name == "fixed_order_cost":
            cert = _build_fixed_order_cost_cert(parsed, weak_evidence, required, optional)
        elif rule_name == "shortage_variable":
            cert = _build_shortage_variable_cert(parsed, required, optional)
        elif rule_name == "order_variable":
            cert = _build_simple_variable_cert(rule_name, parsed, required, optional, "order", "Q")
        elif rule_name == "inventory_variable":
            cert = _build_simple_variable_cert(rule_name, parsed, required, optional, "inventory", "I")
        elif rule_name == "binary_order_variable":
            cert = _build_simple_variable_cert(rule_name, parsed, required, optional, "binary_order", "Y", binary=True)
        elif rule_name == "holding_cost":
            cert = _build_cost_cert(rule_name, parsed, required, optional, "inventory", "I")
        elif rule_name == "shortage_cost":
            cert = _build_cost_cert(rule_name, parsed, required, optional, "shortage", "B")
        elif rule_name == "lead_time":
            cert = _build_lead_time_cert(parsed, required, optional)
        else:
            cert = _make_cert(rule_name, required, optional)
        certs.append(cert.to_dict())
    return certs


def detect_structures(parsed):
    graph = LPStructureGraph(parsed)
    weak = graph.weak_evidence()
    required_structures = list(STRUCTURE_KEYS)
    certificates = build_rule_certificates(parsed, {}, required_structures, [], weak)
    return {cert["rule_name"]: cert["score"] >= PASS_SCORE_THRESHOLD for cert in certificates}


def build_structure_certificate(parsed, expected, detected, required_structures, optional_structures, weak_evidence):
    # `detected` is accepted for backward compatibility; certificates are rebuilt
    # from evidence so each rule can carry score/evidence_strength details.
    return build_rule_certificates(parsed, expected, required_structures, optional_structures, weak_evidence)


def check_structures(parsed, expected, problem_type=None):
    graph = LPStructureGraph(parsed)
    weak_evidence = graph.weak_evidence()
    required_structures, optional_structures, forbidden_structures = split_expected_structures(expected, problem_type=problem_type)
    certificates = build_rule_certificates(parsed, expected or {}, required_structures, optional_structures, weak_evidence)
    cert_by_rule = {cert["rule_name"]: cert for cert in certificates}

    detected = {key: cert_by_rule[key]["score"] >= PASS_SCORE_THRESHOLD for key in STRUCTURE_KEYS}
    passed = {}
    missing = []
    low_score_required = []
    messages = []

    for key in STRUCTURE_KEYS:
        cert = cert_by_rule[key]
        if key in required_structures:
            ok = cert["score"] >= PASS_SCORE_THRESHOLD
            passed[key] = ok
            if not ok:
                missing.append(key)
                low_score_required.append({
                    "rule_name": key,
                    "score": cert["score"],
                    "evidence_strength": cert["evidence_strength"],
                    "repair_hint": cert["repair_hint"],
                })
                messages.append(
                    f"Missing or weak {STRUCTURE_DESCRIPTIONS.get(key, key)} "
                    f"(score={cert['score']:.2f}, evidence={cert['evidence_strength']})."
                )
        else:
            passed[key] = True

    extra_detected = [key for key, value in detected.items() if value and key not in required_structures and key not in optional_structures]
    optional_detected = {key: bool(detected.get(key, False)) for key in optional_structures}

    required_scores = [cert_by_rule[key]["score"] for key in required_structures]
    structure_score = sum(required_scores) / len(required_scores) if required_scores else 1.0

    return StructureCheckResult(
        expected=dict(expected or {}),
        detected=detected,
        passed=passed,
        missing=missing,
        extra_detected=extra_detected,
        structure_score=float(structure_score),
        messages=messages,
        certificates=certificates,
        optional_detected=optional_detected,
        weak_evidence=weak_evidence,
        required_structures=list(required_structures),
        optional_structures=list(optional_structures),
        forbidden_structures=list(forbidden_structures),
        low_score_required=low_score_required,
    )
