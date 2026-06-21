# FullV2 Failure Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `ReplenishVerifier-FullV2` no worse than the older `ReplenishVerifier-Full` on the current k=8/100 run if a no-reference fix exists; otherwise keep the diagnostic `fullv2_failure_summary.md` as the formal failure explanation.

**Architecture:** The root-cause evidence shows FullV2 currently over-prioritizes objective-consensus cluster majority before structure/constraint signals. The minimal fix is to preserve hard viability, then make structure/constraint dominance protect against consensus-majority-but-structurally-weaker candidates; diagnostics and leakage audit remain post-hoc/evaluation-only.

**Tech Stack:** Python 3.10+, pytest, existing `replenishverifier.experiments.methods` selector utilities, existing `diagnose_selection_metrics`, existing `audit_leakage`.

## Global Constraints

- Do not regenerate candidates.
- Do not edit `replenishverifier/llm/run_generation.py`.
- Do not use `reference_objective`, `objective_correct`, oracle fields, reference LP, or reference answers in formal selection.
- Keep `Best-of-K` selection behavior unchanged.
- Run leakage audit before treating FullV2 results as usable.
- If `FullV2` remains below `Full`, output/update `fullv2_failure_summary.md` explaining the failure as one or more of: objective consensus misleading; structure/constraint stronger; type-aware penalty too strong; non-reference signals unable to distinguish.

---

### Task 1: Add regression test for misleading majority consensus

**Files:**
- Modify: `tests/test_fullv2_not_structure_alias.py`

**Interfaces:**
- Consumes: `select_for_method(method_name, evaluated_by_problem, benchmark)` from `replenishverifier.experiments.methods`.
- Produces: A failing test documenting that FullV2 should not prefer a large wrong objective-consensus cluster when a single candidate has strictly stronger structure/constraint signals and all candidates are otherwise viable.

- [ ] **Step 1: Write the failing test**

Append this test to `tests/test_fullv2_not_structure_alias.py`:

```python
def test_fullv2_does_not_let_wrong_majority_consensus_override_stronger_structure_signal():
    rows = [
        _row("c0", objective=116.0, structure=0.857, consensus=0.125, objective_terms=1.0, lp_terms=1.0),
        _row("c1", objective=150.0, structure=0.836, consensus=0.875, objective_terms=1.0, lp_terms=1.0),
        _row("c2", objective=150.0, structure=0.836, consensus=0.875, objective_terms=1.0, lp_terms=1.0),
    ]

    selected = _select("ReplenishVerifier-FullV2", rows)

    assert selected["candidate_id"] == "c0"
    components = selected["selection_components"]
    assert components["selector_family"] == "fullv2"
    assert set(components).isdisjoint({
        "reference_objective",
        "objective_correct",
        "relative_error",
        "reference_lp",
        "reference_answer",
        "oracle",
    })
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_fullv2_not_structure_alias.py::test_fullv2_does_not_let_wrong_majority_consensus_override_stronger_structure_signal -q
```

Expected: FAIL because current FullV2 selects `c1`/`c2` due to higher `objective_consensus_score` before structure.

---

### Task 2: Reorder FullV2 tuple to protect structure/constraint before consensus

**Files:**
- Modify: `replenishverifier/experiments/methods.py`
- Test: `tests/test_fullv2_not_structure_alias.py`

**Interfaces:**
- Consumes: `_fullv2_feature_tuple(row) -> list[tuple[str, value]]`.
- Produces: FullV2 score tuple that still uses only no-reference fields but ranks `structure_score` and `constraint_coverage` before objective-consensus cluster fields.

- [ ] **Step 1: Update `_fullv2_feature_tuple` non-fallback branch**

In `replenishverifier/experiments/methods.py`, change the non-fallback `tuple_items` order so it starts like this after `solver_ok` / `has_objective`:

```python
        tuple_items = [
            ("solver_ok", solver_ok),
            ("has_objective", _has_objective_score(row)),
            ("structure_score", _structure_score(row)),
            ("constraint_coverage", _constraint_coverage(row)),
            ("neg_critical_structure_penalty", -critical_penalty),
            ("type_aware_hard_gate_score", _type_aware_hard_gate_score(row)),
            ("neg_type_aware_missing_critical_count", -critical_penalty),
            ("objective_term_lp_coefficient_coverage", float(row.get("objective_term_lp_coefficient_coverage", 0.0) or 0.0)),
            ("objective_term_coverage", _objective_term_coverage(row)),
            ("objective_consensus_score", float(row.get("objective_consensus_score", 0.0) or 0.0)),
            ("objective_cluster_size", float(row.get("objective_cluster_size", 0) or 0)),
            ("objective_density_score", float(row.get("objective_density_score", 0.0) or 0.0)),
            ("neg_distance_to_cluster_median_normalized", -_normalized_cluster_distance(row)),
            ("static_validation_score", _static_validation_score(row)),
            ("code_validity_score", _code_validity_score(row)),
            ("neg_runtime_normalized", -runtime),
            ("neg_candidate_rank", -candidate_rank),
        ]
```

