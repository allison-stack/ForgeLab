# Backend Implementation Reference

> Phase 2 is complete. All Python modules are written and 14 tests pass.

## Module Summary

| File | Status | Tests |
|------|--------|-------|
| `src/forgelab/state.py` | ✅ Done | (type definitions, no tests needed) |
| `src/forgelab/llm.py` | ✅ Done | `tests/test_llm.py` (2 tests) |
| `src/forgelab/agents/base.py` | ✅ Done | `tests/test_base_agent.py` (3 tests) |
| `src/forgelab/agents/evaluator.py` | ✅ Done | `tests/test_evaluator.py` (2 tests) |
| `src/forgelab/agents/router.py` | ✅ Done | `tests/test_router.py` (4 tests) |
| `src/forgelab/agents/researcher.py` | ✅ Done | (tested via integration) |
| `src/forgelab/agents/architect.py` | ✅ Done | (tested via integration) |
| `src/forgelab/agents/coder.py` | ✅ Done | (tested via integration) |
| `src/forgelab/agents/reviewer.py` | ✅ Done | (tested via integration) |
| `src/forgelab/agents/verifier.py` | ✅ Done | (tested via integration) |
| `src/forgelab/graph.py` | ✅ Done | `tests/test_graph.py` (2 tests) |
| `src/forgelab/api.py` | ✅ Done | `tests/test_api.py` (1 test) |

**Total tests:** 14 passing

## Key Implementation Patterns

### Module-level singleton pattern (all agent modules)
```python
class _EvaluatorAgent(BaseAgent):
    role = "evaluator"

_agent = _EvaluatorAgent()  # reads AGENTS.md once at import time

def run(state: WorkflowState) -> dict:
    raw, tokens = _agent.call(user_msg)
    ...
    return update
```

Loading the agent once at import is important — it reads the AGENTS.md file from disk. Doing it per-call would be slow.

### State update pattern
All `run()` functions return a *partial* dict — only the fields they changed:
```python
update = {"complexity": "complex", "upgrade_recommendation": None}
update.update(BaseAgent._add_cost(state, "evaluator", tokens))
return update
# LangGraph merges this into the full state — don't return the whole state
```

### JSON parse defense (evaluator, router)
```python
try:
    parsed = json.loads(raw)
except json.JSONDecodeError:
    parsed = {"complexity": "moderate", "upgrade_recommendation": None}
```
Never crash on bad LLM output — fall back to a safe default.

### Interrupt consumption (coder)
```python
update: dict = {"code_changes": raw, "interrupt": None}  # consume interrupt
```
Coder sets interrupt to None after reading it so it doesn't re-apply on retries.

## Running the Backend

```bash
# From the forgelab repo:
pip install -e .
cp .env.example .env
# Edit .env: set OLLAMA_MODEL to a model you have pulled

forgelab start          # starts at http://127.0.0.1:8000
# or
uvicorn forgelab.api:app --reload --port 8000

# Verify:
curl http://localhost:8000/health
# → {"status":"ok"}
```
