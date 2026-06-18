# README Chinese Experiment Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not use subagent-driven development because the user requested no multi-agent work.

**Goal:** Add a Chinese README section explaining how to run experiments from simplest to most formal, what each output is for, how to compare methods, how to download/use a model, and how repository paths match commands.

**Architecture:** Documentation-only change in `README.md`. Insert the new section after `Installation and tests` and before `Benchmark generation`, so users first install/test, then read the experiment roadmap before detailed commands.

**Tech Stack:** Markdown, existing Python CLIs in `scripts/` and `replenishverifier.*`.

## Global Constraints

- Communicate with the user in Chinese.
- Do not use Explore subagents or multi-agent orchestration.
- Do not create a git worktree.
- Do not run real LLM generation.
- Do not run large-scale benchmarks.
- Do not fill any experimental result numbers.
- Do not claim SFT, TGRPO, DPO, RL, PRM, or LoRA training has been completed.
- Formal candidate selection must not use `reference_objective`; reference objectives are evaluation-only.

---

### Task 1: Add README Chinese Experiment Roadmap

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: existing commands documented in README.
- Produces: a new Chinese section `## 中文实验路线：从简单到正式`.

- [ ] **Step 1: Insert section after Installation and tests**

Add a section covering: unit tests, small benchmark, structure sanity check, demo/synthetic candidates, model download/use, real LLM generation, evaluation/comparison, repair/runtime/renaming/preference advanced steps, and path matching rules.

- [ ] **Step 2: Verify no fake result numbers are introduced**

Search the added section conceptually: it must explain what outputs mean and where to compare, but must not provide invented results.

- [ ] **Step 3: Run tests**

Run: `python -m pytest`
Expected: test suite passes; doc-only changes should not break code.

- [ ] **Step 4: Report changed files and test result**

Summarize the README change in Chinese.

## Self-Review

- Spec coverage: The task covers experiment order, output meaning, comparisons, model download/use, and path matching.
- Placeholder scan: No placeholders or result-number slots are introduced.
- Type consistency: All command names match the current README/code surface.
