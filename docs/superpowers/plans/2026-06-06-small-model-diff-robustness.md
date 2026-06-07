# Small-Model Diff Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce Coder parse errors when running small models (e.g. `qwen2.5:1.5b`) by adding few-shot examples to the Coder system prompt and a retry loop with explicit corrective feedback in the Coder agent.

**Architecture:** Two independent changes — a prompt edit to `AGENTS.md` (Approach A) and a code change to `coder.py` (Approach B). The retry loop validates output with a lightweight marker check and replaces `user_msg` with corrective feedback on failure, capping at 3 total attempts. `patch_applier.py` remains the downstream fallback and is untouched.

**Tech Stack:** Python 3.12, pytest, unittest.mock

**Spec:** `docs/superpowers/specs/2026-06-06-small-model-diff-robustness-design.md`

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/forgelab/personas/coder/AGENTS.md` | Modify | Add `## Examples` section with 2 few-shot input→output pairs |
| `src/forgelab/agents/coder.py` | Modify | Add `_is_valid_diff()` helper and retry loop |
| `tests/test_coder.py` | Create | TDD tests for `_is_valid_diff` and retry behaviour |

---

### Task 1: Add few-shot examples to Coder system prompt

**Files:**
- Modify: `src/forgelab/personas/coder/AGENTS.md`

- [ ] **Step 1: Read the current file**

```bash
cat src/forgelab/personas/coder/AGENTS.md
```

- [ ] **Step 2: Append the `## Examples` section at the end of the file**

Add this block after the `## Output Format` section (at the very end of the file):

```markdown
## Examples

### Example 1 — single-line fix

Task: Fix `calculate_total` returning wrong value when discount is zero.
Plan: Remove the `or 1` fallback that defaults discount to 1.

--- a/store/pricing.py
+++ b/store/pricing.py
@@ -12,1 +12,1 @@
-    return subtotal / (discount or 1)
+    return subtotal / discount

### Example 2 — new guard clause

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

- [ ] **Step 3: Run existing tests to confirm nothing broke**

```bash
pytest --tb=short -q
```

Expected: 35 passed.

- [ ] **Step 4: Commit**

```bash
git add src/forgelab/personas/coder/AGENTS.md
git commit -m "add few-shot unified diff examples to Coder system prompt"
```

---

### Task 2: Add `_is_valid_diff` and retry loop to `coder.py` (TDD)

**Files:**
- Create: `tests/test_coder.py`
- Modify: `src/forgelab/agents/coder.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_coder.py`:

```python
from unittest.mock import patch


def test_is_valid_diff_true():
    from forgelab.agents.coder import _is_valid_diff

    assert _is_valid_diff(
        "--- a/foo.py\n+++ b/foo.py\n@@ -1,1 +1,1 @@\n-old\n+new"
    ) is True


def test_is_valid_diff_false_prose():
    from forgelab.agents.coder import _is_valid_diff

    assert _is_valid_diff("Here is the fix: change line 5 to return 2.") is False


def test_is_valid_diff_false_before_after():
    from forgelab.agents.coder import _is_valid_diff

    assert _is_valid_diff("# before\nreturn 1\n# after\nreturn 2") is False


def test_coder_retries_on_bad_output():
    from forgelab.agents.coder import run

    responses = [
        ("Here is the fix: change line 5.", 10),
        ("--- a/foo.py\n+++ b/foo.py\n@@ -5,1 +5,1 @@\n-old\n+new", 20),
    ]
    state = {
        "task": "Fix line 5",
        "findings": "Found issue",
        "plan": "Change line 5",
        "interrupt": None,
        "model_in_use": "qwen2.5:1.5b",
        "session_cost": {},
    }

    with patch("forgelab.agents.coder._agent") as mock_agent:
        mock_agent.call.side_effect = responses
        result = run(state)

    assert mock_agent.call.call_count == 2
    assert "--- a/foo.py" in result["code_changes"]


def test_coder_returns_after_max_retries():
    from forgelab.agents.coder import run

    bad_output = "Here is how to fix it: just change the code."
    state = {
        "task": "Fix something",
        "findings": "None",
        "plan": "Do it",
        "interrupt": None,
        "model_in_use": "qwen2.5:1.5b",
        "session_cost": {},
    }

    with patch("forgelab.agents.coder._agent") as mock_agent:
        mock_agent.call.return_value = (bad_output, 10)
        result = run(state)

    assert mock_agent.call.call_count == 3
    assert result["code_changes"] == bad_output


def test_coder_no_retry_on_valid_diff():
    from forgelab.agents.coder import run

    valid = "--- a/foo.py\n+++ b/foo.py\n@@ -1,1 +1,1 @@\n-old\n+new"
    state = {
        "task": "Fix something",
        "findings": "None",
        "plan": "Do it",
        "interrupt": None,
        "model_in_use": "qwen2.5:1.5b",
        "session_cost": {},
    }

    with patch("forgelab.agents.coder._agent") as mock_agent:
        mock_agent.call.return_value = (valid, 15)
        result = run(state)

    assert mock_agent.call.call_count == 1
    assert result["code_changes"] == valid
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_coder.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name '_is_valid_diff'`

- [ ] **Step 3: Implement `_is_valid_diff` and retry loop in `coder.py`**

Replace the entire contents of `src/forgelab/agents/coder.py` with:

```python
"""Coder — minimal diff implementation."""
from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _CoderAgent(BaseAgent):
    role = "coder"


_agent = _CoderAgent()

_MAX_ATTEMPTS = 3


def _is_valid_diff(text: str) -> bool:
    return "---" in text and "+++" in text and "@@" in text


def run(state: WorkflowState) -> dict:
    interrupt_note = ""
    if state.get("interrupt"):
        interrupt_note = f"\n\n⚡ User interrupt: {state['interrupt']}\nAdapt your implementation accordingly."

    user_msg = (
        f"Task: {state['task']}\n\n"
        f"Researcher findings:\n{state.get('findings', '(none)')}\n\n"
        f"Architect plan:\n{state.get('plan', '(none)')}"
        f"{interrupt_note}"
    )

    raw, tokens_total = "", 0
    for attempt in range(_MAX_ATTEMPTS):
        raw, tokens = _agent.call(user_msg)
        tokens_total += tokens
        if _is_valid_diff(raw):
            break
        if attempt < _MAX_ATTEMPTS - 1:
            user_msg = (
                f"That output is not a unified diff.\n\n"
                f"Your previous output was:\n{raw}\n\n"
                f"Output ONLY a unified diff. Nothing else. "
                f"It must contain --- a/..., +++ b/..., and @@ lines."
            )

    update: dict = {"code_changes": raw, "interrupt": None}
    update.update(BaseAgent._add_cost(state, "coder", tokens_total))
    return update
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_coder.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run full suite**

```bash
pytest --tb=short -q
```

Expected: 40 passed (35 existing + 5 new).

- [ ] **Step 6: Commit**

```bash
git add src/forgelab/agents/coder.py tests/test_coder.py
git commit -m "add diff validation and retry loop to Coder for small model robustness"
```

---

## Verification Checklist

1. `pytest --tb=short -q` → 40 passed
2. `grep -A2 "## Examples" src/forgelab/personas/coder/AGENTS.md` → shows the two examples
3. `grep "_is_valid_diff\|_MAX_ATTEMPTS" src/forgelab/agents/coder.py` → both present
