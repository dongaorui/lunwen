import ast
import re


PATTERNS = {
    "inventory_balance": re.compile(r"inventory|balance|stock", re.IGNORECASE),
    "capacity": re.compile(r"capacity|cap_|_cap|limit|resource", re.IGNORECASE),
    "shortage": re.compile(r"shortage|backlog|unmet", re.IGNORECASE),
    "binary_order": re.compile(r"Binary|cat\s*=\s*['\"]Binary['\"]|order_binary|setup|open_order", re.IGNORECASE),
    "big_m": re.compile(r"big_m|bigm|\bM\b|\*\s*y|y\s*\*", re.IGNORECASE),
    "fixed_order_cost": re.compile(r"fixed_order|setup_cost|fixed_cost|ordering_fixed", re.IGNORECASE),
}


OBJECTIVE_CONTEXT_PATTERNS = {
    "order_cost": re.compile(r"order_cost|ordering_cost|unit_order_cost|purchase_cost|procurement|order\s*\[|Q\s*\[", re.IGNORECASE),
    "holding_cost": re.compile(r"holding_cost|hold_cost|inventory_cost|holding|inventory\s*\[|I\s*\[", re.IGNORECASE),
    "shortage_cost": re.compile(r"shortage_cost|shortage_penalty|backlog_cost|unmet_penalty|unmet_cost|penalty_shortage", re.IGNORECASE),
    "fixed_order_cost": re.compile(r"fixed_order_cost|setup_cost|fixed_cost|ordering_fixed|setup\s*\[|order_binary\s*\[", re.IGNORECASE),
}


class _PulpModelVisitor(ast.NodeVisitor):
    def __init__(self):
        self.has_build_model = False
        self.has_pulp_problem = False
        self.has_objective = False
        self.has_constraints = False

    def visit_FunctionDef(self, node):
        if node.name == "build_model":
            self.has_build_model = True
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "LpProblem":
                self.has_pulp_problem = True
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Add):
            if isinstance(node.value, ast.Tuple) and len(node.value.elts) >= 2:
                self.has_constraints = True
            elif self.has_objective:
                self.has_constraints = True
            else:
                self.has_objective = True
        self.generic_visit(node)


def _base_result():
    return {
        "has_build_model": False,
        "has_pulp_problem": False,
        "has_objective": False,
        "has_constraints": False,
        "has_inventory_balance_pattern": False,
        "has_capacity_pattern": False,
        "has_shortage_pattern": False,
        "has_binary_order_pattern": False,
        "has_big_m_pattern": False,
        "has_fixed_order_cost_pattern": False,
        "static_validation_errors": [],
        "static_validation_score": 0.0,
    }


def _score(result):
    checks = [
        "has_build_model",
        "has_pulp_problem",
        "has_objective",
        "has_constraints",
    ]
    return sum(1.0 for key in checks if result[key]) / len(checks)


def _objective_has(term_key, code):
    return bool(OBJECTIVE_CONTEXT_PATTERNS[term_key].search(code or ""))


def _attach_type_aware_validation(result, problem_type, code):
    type_aware = _type_aware_checks(problem_type, code, result)
    result["type_aware_static_validation"] = type_aware
    result["type_aware_static_validation_score"] = float(type_aware["score"])
    result["type_aware_static_validation_errors"] = list(type_aware["missing_items"])
    return result


