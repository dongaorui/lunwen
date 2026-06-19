# ReplenishVerifier Code Cleanup Report

Updated after package consolidation.

## Current Package Layout

The project now keeps a single implementation package:

- replenishverifier/: main Python package for benchmark generation, LP parsing, structure verification, scoring, experiments, and LLM generation.

The old compatibility package has been removed:

- replenish/: removed. It only contained thin wrappers that forwarded old python -m replenish... commands to replenishverifier... modules.

## Why replenish/ Was Removed

Static inspection showed that replenish/ did not contain independent implementation logic. Its files only imported main from matching replenishverifier modules.

Keeping both package names made the repository harder to explain. The canonical command style is now always python -m replenishverifier.... Old python -m replenish... commands are intentionally no longer supported.

## Files Kept

Do not delete these as part of package-name cleanup:

- replenishverifier/
- scripts/
- tests/
- papers/
- docs/
- data/generated/
- data/candidates/

Experiment outputs under runs/, outputs/, and docs/experiment_results/ are separate cleanup decisions and were not part of this package consolidation.

## Verification

After removing replenish/, these checks passed:

- replenishverifier.experiments.run_all_methods imports successfully.
- replenishverifier.llm.run_generation imports successfully.
- replenishverifier.verifier.structure_rules imports successfully.
- Importing replenish raises ModuleNotFoundError, confirming the old package is gone.
- Selected core tests passed: 29 passed.
