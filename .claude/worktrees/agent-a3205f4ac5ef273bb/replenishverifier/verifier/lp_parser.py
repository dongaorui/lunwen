import re
from dataclasses import asdict, dataclass
from pathlib import Path


SECTION_NAMES = ["Minimize", "Maximize", "Subject To", "Bounds", "Generals", "Binaries", "End"]
AUTO_CONSTRAINT_RE = re.compile(r"^_C\d+$", re.IGNORECASE)


@dataclass
class ParsedLP:
    path: str
    sense: str
    objective: str
    constraints: dict
    constraint_names: list
    variable_names: list
    binary_variables: list
    bounds: list
    raw_text: str
    normalized_constraint_names: dict
    normalized_variable_names: dict
    constraint_concept_tags: dict
    variable_concept_tags: dict
    auto_named_constraints: list

    def to_dict(self):
        return asdict(self)


def normalize_symbol_name(name):
    """Normalize PuLP/LP symbols for weak matching without changing raw names."""
    normalized = str(name or "").strip().lower()
    normalized = normalized.replace("-", "_")
    normalized = normalized.replace("[", "_").replace("]", "")
    normalized = normalized.replace("(", "_").replace(")", "")
    normalized = normalized.replace(",", "_").replace(" ", "_")
    normalized = re.sub(r"__+", "_", normalized)
    return normalized.strip("_")


def is_auto_constraint_name(name):
    return AUTO_CONSTRAINT_RE.match(str(name or "")) is not None


def tag_symbol_concepts(name):
    """Return weak concept tags inferred from a symbol/name.

    These tags are intentionally auxiliary evidence: they improve robustness to
    descriptive names, but do not establish algebraic equivalence.
    """
    n = normalize_symbol_name(name)
    tags = set()
    if is_auto_constraint_name(name):
        tags.add("auto_named_constraint")
    if n == "q" or n.startswith("q_") or any(term in n for term in ["order", "purchase", "replenish"]):
        tags.add("order")
    if n == "i" or n.startswith("i_") or any(term in n for term in ["inventory", "stock", "onhand", "on_hand", "ending_inventory", "inv"]):
        tags.add("inventory")
    if n == "b" or n.startswith("b_") or any(term in n for term in ["shortage", "backlog", "backorder", "unmet", "lost_sales", "deficit"]):
        tags.add("shortage")
    if n == "y" or n.startswith("y_") or any(term in n for term in ["setup", "trigger", "indicator", "is_order", "open_order", "binary"]):
        tags.add("binary_order")
    if any(term in n for term in ["capacity", "cap", "limit", "resource"]):
        tags.add("capacity")
    if any(term in n for term in ["demand", "requirement", "sales"]):
        tags.add("demand")
    if any(term in n for term in ["balance", "flow", "recurrence", "conservation"]):
        tags.add("flow")
    if any(term in n for term in ["big_m", "bigm", "link"]):
        tags.add("big_m")
    if any(term in n for term in ["fixed", "setup", "ordering_cost", "order_cost"]):
        tags.add("fixed_cost")
    if "holding" in n:
        tags.add("holding_cost")
    if any(term in n for term in ["shortage_cost", "penalty", "backlog_cost"]):
        tags.add("shortage_cost")
    return sorted(tags)


def expression_variables(expr, variable_names):
    """Return parsed variable names that occur as whole LP tokens in expr."""
    out = []
    for name in variable_names:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", expr or ""):
            out.append(name)
    return out


def _get_section(text, section_name, next_names):
    pattern = rf"(?ims)^\s*{re.escape(section_name)}\s*$"
    match = re.search(pattern, text)
    if not match:
        return ""
    start = match.end()
    end = len(text)
    for next_name in next_names:
        next_match = re.search(rf"(?ims)^\s*{re.escape(next_name)}\s*$", text[start:])
        if next_match:
            end = start + next_match.start()
            break
    return text[start:end].strip()


def _parse_constraints(subject_text):
    constraints = {}
    current_name = None
    current_lines = []

    for raw in subject_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if ":" in line:
            if current_name is not None:
                constraints[current_name] = " ".join(current_lines).strip()
            name, expr = line.split(":", 1)
            current_name = name.strip()
            current_lines = [expr.strip()]
        elif current_name is not None:
            current_lines.append(line)
        else:
            # Non-PuLP LP fragments may omit names. Preserve them under a stable
            # synthetic auto name so downstream diagnostics can still inspect the
            # expression, but never treat the synthetic name as semantic evidence.
            current_name = f"_C{len(constraints) + 1}"
            current_lines = [line]

    if current_name is not None:
        constraints[current_name] = " ".join(current_lines).strip()

    return constraints


def _extract_names_from_expr(expr):
    tokens = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", expr)
    blacklist = {
        "Minimize", "Maximize", "Subject", "To", "Bounds", "Generals", "Binaries", "End",
        "OBJ", "obj", "total_cost", "free", "inf", "infinity",
    }
    names = []
    for token in tokens:
        if token in blacklist:
            continue
        if re.fullmatch(r"[eE]", token):
            continue
        names.append(token)
    return names


def parse_lp_text(text, path="<memory>"):
    sense = "minimize" if re.search(r"(?im)^\s*Minimize\s*$", text) else "maximize"
    objective = _get_section(text, "Minimize", ["Subject To", "Bounds", "Generals", "Binaries", "End"])
    if not objective:
        objective = _get_section(text, "Maximize", ["Subject To", "Bounds", "Generals", "Binaries", "End"])

    subject = _get_section(text, "Subject To", ["Bounds", "Generals", "Binaries", "End"])
    bounds_text = _get_section(text, "Bounds", ["Generals", "Binaries", "End"])
    binaries_text = _get_section(text, "Binaries", ["End"])

    constraints = _parse_constraints(subject)
    bounds = [line.strip() for line in bounds_text.splitlines() if line.strip()]

    binary_variables = []
    for line in binaries_text.splitlines():
        line = line.strip()
        if line:
            binary_variables.extend(_extract_names_from_expr(line))

    variable_set = set()
    for name in _extract_names_from_expr(objective):
        variable_set.add(name)
    for expr in constraints.values():
        for name in _extract_names_from_expr(expr):
            variable_set.add(name)
    for line in bounds:
        for name in _extract_names_from_expr(line):
            variable_set.add(name)
    for name in binary_variables:
        variable_set.add(name)

    for constraint_name in constraints:
        variable_set.discard(constraint_name)

    constraint_names = sorted(constraints.keys())
    variable_names = sorted(variable_set)
    normalized_constraint_names = {name: normalize_symbol_name(name) for name in constraint_names}
    normalized_variable_names = {name: normalize_symbol_name(name) for name in variable_names}

    return ParsedLP(
        path=str(path),
        sense=sense,
        objective=objective,
        constraints=constraints,
        constraint_names=constraint_names,
        variable_names=variable_names,
        binary_variables=sorted(set(binary_variables)),
        bounds=bounds,
        raw_text=text,
        normalized_constraint_names=normalized_constraint_names,
        normalized_variable_names=normalized_variable_names,
        constraint_concept_tags={name: tag_symbol_concepts(name) for name in constraint_names},
        variable_concept_tags={name: tag_symbol_concepts(name) for name in variable_names},
        auto_named_constraints=[name for name in constraint_names if is_auto_constraint_name(name)],
    )


def parse_lp_file(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    return parse_lp_text(text, path=str(path))
