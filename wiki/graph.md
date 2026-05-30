# LangGraph Workflow — `src/forgelab/graph.py`

## Overview

`build_graph()` returns a compiled LangGraph `StateGraph` that wires all 7 agent nodes with conditional routing. Called once at module level in `api.py`.

## Node List

| Node | Module | Entry point |
|------|--------|-------------|
| `evaluator` | `agents/evaluator.py` | `evaluator.run` |
| `router` | `agents/router.py` | `router.run` |
| `researcher` | `agents/researcher.py` | `researcher.run` |
| `architect` | `agents/architect.py` | `architect.run` |
| `coder` | `agents/coder.py` | `coder.run` |
| `reviewer` | `agents/reviewer.py` | `reviewer.run` |
| `verifier` | `agents/verifier.py` | `verifier.run` |

## Edges

```python
g.set_entry_point("evaluator")
g.add_edge("evaluator", "router")
g.add_conditional_edges("router", _route_after_router)
g.add_conditional_edges("researcher", _route_after_researcher)
g.add_edge("architect", "coder")
g.add_edge("coder", "reviewer")
g.add_conditional_edges("reviewer", _route_after_reviewer)
g.add_edge("verifier", END)
```

## Routing Functions

```python
def _route_after_router(state) -> str:
    # All task types → researcher first
    return "researcher"

def _route_after_researcher(state) -> str:
    task_type = state.get("task_type", "bug_fix")
    if task_type in ("new_feature", "architecture"):
        return "architect"
    if task_type == "code_review":
        return "reviewer"
    if task_type == "explain":
        return END
    return "coder"  # bug_fix, refactor, and anything else

def _route_after_reviewer(state) -> str:
    feedback = state.get("review_feedback", "")
    if "APPROVED" in feedback.upper():
        return "verifier"
    return "coder"  # revision loop
```

## Streaming

`api.py` uses `_graph.astream(initial_state, stream_mode="updates")` which yields `{node_name: state_update}` after each node completes.

## Build Pattern

```python
# api.py — built once at module level
_graph = build_graph()

# In WebSocket handler:
async for event in _graph.astream(initial_state, stream_mode="updates"):
    for node_name, update in event.items():
        # stream events to client
```
