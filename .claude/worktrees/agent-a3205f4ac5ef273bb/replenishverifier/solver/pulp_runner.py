from pathlib import Path

import pulp


def solve_pulp_model(model, lp_path=None, msg=False, time_limit=None):
    if lp_path is not None:
        lp_path = Path(lp_path)
        lp_path.parent.mkdir(parents=True, exist_ok=True)
        model.writeLP(str(lp_path))

    solver = pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)
    status_code = model.solve(solver)
    status = pulp.LpStatus.get(status_code, str(status_code))

    try:
        obj = pulp.value(model.objective)
    except Exception:
        obj = None

    return {
        "status": status,
        "objective": None if obj is None else float(obj),
        "lp_path": None if lp_path is None else str(lp_path),
    }
