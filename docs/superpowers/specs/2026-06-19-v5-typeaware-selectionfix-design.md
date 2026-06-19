# v5 TypeAware Selectionfix Design

## Goal

Improve ReplenishVerifier v5 TypeAware selection, diagnostics, metrics, and reporting without changing LLM generation-time static validation, hard rejection, or retry behavior.

## Scope

This round intentionally excludes `replenishverifier/llm/run_generation.py` and any new generation-time flag such as `--require_type_aware_valid_code`. Generation-stage validation/retry will be handled separately.

## Constraints

- Formal selection must not use `reference_objective`, `objective_correct`, reference LPs, reference answers, relative error, pass@k, or oracle diagnostics.
- Reference objective and objective correctness remain post-hoc evaluation, oracle, diagnostics, and error-analysis fields only.
- Existing method names and output files remain backward compatible.
- New diagnostics may report post-hoc objective correctness, but must label it as post-hoc and not feed it into selection.

## Design

### Method-specific tie-breakers

Selection ranking now uses `_selection_tie_break_key_for_method(row, method_name, allow_feasible_selection=False)` instead of sending every method through the same structure-heavy tie-breaker. Solver-only methods use solver/generic validity signals; structure methods use structure-specific signals; consensus methods use objective consensus and generic validity; TypeAware uses TypeAware score, critical-structure pass, objective-term and constraint coverage, hard-gate score, feedback count, runtime, and candidate order.

### TypeAware critical pool filter

`ReplenishVerifier-TypeAware` applies a method-local viable-candidate pool filter. If any viable candidate has no critical missing structures, TypeAware ranks only that subset. If every viable candidate misses critical structures, it falls back to the viable set and records fallback metadata. Other methods are unchanged.

### Objective-term metrics

Objective-term reporting keeps surface regex coverage and adds parsed-LP objective coefficient coverage. Final objective-term coverage is the surface score when no LP objective coefficients are available, and `min(surface, lp_coefficient)` when coefficient evidence exists. This makes superficial cost-variable strings less likely to overstate objective correctness.

### Diagnostics and reporting

Selection diagnostics now include missed-oracle summaries and paired TypeAware-vs-baseline comparisons. Paper metrics export objective/structure count denominators, objective-term surface/coefficient/final coverage, missed-oracle tables, and paired-comparison tables.

## Verification

Tests cover method-specific tie-breakers, TypeAware critical filtering, objective-term coefficient coverage, missed-oracle diagnostics, paired comparisons, and paper reporting tables. Full pytest must pass before using the results.
