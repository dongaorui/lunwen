from replenishverifier.experiments.compare_experiment_packages import compare_experiment_packages
from replenishverifier.utils.io import write_jsonl


def _selected(method, pid, cid, correct=1.0):
    return {
        "method_name": method,
        "problem_id": pid,
        "candidate_id": cid,
        "selected": True,
        "objective_correct": correct,
        "execution": {"executable": True, "status": "Optimal", "objective": 1.0},
        "structure_score": 1.0,
    }


def test_compare_experiment_packages_writes_regression_summary(tmp_path):
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    out_dir = tmp_path / "out"
    old_dir.mkdir()
    new_dir.mkdir()
    write_jsonl(old_dir / "main_results.jsonl", [
        _selected("ReplenishVerifier-Full", "p0", "k0", correct=1.0),
        _selected("ReplenishVerifier-Full", "p1", "k0", correct=1.0),
    ])
    write_jsonl(new_dir / "main_results.jsonl", [
        _selected("ReplenishVerifier-Full", "p0", "k1", correct=0.0),
        _selected("ReplenishVerifier-Full", "p1", "k0", correct=1.0),
    ])

    result = compare_experiment_packages(old_dir=old_dir, new_dir=new_dir, out_dir=out_dir)

    assert (out_dir / "regression_summary.md").exists()
    assert (out_dir / "selected_candidate_changes.csv").exists()
    assert result["method_regressions"][0]["method"] == "ReplenishVerifier-Full"
    assert result["method_regressions"][0]["objective_accuracy_delta"] == -0.5
    text = (out_dir / "regression_summary.md").read_text(encoding="utf-8")
    assert "posthoc_only" in text
    assert "ReplenishVerifier-Full" in text


def test_compare_experiment_packages_falls_back_to_markdown_summary(tmp_path):
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    out_dir = tmp_path / "out"
    old_dir.mkdir()
    new_dir.mkdir()
    (old_dir / "main_results.md").write_text(
        "# Main Results\n\n"
        "| method | n | objective_accuracy |\n"
        "| --- | --- | --- |\n"
        "| ReplenishVerifier-Full | 100 | 0.7400 |\n",
        encoding="utf-8",
    )
    (new_dir / "main_results.md").write_text(
        "# Main Results\n\n"
        "| method | n | objective_accuracy |\n"
        "| --- | --- | --- |\n"
        "| ReplenishVerifier-Full | 100 | 0.7200 |\n",
        encoding="utf-8",
    )

    result = compare_experiment_packages(old_dir=old_dir, new_dir=new_dir, out_dir=out_dir)

    assert result["method_regressions"][0]["objective_accuracy_delta"] == -0.020000000000000018
    assert (out_dir / "regression_summary.md").exists()
