# ForgeLab Benchmark Design

**Status:** Implemented  
**Date:** 2026-06-01  
**Author:** ForgeLab Capstone Project

---

## Context

ForgeLab is a multi-agent coding assistant built on LangGraph. This benchmark measures its real-world performance against SWE-bench Lite — a curated set of 300 real GitHub issues with reproducible tests. Results are compared to a single-LLM baseline to isolate the contribution of the multi-agent pipeline.

---

## Pre-Requisite

The Coder persona must output unified diffs (not before/after blocks). Updated in `src/forgelab/personas/coder/AGENTS.md`.

---

## What Gets Built

`forgelab benchmark [--tasks benchmark/tasks.json] [--output benchmark/results/]`

For each of 15 randomly sampled SWE-bench Lite tasks (seed=42):

1. Clone repo at `base_commit` (buggy state)
2. Run ForgeLab (`graph.ainvoke` directly, no WebSocket)
3. Apply Coder's unified diff output to real repo files via `patch_applier.py`
4. Run `fail_to_pass` tests → passed? + `pass_to_pass` tests → regression?
5. Reset repo, run single-LLM baseline (same model, one-shot prompt)
6. Same tests on baseline result

Output: `benchmark/results/results.json` (per-task) + `summary.csv` (pass rates table).

---

## Task Dataset

- **Source:** `princeton-nlp/SWE-bench_Lite` (HuggingFace Datasets)
- **Sample:** 15 tasks, seed=42 → reproducible across runs
- **Committed:** `benchmark/tasks.json` (does not re-download on each run)
- **Fields per task:** `instance_id`, `repo`, `base_commit`, `issue_text`, `fail_to_pass`, `pass_to_pass`

---

## Per-Task Execution Flow

```
graph.ainvoke(initial_state)
    → Supervisor routes to Researcher → Planner → Coder → Reviewer
    → Coder outputs unified diff in code_changes field
    → patch_applier applies diff to cloned repo
    → pytest runs fail_to_pass tests
    → git checkout . resets repo
    → baseline.run_baseline() runs one-shot LLM call
    → patch_applier applies baseline diff
    → pytest runs fail_to_pass tests again
```

---

## Patch Applier

3-level fallback in `src/forgelab/patch_applier.py`:

| Level | What | Return value |
|---|---|---|
| 1 | Direct `patch -p1` | `"applied"` |
| 2 | Strip markdown fences, retry | `"stripped"` |
| 3 | LLM converts to valid diff | `"reformatted"` |
| fail | All levels fail | `"parse_error"` |

`parse_error` → task counted as failed; benchmark continues.

---

## Single-LLM Baseline

`src/forgelab/baseline.py`:
- Same model as ForgeLab Coder (`OLLAMA_MODEL` env var)
- Greps repo for relevant files by keyword
- One-shot prompt: issue text + relevant files → unified diff
- Only variable between ForgeLab and baseline: the multi-agent pipeline

---

## Report Format

**results.json** (per task):
```json
{
  "instance_id": "...",
  "forgelab_passed": true,
  "forgelab_iterations": 1,
  "forgelab_tokens": 3200,
  "forgelab_parse_error": false,
  "baseline_passed": false,
  "baseline_parse_error": false,
  "fail_to_pass_tests": ["tests/test_foo.py::test_bar"],
  "regression": false
}
```

**summary.csv**: same fields, one row per task.

**Console summary:**
```
============================================================
Benchmark complete: 15 tasks
ForgeLab:  8/15 passed (53.3%) | 2 parse errors | avg 1.3 iterations
Baseline:  4/15 passed (26.7%) | 3 parse errors
Reference: Claude Sonnet 4.6 scored 79.6% on full SWE-bench Lite (April 2025)
============================================================
```

---

## Verification

```bash
# CLI help
forgelab benchmark --help             # shows --tasks and --output
forgelab benchmark --tasks bad.json   # exits with "not found"

# Tests
pytest --tb=short -q                  # all 35 tests pass

# Full run
forgelab benchmark                    # runs all 15 tasks, writes results/
```

---

## Non-Official Evaluation

Results are labeled "non-official evaluation" — we use real SWE-bench Lite data but not the official Docker harness. Scores may differ from official leaderboard numbers.
