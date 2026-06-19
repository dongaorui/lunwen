"""Problem-type-specific replenishment structure schema.

Required structures contribute to the main structure score. Optional structures are
reported in certificates but do not affect the main score. Forbidden structures
are explicit schema metadata for future diagnostics and are not penalized by
absence.
"""

STRUCTURE_KEYS = [
    "inventory_balance",
    "order_variable",
    "inventory_variable",
    "shortage_variable",
    "capacity_constraint",
    "binary_order_variable",
    "big_m_constraint",
    "lead_time",
    "order_cost",
    "holding_cost",
    "shortage_cost",
    "fixed_order_cost",
    "demand_satisfaction",
    "nonnegative_bounds",
    "objective_minimize",
]


EXPECTED_STRUCTURES_BY_TYPE = {
    "single_period_newsvendor": {
        "required": {
            "order_variable",
            "inventory_variable",
            "shortage_variable",
            "order_cost",
            "holding_cost",
            "shortage_cost",
            "demand_satisfaction",
            "nonnegative_bounds",
            "objective_minimize",
        },
        "optional": {"inventory_balance"},
        "forbidden": set(),
    },
    "single_item_multi_period": {
        "required": {
            "inventory_balance",
            "order_variable",
            "inventory_variable",
            "order_cost",
            "holding_cost",
            "nonnegative_bounds",
            "objective_minimize",
        },
        "optional": {"capacity_constraint", "lead_time"},
        "forbidden": set(),
    },
    "single_item_multi_period_shortage": {
        "required": {
            "inventory_balance",
            "order_variable",
            "inventory_variable",
            "shortage_variable",
            "order_cost",
            "holding_cost",
            "shortage_cost",
            "nonnegative_bounds",
            "objective_minimize",
        },
        "optional": {"lead_time"},
        "forbidden": set(),
    },
    "multi_item_capacity": {
        "required": {
            "inventory_balance",
            "order_variable",
            "inventory_variable",
            "capacity_constraint",
            "order_cost",
            "holding_cost",
            "nonnegative_bounds",
            "objective_minimize",
        },
        "optional": {"shortage_variable", "lead_time"},
        "forbidden": set(),
    },
    "fixed_order_cost_big_m": {
        "required": {
            "inventory_balance",
            "order_variable",
            "inventory_variable",
            "binary_order_variable",
            "big_m_constraint",
            "order_cost",
            "holding_cost",
            "fixed_order_cost",
            "nonnegative_bounds",
            "objective_minimize",
        },
        "optional": {"capacity_constraint", "lead_time"},
        "forbidden": set(),
    },
}

# Backward-compatible alias for older imports.
STRUCTURE_SCHEMA = EXPECTED_STRUCTURES_BY_TYPE


def _copy_schema(schema):
    return {
        "required": set(schema.get("required", set())),
        "optional": set(schema.get("optional", set())),
        "forbidden": set(schema.get("forbidden", set())),
    }


def get_structure_schema(problem_type: str) -> dict:
    """Return required/optional/forbidden structure sets for a problem type."""
    if problem_type not in EXPECTED_STRUCTURES_BY_TYPE:
        raise ValueError(f"Unknown problem_type: {problem_type}")
    return _copy_schema(EXPECTED_STRUCTURES_BY_TYPE[problem_type])


def schema_for_problem_type(problem_type):
    """Backward-compatible wrapper around get_structure_schema."""
    return get_structure_schema(problem_type)


def expected_from_schema(problem_type):
    schema = get_structure_schema(problem_type)
    expected = {key: False for key in STRUCTURE_KEYS}
    for key in schema["required"]:
        expected[key] = True
    return expected


def _truthy_expected_keys(expected):
    return {key for key, value in (expected or {}).items() if value}


def split_expected_structures(expected=None, problem_type=None):
    """Return required/optional/forbidden structure names.

    Instance-level ``expected_structures`` takes precedence: truthy keys in an
    explicit expected map are treated as required for that instance. The default
    problem-type schema is used as fallback when no explicit expected map is
    supplied, and as metadata for optional/forbidden structures when available.
    """
    schema = None
    if problem_type is not None:
        schema = get_structure_schema(problem_type)

    if schema is not None:
        required = set(schema["required"])
    else:
        required = set()
    required |= _truthy_expected_keys(expected)

    if schema is not None:
        optional = set(schema["optional"]) - required
        forbidden = set(schema["forbidden"]) - required
    else:
        optional = set(STRUCTURE_KEYS) - required
        forbidden = set()

    return sorted(required), sorted(optional), sorted(forbidden)
