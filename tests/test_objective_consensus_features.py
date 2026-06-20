from replenishverifier.selection.objective_consensus import compute_objective_consensus_features


def _row(candidate_id, objective, executable=True, status="Optimal"):
    return {
        "problem_id": "p0",
        "candidate_id": candidate_id,
        "execution": {"executable": executable, "status": status, "objective": objective},
    }


def test_objective_consensus_clusters_solver_ok_finite_objectives():
    rows = [
        _row("k0", 10.0),
        _row("k1", 10.000001),
        _row("k2", 20.0),
        _row("k3", None),
        _row("k4", 10.0, executable=False, status="Error"),
    ]

    features = compute_objective_consensus_features(rows, abs_tol=1e-4, rel_tol=1e-4)

    by_id = {row["candidate_id"]: row for row in features}
    assert by_id["k0"]["objective_cluster_size"] == 2
    assert by_id["k1"]["objective_cluster_id"] == by_id["k0"]["objective_cluster_id"]
    assert by_id["k2"]["objective_cluster_size"] == 1
    assert by_id["k3"]["objective_cluster_size"] == 0
    assert by_id["k4"]["solver_ok"] is False


def test_objective_consensus_density_not_zero_when_all_objectives_differ():
    rows = [_row("k0", 10.0), _row("k1", 20.0), _row("k2", 30.0)]

    features = compute_objective_consensus_features(rows, abs_tol=1e-6, rel_tol=1e-6)

    assert all(row["objective_consensus_score"] > 0.0 for row in features)
    assert all(row["objective_density_score"] > 0.0 for row in features)
    assert all(row["objective_cluster_size"] == 1 for row in features)