Do not add any reference/evaluation fields.

- [ ] **Step 2: Verify GREEN for FullV2 tests**

Run:

```bash
python -m pytest tests/test_fullv2_not_structure_alias.py tests/test_fullv2_no_reference_leakage.py -q
```

Expected: PASS.

- [ ] **Step 3: Run focused selection/leakage tests**

Run:

```bash
python -m pytest tests/test_selection_gating.py tests/test_fullv2_not_structure_alias.py tests/test_fullv2_no_reference_leakage.py tests/test_leakage_audit.py -q
```

Expected: PASS.

---

### Task 3: Rerun current experiment from existing candidates and diagnostics

**Files:**
- Read inputs: existing benchmark/candidates used by `runs/qwen3_8b_k8_100_v6_fullv2_20260620_190534` or package candidates if available.
- Write outputs: a new run directory, e.g. `runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620`.

**Interfaces:**
- Consumes: existing candidate JSONL/benchmark JSONL only.
- Produces: `main_results.md`, diagnostics including `fullv2_failure_summary.md`, paper metrics if requested, and leakage audit report.

- [ ] **Step 1: Rerun all methods without regenerating candidates**

Use the same benchmark/candidate inputs as the existing run. If the exact candidate file is absent, use the already decompressed package candidate JSONL. Command shape:

```bash
python -m replenishverifier.experiments.run_all_methods \
  --benchmark data/generated/test_100_v6.jsonl \
  --candidates data/candidates/qwen3_8b_k8_100_v6_typeaware.jsonl \
  --out_dir runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620 \
  --k_values 1,2,4,8 \
  --timeout 30 \
  --no_demo_if_empty
```

Expected: command completes and writes `main_results.md`. If local data paths are absent, do not fake results; instead update progress with the exact missing path.

- [ ] **Step 2: Generate diagnostics**

```bash
python -m replenishverifier.experiments.diagnose_selection_metrics \
  --exp_dir runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620 \
  --out_dir runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620/diagnostics
```

Expected: diagnostics include `fullv2_failure_summary.md`, `fullv2_score_debug.csv`, and `diagnostic_join_unmatched.csv`.

- [ ] **Step 3: Run leakage audit**

```bash
python -m replenishverifier.experiments.audit_leakage \
  --exp_dir runs/qwen3_8b_k8_100_v6_fullv2_structuresafe_20260620 \
  --write_report
```

Expected: `LEAKAGE AUDIT PASSED`.

---

### Task 4: Decide final outcome and update planning files

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`
- Possibly create/update: `runs/.../diagnostics/fullv2_failure_summary.md`

**Interfaces:**
- Consumes: rerun `main_results.md`, diagnostics, leakage audit output.
- Produces: final user-facing summary with exact metrics and either success or failure explanation.

- [ ] **Step 1: Compare metrics**

Read the new `main_results.md` and compare:

- `Best-of-K` objective_accuracy
- `ReplenishVerifier-Full` objective_accuracy
- `ReplenishVerifier-FullV2` objective_accuracy
- structure completeness and constraint coverage for Full vs FullV2

- [ ] **Step 2: If FullV2 is still below Full, keep/update failure summary**

Ensure `fullv2_failure_summary.md` states:

```markdown
# FullV2 Failure Summary

FullV2 remains below ReplenishVerifier-Full on objective_accuracy.

Root cause: objective consensus can be misleading when a wrong objective is generated by the majority of candidates. In the observed loss cases, the structurally stronger candidate selected by Full/Structure had lower consensus support but was post-hoc objective-correct.

Interpretation:
- objective consensus misleading: yes
- structure/constraint still stronger: yes
- type-aware penalty too strong: no direct evidence in the observed loss cases; critical missing counts were zero and type-aware hard-gate scores were tied
- non-reference signals unable to distinguish: partially; when all candidates tie on execution, objective terms, type-aware hard gates, and LP health, no-reference signals cannot know the minority objective is correct except through structure/constraint heuristics

Formal selection remains no-reference; post-hoc correctness is used only for this diagnostic explanation.
```

- [ ] **Step 3: Update planning files**

Append concise results, changed files, tests, and audit status to `progress.md`, and append durable root-cause findings to `findings.md`.
