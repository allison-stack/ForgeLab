# Small-Model Diff Robustness Design

**Status:** Approved  
**Date:** 2026-06-06

---

## Problem

Small models (e.g. `qwen2.5:1.5b`) frequently ignore the Coder agent's unified diff instruction and produce prose, before/after blocks, or incomplete output instead. The existing `patch_applier.py` 3-level fallback handles bad output after the fact, but a 1.5b model also fails at level 3 (LLM reformatter), so parse errors are near-certain.

---

## Goal

Reduce Coder parse errors when running small models, without changing the LLM infrastructure or adding dependencies.

---

## Scope

Changes are limited to two files:

| File | Change |
|---|---|
| `src/forgelab/personas/coder/AGENTS.md` | Add `## Examples` section with 2 few-shot input→output pairs |
| `src/forgelab/agents/coder.py` | Wrap `_agent.call()` in a retry loop (max 3 attempts) |

No changes to `llm.py`, `patch_applier.py`, `baseline.py`, or any other file.

---

## Approach A: Few-Shot Examples in `AGENTS.md`

Add an `## Examples` section to the Coder system prompt. Small models generalise from concrete examples far more reliably than from abstract instructions alone.

Two examples are sufficient — one single-line fix, one multi-line addition. They must be short enough not to bloat the context window (~100 tokens total).

### Example 1 — single-line fix

```
Task: Fix `calculate_total` returning wrong value when discount is zero.
Plan: Remove the `or 1` fallback that defaults discount to 1.

--- a/store/pricing.py
+++ b/store/pricing.py
@@ -12,1 +12,1 @@
-    return subtotal / (discount or 1)
+    return subtotal / discount
```

### Example 2 — new guard clause

```
Task: Raise ValueError when `radius` is negative in `Circle.__init__`.
Plan: Add an early validation check before assigning self.radius.

--- a/shapes/circle.py
+++ b/shapes/circle.py
@@ -4,2 +4,4 @@
 def __init__(self, radius: float) -> None:
+    if radius < 0:
+        raise ValueError("radius must be non-negative")
     self.radius = radius
```

---

## Approach B: Retry Loop in `coder.py`

After each `_agent.call()`, validate the output with a lightweight check. If invalid, retry with explicit corrective feedback showing the model what it produced. Cap at 3 total attempts (initial + 2 retries).

### Validation

```python
def _is_valid_diff(text: str) -> bool:
    return "---" in text and "+++" in text and "@@" in text
```

Intentionally permissive — checks for required markers only, not syntactic correctness. `patch_applier._try_apply` remains the strict validator downstream.

### Retry prompt

On each failed attempt (except the last), replace `user_msg` with:

```
That output is not a unified diff.

Your previous output was:
{raw}

Output ONLY a unified diff. Nothing else.
It must contain --- a/..., +++ b/..., and @@ lines.
```

This keeps the feedback tight — the model sees its mistake and the corrective instruction without the original task context growing unbounded.

### After 3 attempts

Whatever `raw` holds is passed to `patch_applier` unchanged. The 3-level fallback in `patch_applier` remains the last line of defence.

---

## Data Flow

```
coder.py run()
  └─ attempt 1: _agent.call(original user_msg)
       ├─ _is_valid_diff() → True  → return raw
       └─ False → build corrective user_msg
  └─ attempt 2: _agent.call(corrective user_msg)
       ├─ _is_valid_diff() → True  → return raw
       └─ False → build corrective user_msg
  └─ attempt 3: _agent.call(corrective user_msg)
       └─ return raw regardless
  → patch_applier.apply_patch(raw, repo_dir)
       level 1: direct patch
       level 2: strip markdown fences
       level 3: LLM reformat
       → "parse_error" if all fail
```

---

## Testing

Existing tests in `tests/test_patch_applier.py` and `tests/test_benchmark_cli.py` are unaffected. New tests needed:

| Test | File | What it checks |
|---|---|---|
| `test_is_valid_diff_true` | `tests/test_coder.py` | Returns True for a string with `---`, `+++`, `@@` |
| `test_is_valid_diff_false` | `tests/test_coder.py` | Returns False for prose output |
| `test_coder_retries_on_bad_output` | `tests/test_coder.py` | Calls `_agent.call` up to 3 times when output is invalid; stops early when valid |
| `test_coder_returns_after_max_retries` | `tests/test_coder.py` | Returns raw output after 3 attempts even if still invalid |

---

## Non-Goals

- Structured output / JSON envelope (Approach C) — deferred; adds infrastructure complexity without closing the content gap
- Improving Researcher, Planner, or Reviewer output — they produce natural language, no format constraint needed
- Changing `patch_applier.py` — its fallback chain is already correct
