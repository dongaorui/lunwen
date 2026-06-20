import statistics


def _solver_ok(row):
    execution = row.get("execution") or {}
    objective = execution.get("objective")
    if not execution.get("executable") or str(execution.get("status") or "") != "Optimal":
        return False
    if objective is None:
        return False
    try:
        value = float(objective)
    except (TypeError, ValueError):
        return False
    return value == value and value not in {float("inf"), float("-inf")}


def _objective_value(row):
    try:
        return float((row.get("execution") or {}).get("objective"))
    except (TypeError, ValueError):
        return None


def _within_tolerance(a, b, abs_tol, rel_tol):
    return abs(a - b) <= max(abs_tol, rel_tol * max(abs(a), abs(b), 1.0))


def _build_clusters(valid_items, abs_tol, rel_tol):
    clusters = []
    for idx, objective in sorted(valid_items, key=lambda item: item[1]):
        placed = False
        for cluster in clusters:
            if _within_tolerance(objective, cluster["median"], abs_tol, rel_tol):
                cluster["items"].append((idx, objective))
                values = [value for _, value in cluster["items"]]
                cluster["median"] = float(statistics.median(values))
                placed = True
                break
        if not placed:
            clusters.append({"items": [(idx, objective)], "median": objective})
    return clusters


def compute_objective_consensus_features(rows, abs_tol=1e-5, rel_tol=1e-4):
    rows = list(rows)
    valid_items = []
    for idx, row in enumerate(rows):
        if _solver_ok(row):
            valid_items.append((idx, _objective_value(row)))
    clusters = _build_clusters(valid_items, abs_tol=abs_tol, rel_tol=rel_tol) if valid_items else []
    valid_count = len(valid_items)
    cluster_by_idx = {}
    for cluster_id, cluster in enumerate(clusters):
        values = [value for _, value in cluster["items"]]
        median = float(statistics.median(values))
        for idx, value in cluster["items"]:
            cluster_by_idx[idx] = {
                "objective_cluster_id": cluster_id,
                "objective_cluster_size": len(cluster["items"]),
                "objective_consensus_score": float(len(cluster["items"]) / max(valid_count, 1)),
                "objective_cluster_median": median,
                "distance_to_cluster_median": float(abs(value - median)),
            }
    all_values = [value for _, value in valid_items]
    span = max(all_values) - min(all_values) if len(all_values) > 1 else 0.0
    nearest_distance = {}
    for idx, value in valid_items:
        distances = [abs(value - other) for other_idx, other in valid_items if other_idx != idx]
        nearest_distance[idx] = min(distances) if distances else 0.0
    result = []
    for idx, row in enumerate(rows):
        objective = _objective_value(row) if _solver_ok(row) else None
        base = {
            "problem_id": row.get("problem_id"),
            "candidate_id": row.get("candidate_id"),
            "solver_ok": _solver_ok(row),
            "objective_value": objective,
            "objective_cluster_id": None,
            "objective_cluster_size": 0,
            "objective_consensus_score": 0.0,
            "objective_density_score": 0.0,
            "objective_cluster_median": None,
            "distance_to_cluster_median": None,
        }
        if idx in cluster_by_idx:
            base.update(cluster_by_idx[idx])
            if span <= max(abs_tol, rel_tol):
                density = 1.0
            else:
                density = 1.0 - min(nearest_distance.get(idx, span) / max(span, abs_tol), 1.0)
                density = max(density, 1.0 / max(valid_count, 1))
            base["objective_density_score"] = float(density)
        result.append(base)
    return result