def _type_aware_checks(problem_type, code, result):
    checks = []

    def add(item_id, passed, feedback):
        checks.append({"id": item_id, "passed": bool(passed), "feedback": feedback})

    has_inventory = result.get("has_inventory_balance_pattern")
    has_capacity = result.get("has_capacity_pattern")
    has_shortage = result.get("has_shortage_pattern")
    has_binary = result.get("has_binary_order_pattern")
    has_big_m = result.get("has_big_m_pattern")
    has_fixed_cost = result.get("has_fixed_order_cost_pattern") or _objective_has("fixed_order_cost", code)
    has_shortage_cost = _objective_has("shortage_cost", code)
    has_order_cost = _objective_has("order_cost", code)
    has_holding_cost = _objective_has("holding_cost", code)

    if problem_type in {"single_item_multi_period", "single_item_multi_period_shortage", "multi_item_capacity", "fixed_order_cost_big_m"}:
        add("inventory_balance", has_inventory, "Add explicit inventory balance constraints linking inventory, orders, and demand across periods.")
    if problem_type == "multi_item_capacity":
        add("capacity_constraint", has_capacity, "Add per-period capacity/resource constraints across items.")
    if problem_type == "single_item_multi_period_shortage":
        add("shortage_variable", has_shortage, "Add shortage/backlog/unmet-demand variables.")
        add("shortage_cost_term", has_shortage_cost, "Include shortage penalty terms in the objective.")
    if problem_type == "fixed_order_cost_big_m":
        add("fixed_order_binary", has_binary, "Add binary order/setup variables.")
        add("big_m_linking", has_big_m, "Add Big-M linking constraints tying order quantities to binary setup/order variables.")
        add("fixed_order_cost_term", has_fixed_cost, "Include fixed order/setup cost terms in the objective.")
    if problem_type in {"single_item_multi_period", "single_item_multi_period_shortage", "multi_item_capacity", "fixed_order_cost_big_m"}:
        add("order_cost_term", has_order_cost, "Include ordering or purchase cost terms in the objective.")
        add("holding_cost_term", has_holding_cost, "Include holding or inventory cost terms in the objective.")

    missing = [f"missing_{item['id']}" for item in checks if not item["passed"]]
    passed = [item["id"] for item in checks if item["passed"]]
    feedback = [item["feedback"] for item in checks if not item["passed"]]
    score = float(len(passed) / len(checks)) if checks else 1.0
    hard_gate_failures = [item for item in missing if item in {
        "missing_inventory_balance",
        "missing_capacity_constraint",
        "missing_shortage_variable",
        "missing_shortage_cost_term",
        "missing_fixed_order_binary",
        "missing_big_m_linking",
        "missing_fixed_order_cost_term",
    }]
    hard_gate_score = float((len(checks) - len(hard_gate_failures)) / max(len(checks), 1)) if checks else 1.0
    return {
        "problem_type": problem_type,
        "checklist": checks,
        "passed_items": passed,
        "missing_items": missing,
        "repair_feedback": feedback,
        "score": score,
        "hard_gate_failures": hard_gate_failures,
        "hard_gate_score": hard_gate_score,
        "evidence": {
            "inventory_balance": bool(has_inventory),
            "capacity_constraint": bool(has_capacity),
            "shortage_variable": bool(has_shortage),
            "shortage_cost_term": bool(has_shortage_cost),
            "fixed_order_binary": bool(has_binary),
            "big_m_linking": bool(has_big_m),
            "fixed_order_cost_term": bool(has_fixed_cost),
            "order_cost_term": bool(has_order_cost),
            "holding_cost_term": bool(has_holding_cost),
        },
    }


def compute_static_validation(generated_code: str, problem_type: str | None = None) -> dict:
    code = generated_code or ""
    result = _base_result()
    if not code.strip():
        result["static_validation_errors"].append("empty_code")
        return _attach_type_aware_validation(result, problem_type, code)
    if "```" in code:
        result["static_validation_errors"].append("contains_markdown_fence")

    try:
        tree = ast.parse(code)
    except SyntaxError:
        result["static_validation_errors"].append("syntax_error")
        return _attach_type_aware_validation(result, problem_type, code)

    visitor = _PulpModelVisitor()
    visitor.visit(tree)
    result["has_build_model"] = visitor.has_build_model or "def build_model" in code
    result["has_pulp_problem"] = visitor.has_pulp_problem or "pulp.LpProblem" in code
    result["has_objective"] = visitor.has_objective or "prob +=" in code or "model +=" in code
    result["has_constraints"] = visitor.has_constraints or bool(re.search(r"(<=|>=|==).*,\s*['\"]", code))
    result["has_inventory_balance_pattern"] = bool(PATTERNS["inventory_balance"].search(code))
    result["has_capacity_pattern"] = bool(PATTERNS["capacity"].search(code))
    result["has_shortage_pattern"] = bool(PATTERNS["shortage"].search(code))
    result["has_binary_order_pattern"] = bool(PATTERNS["binary_order"].search(code))
    result["has_big_m_pattern"] = bool(PATTERNS["big_m"].search(code))
    result["has_fixed_order_cost_pattern"] = bool(PATTERNS["fixed_order_cost"].search(code))

    if not result["has_build_model"]:
        result["static_validation_errors"].append("missing_build_model")
    if not result["has_pulp_problem"]:
        result["static_validation_errors"].append("missing_pulp_lp_problem")
    if not result["has_objective"]:
        result["static_validation_errors"].append("missing_objective_surface")
    if not result["has_constraints"]:
        result["static_validation_errors"].append("missing_constraints_surface")

    result["static_validation_score"] = float(_score(result))
    return _attach_type_aware_validation(result, problem_type, code)
