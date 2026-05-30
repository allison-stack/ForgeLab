# Shared Memory Schema

All agents read and write `WorkflowState` via LangGraph. Never access raw
LangGraph internals — use the typed fields below.

| Field | Type | Writer | Description |
|---|---|---|---|
| `task` | str | user | Raw task input |
| `task_type` | str \| None | router | bug_fix · new_feature · code_review · refactor · explain · architecture |
| `complexity` | str \| None | evaluator | simple · moderate · complex · critical |
| `upgrade_recommendation` | dict \| None | evaluator | {recommended_model, benchmark_reason, score, cost_per_1m} or null |
| `model_in_use` | str | evaluator/user | Active model ID |
| `findings` | str \| None | researcher | Codebase + web research results |
| `plan` | str \| None | architect | Implementation plan steps |
| `code_changes` | str \| None | coder | Diffs + explanations |
| `review_feedback` | str \| None | reviewer | Issues found (empty string = approved) |
| `test_results` | dict \| None | verifier | {passed: bool, stdout: str, tests_run: int} |
| `test_framework` | str | auto-detected | pytest · cargo · jest · ctest · go-test — auto-detected from cwd, defaults to "pytest" |
| `agent_messages` | list[dict] | any | A2A messages: {from, to, content, ts} |
| `session_cost` | dict | any | {agent_name: {tokens: int, cost_usd: float}} |
| `interrupt` | str \| None | user | Mid-task injection; agents check after each step |

## Access pattern

```python
# Read
task = state["task"]
findings = state.get("findings")

# Write (return a partial dict from your node function)
return {"findings": result, "session_cost": updated_cost}
```
