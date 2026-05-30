# WorkflowState — Shared Agent Memory

**File:** `src/forgelab/state.py`

`WorkflowState` is a `TypedDict` that all LangGraph nodes read from and write to. It is the only way agents communicate. Never pass data between agents via function arguments or module globals.

## Field Reference

| Field | Type | Writer | Description |
|-------|------|--------|-------------|
| `task` | `str` | user (api.py) | Raw task input from user |
| `task_type` | `str \| None` | router | `bug_fix` · `new_feature` · `code_review` · `refactor` · `explain` · `architecture` |
| `complexity` | `str \| None` | evaluator | `simple` · `moderate` · `complex` · `critical` |
| `upgrade_recommendation` | `UpgradeRecommendation \| None` | evaluator | Dict with recommended_model, benchmark_reason, score, cost_per_1m; or None |
| `model_in_use` | `str` | evaluator/user | Active model ID string (e.g., `qwen2.5-coder:7b` or `anthropic/claude-sonnet-4-6`) |
| `findings` | `str \| None` | researcher | Structured markdown report with codebase + web research citations |
| `plan` | `str \| None` | architect | Numbered implementation steps with risk flags |
| `code_changes` | `str \| None` | coder | Before/after diff per changed file |
| `review_feedback` | `str \| None` | reviewer | Numbered issues + verdict (`APPROVED` or `CHANGES REQUESTED`) |
| `test_results` | `dict \| None` | verifier | `{passed: bool, stdout: str, stderr: str, timed_out: bool, tests_run: int}` |
| `test_framework` | `str` | api.py (auto-detected) | `pytest` · `cargo` · `jest` · `ctest` · `go-test` — detected from target repo cwd |
| `agent_messages` | `list[dict]` | any agent | A2A messages: `{from, to, content, ts}` |
| `session_cost` | `dict[str, AgentCost]` | any agent | Per-agent token/cost accumulator keyed by agent name |
| `interrupt` | `str \| None` | user (via WebSocket) | Mid-task user injection; Coder checks and consumes this before finishing |

## Supporting TypedDicts

```python
class UpgradeRecommendation(TypedDict):
    task_type: str
    recommended_model: str       # e.g., "anthropic/claude-sonnet-4-6"
    benchmark_reason: str        # one-sentence justification
    score: str                   # e.g., "79.6%"
    cost_per_1m: str             # e.g., "$15"

class AgentCost(TypedDict):
    tokens: int
    cost_usd: float
```

## Access Pattern

```python
# Reading (any agent node function)
task = state["task"]
findings = state.get("findings")  # use .get() for optional fields

# Writing (return a partial dict from the node function)
return {"findings": result, "session_cost": updated_cost}
# LangGraph merges this into the current state — do NOT return full state
```

## Test Framework Auto-Detection (api.py)

Detection order when a new task arrives via WebSocket:
1. `Cargo.toml` exists → `cargo`
2. `package.json` contains "jest" → `jest`
3. `CMakeLists.txt` exists → `ctest`
4. `go.mod` exists → `go-test`
5. Default → `pytest`
