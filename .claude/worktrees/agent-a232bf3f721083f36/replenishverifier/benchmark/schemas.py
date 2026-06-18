"""Legacy benchmark constants.

Structure schema definitions live in ``replenishverifier.data.structure_schema``.
This module remains as a compatibility import location for benchmark problem-type
metadata and the legacy ``STRUCTURE_KEYS`` symbol.
"""

from replenishverifier.data.structure_schema import STRUCTURE_KEYS


PROBLEM_TYPES = [
    "single_period_newsvendor",
    "single_item_multi_period",
    "single_item_multi_period_shortage",
    "multi_item_capacity",
    "fixed_order_cost_big_m",
]

DIFFICULTY_BY_TYPE = {
    "single_period_newsvendor": "easy",
    "single_item_multi_period": "medium",
    "single_item_multi_period_shortage": "medium",
    "multi_item_capacity": "hard",
    "fixed_order_cost_big_m": "hard",
}


def empty_structures():
    return {k: False for k in STRUCTURE_KEYS}
