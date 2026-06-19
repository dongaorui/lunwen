# Structure Schema Merge Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `split_expected_structures()` so problem-type schema requirements and explicit instance `expected_structures` are merged correctly.

**Architecture:** Keep `EXPECTED_STRUCTURES_BY_TYPE` as the central schema. `split_expected_structures()` should copy schema sets, merge truthy explicit expected keys into required structures, remove required keys from optional/forbidden metadata, and fall back to schema when explicit expected is `None` or empty. Tests document the partial-override merge behavior.

**Tech Stack:** Python 3.10+, pytest, existing `replenishverifier.data.structure_schema` module.

## Global Constraints

- Communicate with the user in Chinese.
- Do not change formal selection to use `reference_objective`.
- Use TDD: add a failing regression test before production code.
- Do not run LLM generation or large experiments.
- Do not git push.

---

### Task 1: Add Regression Test for Schema + Explicit Expected Merge

**Files:**
- Modify: `tests/test_structure_schema.py`
- Later modify: `replenishverifier/data/structure_schema.py`

**Interfaces:**
- Consumes: `split_expected_structures(expected: dict | None, problem_type: str | None) -> tuple[list[str], list[str], list[str]]`
- Produces: documented behavior where schema required structures remain required and explicit truthy expected keys are added to required.

- [ ] **Step 1: Write the failing test**

```python
def test_explicit_expected_structures_merge_with_default_schema():
    expected = {"capacity_constraint": True}

    required, optional, forbidden = split_expected_structures(expected, problem_type="single_item_multi_period")

    assert "inventory_balance" in required
    assert "order_variable" in required
    assert "inventory_variable" in required
    assert "capacity_constraint" in required
    assert "capacity_constraint" not in optional
    assert forbidden == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_structure_schema.py::test_explicit_expected_structures_merge_with_default_schema -q`

Expected before fix: FAIL because the old implementation returns only `capacity_constraint` as required and drops schema-required keys such as `inventory_balance`.

- [ ] **Step 3: Implement minimal fix**

In `split_expected_structures()`, initialize required from schema when `problem_type` is known, then union truthy explicit expected keys:

```python
if schema is not None:
    required = set(schema["required"])
else:
    required = set()
required |= _truthy_expected_keys(expected)
```

Keep optional/forbidden removal of required keys unchanged.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_structure_schema.py -q`

Expected: all structure schema tests pass.

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`

Expected: full suite passes; warnings may be existing PuLP warnings.

- [ ] **Step 6: Update planning files and report**

Update `progress.md`, `findings.md`, and `task_plan.md` with the bugfix, tests, pytest result, and no-push note.
