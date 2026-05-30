# Agent Reference

Each agent is a LangGraph node: a Python function `run(state: WorkflowState) -> dict` that returns a partial state update.

## Evaluator (`agents/evaluator.py`)

**Role:** First agent to see every task. Scores complexity and recommends a benchmark-optimal premium model if warranted.

**Reads:** `state["task"]`

**Writes:** `complexity`, `upgrade_recommendation`, `session_cost`

**Output:** Strict JSON (parsed, not streamed):
```json
{"complexity": "complex", "upgrade_recommendation": {...} | null}
```

**Fallback on parse error:** `{"complexity": "moderate", "upgrade_recommendation": None}`

**Temperature:** 0.0 (deterministic)

---

## Router (`agents/router.py`)

**Role:** Classifies task type and selects the agent pipeline.

**Reads:** `state["task"]`, `state["complexity"]`

**Writes:** `task_type`, `session_cost`

**Valid task_types:** `bug_fix`, `new_feature`, `architecture`, `code_review`, `refactor`, `explain`

**Fallback on parse error:** `bug_fix`

**Temperature:** 0.0 (deterministic)

---

## Researcher (`agents/researcher.py`)

**Role:** Finds everything relevant before any code is written. Greps the target repo (Path.cwd()) and synthesizes findings.

**Reads:** `state["task"]`, `state["task_type"]`

**Writes:** `findings`, `session_cost`

**Tools:** `grep -rn --include=*.py` on Path.cwd(), capped at 3000 chars. Uses first 5 task keywords longer than 4 chars.

**Output format:** Structured markdown with `## Codebase Findings`, `## Web Research`, `## Summary for Downstream Agents` sections. All citations as `file:line` or URL.

**Temperature:** 0.3

---

## Architect (`agents/architect.py`)

**Role:** Designs the implementation plan before Coder writes a line. Only called for `new_feature` and `architecture` task types.

**Reads:** `state["task"]`, `state["findings"]`

**Writes:** `plan`, `session_cost`

**Output format:** Numbered steps with explicit interfaces. `## Risk Flags` section for irreversible changes.

**Temperature:** 0.4

---

## Coder (`agents/coder.py`)

**Role:** Makes the minimal diff that satisfies the requirement. Checks and consumes `interrupt` before finishing.

**Reads:** `state["task"]`, `state["findings"]`, `state["plan"]`, `state["interrupt"]`

**Writes:** `code_changes`, `interrupt` (set to None to consume), `session_cost`

**Output format:** Before/after code blocks per changed file.

**Temperature:** 0.1

---

## Reviewer (`agents/reviewer.py`)

**Role:** Adversarial review. Assumes bugs exist. Checks correctness, security, error handling, edge cases, performance. NOT style.

**Reads:** `state["task"]`, `state["code_changes"]`, `state["findings"]`

**Writes:** `review_feedback`, `session_cost`

**Output:** Numbered issues with `file:line` + fix. Ends with `## Verdict: APPROVED` or `## Verdict: CHANGES REQUESTED`.

**Graph behavior:** `"APPROVED"` (case-insensitive) in `review_feedback` → moves to Verifier. Otherwise → loops back to Coder.

**Temperature:** 0.5 (intentionally higher for adversarial variability)

---

## Verifier (`agents/verifier.py`)

**Role:** Generates tests, runs them in Docker sandbox, reports deterministic pass/fail.

**Reads:** `state["task"]`, `state["code_changes"]`, `state["test_framework"]`

**Writes:** `test_results`, `session_cost`

**test_results shape:** `{passed: bool, stdout: str, stderr: str, timed_out: bool, tests_run: int}`

**Test frameworks:** pytest · cargo · jest · ctest · go-test (from state["test_framework"])

**Temperature:** 0.1

---

## Module-Level Singleton Pattern

All agent modules use a module-level singleton to avoid re-reading AGENTS.md on every call:

```python
class _EvaluatorAgent(BaseAgent):
    role = "evaluator"

_agent = _EvaluatorAgent()  # loaded once at import time

def run(state: WorkflowState) -> dict:
    raw, tokens = _agent.call(user_msg)
    ...
```
