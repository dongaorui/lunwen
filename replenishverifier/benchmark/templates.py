import random
from copy import deepcopy

import pulp

from replenishverifier.data.structure_schema import expected_from_schema


def expected_for(problem_type):
    return expected_from_schema(problem_type)


def sample_params(problem_type, rng=None):
    rng = rng or random.Random()

    if problem_type == "single_period_newsvendor":
        return {
            "demand": rng.randint(30, 120),
            "unit_order_cost": rng.randint(1, 5),
            "holding_cost": rng.randint(1, 4),
            "shortage_cost": rng.randint(5, 15),
        }

    if problem_type == "single_item_multi_period":
        t_count = rng.randint(3, 6)
        return {
            "periods": t_count,
            "initial_inventory": rng.randint(0, 30),
            "demand": [rng.randint(15, 60) for _ in range(t_count)],
            "unit_order_cost": rng.randint(1, 5),
            "holding_cost": rng.randint(1, 4),
        }

    if problem_type == "single_item_multi_period_shortage":
        t_count = rng.randint(3, 6)
        return {
            "periods": t_count,
            "initial_inventory": rng.randint(0, 20),
            "demand": [rng.randint(20, 70) for _ in range(t_count)],
            "unit_order_cost": rng.randint(1, 5),
            "holding_cost": rng.randint(1, 4),
            "shortage_cost": rng.randint(8, 20),
        }

    if problem_type == "multi_item_capacity":
        t_count = rng.randint(3, 5)
        n_items = rng.randint(2, 4)
        demand = [[rng.randint(10, 50) for _ in range(t_count)] for _ in range(n_items)]
        volume = [rng.randint(1, 4) for _ in range(n_items)]
        initial_inventory = [rng.randint(0, 20) for _ in range(n_items)]
        return {
            "items": n_items,
            "periods": t_count,
            "initial_inventory": initial_inventory,
            "demand": demand,
            "volume": volume,
            "storage_capacity": rng.randint(80, 160),
            "unit_order_cost": [rng.randint(1, 5) for _ in range(n_items)],
            "holding_cost": [rng.randint(1, 4) for _ in range(n_items)],
        }

    if problem_type == "fixed_order_cost_big_m":
        t_count = rng.randint(3, 6)
        demand = [rng.randint(15, 60) for _ in range(t_count)]
        return {
            "periods": t_count,
            "initial_inventory": rng.randint(0, 20),
            "demand": demand,
            "unit_order_cost": rng.randint(1, 5),
            "holding_cost": rng.randint(1, 4),
            "fixed_order_cost": rng.randint(20, 80),
            "big_m": max(sum(demand), max(demand) * 2),
        }

    raise ValueError(f"Unknown problem_type: {problem_type}")


def natural_language(problem_type, params):
    if problem_type == "single_period_newsvendor":
        return (
            "A retailer decides a single-period order quantity for one product. "
            f"Demand is {params['demand']}. Unit ordering cost is {params['unit_order_cost']}, "
            f"holding cost for leftover inventory is {params['holding_cost']}, and shortage penalty is "
            f"{params['shortage_cost']}. Formulate and solve a linear optimization model."
        )

    if problem_type == "single_item_multi_period":
        return (
            f"A firm plans replenishment for one item over {params['periods']} periods. "
            f"Initial inventory is {params['initial_inventory']}. Period demands are {params['demand']}. "
            f"Unit ordering cost is {params['unit_order_cost']} and holding cost is {params['holding_cost']}. "
            "Use inventory balance constraints to minimize total ordering and holding cost."
        )

    if problem_type == "single_item_multi_period_shortage":
        return (
            f"A firm plans replenishment for one item over {params['periods']} periods with backorders allowed. "
            f"Initial inventory is {params['initial_inventory']}. Period demands are {params['demand']}. "
            f"Unit ordering cost is {params['unit_order_cost']}, holding cost is {params['holding_cost']}, "
            f"and shortage penalty is {params['shortage_cost']}. Formulate a linear model with inventory and shortage variables."
        )

    if problem_type == "multi_item_capacity":
        return (
            f"A warehouse replenishes {params['items']} items over {params['periods']} periods. "
            f"Initial inventories are {params['initial_inventory']}. Demand matrix by item and period is {params['demand']}. "
            f"Item volumes are {params['volume']} and storage capacity per period is {params['storage_capacity']}. "
            "Minimize ordering and holding costs subject to inventory balance and capacity constraints."
        )

    if problem_type == "fixed_order_cost_big_m":
        return (
            f"A firm plans replenishment over {params['periods']} periods with fixed ordering cost. "
            f"Initial inventory is {params['initial_inventory']}. Demands are {params['demand']}. "
            f"Unit ordering cost is {params['unit_order_cost']}, holding cost is {params['holding_cost']}, "
            f"fixed ordering cost is {params['fixed_order_cost']}. Use binary order trigger variables and Big-M constraints "
            f"with M = {params['big_m']}."
        )

    raise ValueError(f"Unknown problem_type: {problem_type}")


