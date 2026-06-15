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


def _variant(style, text, template_id):
    return {"style": style, "text": text, "template_id": template_id}


def natural_language_variants(problem_type, params):
    if problem_type == "single_period_newsvendor":
        return [
            _variant("math", f"Single-period newsvendor: choose order Q, leftover inventory I, and shortage B for demand {params['demand']}. Minimize {params['unit_order_cost']}Q + {params['holding_cost']}I + {params['shortage_cost']}B subject to demand satisfaction.", "single_period_newsvendor_math"),
            _variant("business", f"A retailer is buying one product for a one-day selling season. Demand is {params['demand']}; each unit ordered costs {params['unit_order_cost']}, leftovers cost {params['holding_cost']}, and unmet demand costs {params['shortage_cost']}. Build a linear optimization model for the order decision.", "single_period_newsvendor_business"),
            _variant("verbose", f"Consider a single item with one ordering opportunity and uncertain demand represented by the realized demand value {params['demand']}. The formulation should account for the order quantity, any ending inventory, and any shortage. Ordering, holding, and shortage costs are {params['unit_order_cost']}, {params['holding_cost']}, and {params['shortage_cost']}, respectively. Formulate and solve the corresponding linear program.", "single_period_newsvendor_verbose"),
            _variant("table", f"Problem data:\n- Type: single-period newsvendor\n- Demand: {params['demand']}\n- Unit order cost: {params['unit_order_cost']}\n- Holding cost: {params['holding_cost']}\n- Shortage penalty: {params['shortage_cost']}\nTask: formulate a linear minimization model with order, inventory, and shortage variables.", "single_period_newsvendor_table"),
        ]

    if problem_type == "single_item_multi_period":
        return [
            _variant("math", f"Plan one-item replenishment over T={params['periods']} periods with initial inventory {params['initial_inventory']} and demands {params['demand']}. Minimize order cost {params['unit_order_cost']} and holding cost {params['holding_cost']} using inventory-balance constraints.", "single_item_multi_period_math"),
            _variant("business", f"A store replenishes a single SKU across {params['periods']} periods. It starts with {params['initial_inventory']} units and faces period demands {params['demand']}. Ordering costs {params['unit_order_cost']} per unit and holding costs {params['holding_cost']} per unit. Build the cost-minimizing replenishment LP.", "single_item_multi_period_business"),
            _variant("verbose", f"The planner must decide how much to order in each period for one item. Initial stock is {params['initial_inventory']}; demand by period is {params['demand']}. The model should carry inventory forward with standard balance equations and minimize the sum of ordering and inventory holding costs, with unit costs {params['unit_order_cost']} and {params['holding_cost']}.", "single_item_multi_period_verbose"),
            _variant("table", f"Problem data:\n- Type: single-item multi-period replenishment\n- Periods: {params['periods']}\n- Initial inventory: {params['initial_inventory']}\n- Demands: {params['demand']}\n- Unit order cost: {params['unit_order_cost']}\n- Holding cost: {params['holding_cost']}\nTask: formulate and solve a linear inventory-balance model.", "single_item_multi_period_table"),
        ]

    if problem_type == "single_item_multi_period_shortage":
        return [
            _variant("math", f"For T={params['periods']} periods, choose order Q_t, inventory I_t, and backlog B_t. Initial inventory is {params['initial_inventory']}, demand is {params['demand']}, and unit order/holding/shortage costs are {params['unit_order_cost']}/{params['holding_cost']}/{params['shortage_cost']}. Minimize total cost with net-inventory balance.", "single_item_multi_period_shortage_math"),
            _variant("business", f"A firm replenishes one product over {params['periods']} periods and allows backorders. Starting inventory is {params['initial_inventory']}; demands are {params['demand']}. Ordering costs {params['unit_order_cost']}, holding costs {params['holding_cost']}, and backlog penalties are {params['shortage_cost']}. Build a linear model.", "single_item_multi_period_shortage_business"),
            _variant("verbose", f"The replenishment plan may leave demand temporarily unmet, so the LP should include shortage or backlog variables as well as inventory and order variables. Use the initial inventory {params['initial_inventory']} and demand sequence {params['demand']}; minimize ordering, holding, and shortage costs with coefficients {params['unit_order_cost']}, {params['holding_cost']}, and {params['shortage_cost']}.", "single_item_multi_period_shortage_verbose"),
            _variant("table", f"Problem data:\n- Type: multi-period replenishment with shortages\n- Periods: {params['periods']}\n- Initial inventory: {params['initial_inventory']}\n- Demands: {params['demand']}\n- Unit order cost: {params['unit_order_cost']}\n- Holding cost: {params['holding_cost']}\n- Shortage penalty: {params['shortage_cost']}\nTask: formulate a linear backorder model.", "single_item_multi_period_shortage_table"),
        ]

    if problem_type == "multi_item_capacity":
        return [
            _variant("math", f"Plan replenishment for {params['items']} items and {params['periods']} periods. Initial inventories are {params['initial_inventory']}, demands are {params['demand']}, item volumes are {params['volume']}, and storage capacity is {params['storage_capacity']} per period. Minimize order and holding costs subject to inventory balance and capacity.", "multi_item_capacity_math"),
            _variant("business", f"A warehouse manages {params['items']} products over {params['periods']} periods with limited storage. It begins with inventories {params['initial_inventory']} and demand matrix {params['demand']}. Item volumes are {params['volume']} and capacity is {params['storage_capacity']}. Build the replenishment LP minimizing order and holding costs.", "multi_item_capacity_business"),
            _variant("verbose", f"The planner must coordinate multiple items that share a finite warehouse capacity in every period. For each item and period, use the demand data {params['demand']} and starting inventories {params['initial_inventory']}. The model should include item-level inventory balances and aggregate volume limits using volumes {params['volume']} and capacity {params['storage_capacity']}, with order costs {params['unit_order_cost']} and holding costs {params['holding_cost']}.", "multi_item_capacity_verbose"),
            _variant("table", f"Problem data:\n- Type: multi-item capacity-constrained replenishment\n- Items: {params['items']}\n- Periods: {params['periods']}\n- Initial inventories: {params['initial_inventory']}\n- Demand matrix: {params['demand']}\n- Volumes: {params['volume']}\n- Capacity: {params['storage_capacity']}\n- Unit order costs: {params['unit_order_cost']}\n- Holding costs: {params['holding_cost']}\nTask: formulate and solve the LP.", "multi_item_capacity_table"),
        ]

    if problem_type == "fixed_order_cost_big_m":
        return [
            _variant("math", f"Plan T={params['periods']} periods with fixed ordering costs. Initial inventory is {params['initial_inventory']} and demands are {params['demand']}. Use order Q_t, inventory I_t, binary order trigger Y_t, and Big-M links with M={params['big_m']}; minimize unit order cost {params['unit_order_cost']}, holding cost {params['holding_cost']}, and fixed cost {params['fixed_order_cost']}.", "fixed_order_cost_big_m_math"),
            _variant("business", f"A firm pays a setup cost whenever it places an order during a {params['periods']}-period horizon. It starts with {params['initial_inventory']} units and faces demands {params['demand']}. Unit ordering, holding, and fixed order costs are {params['unit_order_cost']}, {params['holding_cost']}, and {params['fixed_order_cost']}. Build a Big-M mixed-integer replenishment model with M={params['big_m']}.", "fixed_order_cost_big_m_business"),
            _variant("verbose", f"In this replenishment problem, ordering in a period incurs both a variable unit cost and a fixed activation cost. The formulation should include binary variables that indicate whether an order is placed and constraints linking order quantities to those binaries. Use initial inventory {params['initial_inventory']}, demands {params['demand']}, unit cost {params['unit_order_cost']}, holding cost {params['holding_cost']}, fixed cost {params['fixed_order_cost']}, and Big-M value {params['big_m']}.", "fixed_order_cost_big_m_verbose"),
            _variant("table", f"Problem data:\n- Type: fixed-order-cost replenishment\n- Periods: {params['periods']}\n- Initial inventory: {params['initial_inventory']}\n- Demands: {params['demand']}\n- Unit order cost: {params['unit_order_cost']}\n- Holding cost: {params['holding_cost']}\n- Fixed order cost: {params['fixed_order_cost']}\n- Big-M: {params['big_m']}\nTask: formulate a mixed-integer linear model with binary order triggers.", "fixed_order_cost_big_m_table"),
        ]

    raise ValueError(f"Unknown problem_type: {problem_type}")


def choose_natural_language_variant(problem_type, params, rng=None, style=None):
    variants = natural_language_variants(problem_type, params)
    if style is not None:
        for variant in variants:
            if variant["style"] == style or variant["template_id"] == style:
                return variant
        raise ValueError(f"Unknown language style/template for {problem_type}: {style}")
    if rng is None:
        return variants[0]
    return rng.choice(variants)


def natural_language(problem_type, params, rng=None, style=None):
    return choose_natural_language_variant(problem_type, params, rng=rng, style=style)["text"]


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
