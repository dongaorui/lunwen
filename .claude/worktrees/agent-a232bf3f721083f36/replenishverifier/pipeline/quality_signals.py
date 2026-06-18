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


def compute_static_validation(generated_code: str, problem_type: str | None = None) -> dict:
    code = generated_code or ""
    result = _base_result()
    if not code.strip():
        result["static_validation_errors"].append("empty_code")
        return result
    if "```" in code:
        result["static_validation_errors"].append("contains_markdown_fence")

    try:
        tree = ast.parse(code)
    except SyntaxError:
        result["static_validation_errors"].append("syntax_error")
        return result

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
    return result