def build_model(problem_type, params):
    if problem_type == "single_period_newsvendor":
        model = pulp.LpProblem("single_period_newsvendor", pulp.LpMinimize)
        q = pulp.LpVariable("Q_0", lowBound=0)
        inv = pulp.LpVariable("I_0", lowBound=0)
        back = pulp.LpVariable("B_0", lowBound=0)
        model += params["unit_order_cost"] * q + params["holding_cost"] * inv + params["shortage_cost"] * back, "total_cost"
        model += q + back - inv == params["demand"], "demand_satisfaction_0"
        return model

    if problem_type == "single_item_multi_period":
        t_count = params["periods"]
        model = pulp.LpProblem("single_item_multi_period", pulp.LpMinimize)
        q = pulp.LpVariable.dicts("Q", range(t_count), lowBound=0)
        inv = pulp.LpVariable.dicts("I", range(t_count), lowBound=0)
        model += pulp.lpSum(params["unit_order_cost"] * q[t] + params["holding_cost"] * inv[t] for t in range(t_count)), "total_cost"
        for t in range(t_count):
            prev = params["initial_inventory"] if t == 0 else inv[t - 1]
            model += inv[t] == prev + q[t] - params["demand"][t], f"inventory_balance_{t}"
        return model

    if problem_type == "single_item_multi_period_shortage":
        t_count = params["periods"]
        model = pulp.LpProblem("single_item_multi_period_shortage", pulp.LpMinimize)
        q = pulp.LpVariable.dicts("Q", range(t_count), lowBound=0)
        inv = pulp.LpVariable.dicts("I", range(t_count), lowBound=0)
        back = pulp.LpVariable.dicts("B", range(t_count), lowBound=0)
        model += pulp.lpSum(
            params["unit_order_cost"] * q[t] + params["holding_cost"] * inv[t] + params["shortage_cost"] * back[t]
            for t in range(t_count)
        ), "total_cost"
        for t in range(t_count):
            prev_net = params["initial_inventory"] if t == 0 else inv[t - 1] - back[t - 1]
            model += inv[t] - back[t] == prev_net + q[t] - params["demand"][t], f"inventory_balance_{t}"
        return model

    if problem_type == "multi_item_capacity":
        n_items, t_count = params["items"], params["periods"]
        model = pulp.LpProblem("multi_item_capacity", pulp.LpMinimize)
        q = pulp.LpVariable.dicts("Q", ((i, t) for i in range(n_items) for t in range(t_count)), lowBound=0)
        inv = pulp.LpVariable.dicts("I", ((i, t) for i in range(n_items) for t in range(t_count)), lowBound=0)
        model += pulp.lpSum(
            params["unit_order_cost"][i] * q[(i, t)] + params["holding_cost"][i] * inv[(i, t)]
            for i in range(n_items) for t in range(t_count)
        ), "total_cost"
        for i in range(n_items):
            for t in range(t_count):
                prev = params["initial_inventory"][i] if t == 0 else inv[(i, t - 1)]
                model += inv[(i, t)] == prev + q[(i, t)] - params["demand"][i][t], f"inventory_balance_{i}_{t}"
        for t in range(t_count):
            model += pulp.lpSum(params["volume"][i] * inv[(i, t)] for i in range(n_items)) <= params["storage_capacity"], f"capacity_{t}"
        return model

    if problem_type == "fixed_order_cost_big_m":
        t_count = params["periods"]
        model = pulp.LpProblem("fixed_order_cost_big_m", pulp.LpMinimize)
        q = pulp.LpVariable.dicts("Q", range(t_count), lowBound=0)
        inv = pulp.LpVariable.dicts("I", range(t_count), lowBound=0)
        y = pulp.LpVariable.dicts("Y", range(t_count), lowBound=0, upBound=1, cat="Binary")
        model += pulp.lpSum(
            params["unit_order_cost"] * q[t] + params["holding_cost"] * inv[t] + params["fixed_order_cost"] * y[t]
            for t in range(t_count)
        ), "total_cost"
        for t in range(t_count):
            prev = params["initial_inventory"] if t == 0 else inv[t - 1]
            model += inv[t] == prev + q[t] - params["demand"][t], f"inventory_balance_{t}"
            model += q[t] <= params["big_m"] * y[t], f"big_m_{t}"
        return model

    raise ValueError(f"Unknown problem_type: {problem_type}")


def reference_code(problem_type, params):
    params_repr = repr(deepcopy(params))
    return f'''
import pulp

PROBLEM_TYPE = {problem_type!r}
PARAMS = {params_repr}


def build_model():
    from replenishverifier.benchmark.templates import build_model as _build_model
    return _build_model(PROBLEM_TYPE, PARAMS)


if __name__ == "__main__":
    model = build_model()
    model.solve(pulp.PULP_CBC_CMD(msg=False))
    print(pulp.LpStatus[model.status])
    print(pulp.value(model.objective))
'''.strip() + "\n"
