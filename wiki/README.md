# ForgeLab v2 — LLM Wiki

> **For agents and Claude Code:** This wiki is the canonical reference for the ForgeLab v2 codebase. Read it before touching any file. It is kept current — every file creation or significant change is reflected here.

## What Is ForgeLab?

ForgeLab is a repo-agnostic multi-agent software engineering assistant. Users run `forgelab start` from the root of **any target repository**. ForgeLab never needs to be cloned into the project.

One Ollama model is shaped into 7 expert agents via per-agent persona files (`SKILL.md`, `SOUL.md`, `AGENTS.md`). LangGraph orchestrates the workflow. FastAPI streams events over WebSocket to a React frontend.

## Quick Architecture Reference

```
User task (text) → WebSocket /ws
  → Evaluator (complexity + upgrade rec)
  → Router (task_type + pipeline)
  → Researcher (grep codebase + web browse)
  → [Architect] (plan, for new_feature / architecture)
  → Coder (minimal diff)
  → Reviewer (adversarial review, loops back to Coder if not APPROVED)
  → Verifier (Docker test run)
  → workflow_complete event → React UI
```

## Directory Map

| Path | Purpose |
|------|---------|
| `src/forgelab/state.py` | `WorkflowState` TypedDict — shared memory all agents read/write |
| `src/forgelab/llm.py` | Unified LLM gateway — Ollama-first, OpenRouter fallback |
| `src/forgelab/cli.py` | `forgelab start` CLI entry point |
| `src/forgelab/graph.py` | LangGraph workflow — wires all 7 agent nodes |
| `src/forgelab/api.py` | FastAPI + WebSocket streaming server |
| `src/forgelab/executor.py` | Docker sandbox for deterministic test execution |
| `src/forgelab/agents/base.py` | `BaseAgent` — loads AGENTS.md, exposes `call()` |
| `src/forgelab/agents/evaluator.py` | Complexity scorer + upgrade recommender |
| `src/forgelab/agents/router.py` | Task classifier + pipeline selector |
| `src/forgelab/agents/researcher.py` | Codebase grep + web browse synthesis |
| `src/forgelab/agents/architect.py` | Implementation planner |
| `src/forgelab/agents/coder.py` | Minimal diff implementer |
| `src/forgelab/agents/reviewer.py` | Adversarial code reviewer |
| `src/forgelab/agents/verifier.py` | Test generator + Docker executor |
| `src/forgelab/personas/` | Bundled agent persona data (package data) |
| `frontend/src/` | React + TypeScript + Vite UI |
| `benchmark_registry.yaml` | Task-type → recommended model mappings |
| `agent_personas.yaml` | Agent config: base model, temperatures |

## Key Invariants Every Agent Must Know

1. **`Path.cwd()` is always the target repo.** ForgeLab runs via `forgelab start` from the user's project root. Never use `Path(__file__)` to access the user's code.
2. **Persona files live inside the package.** `_PERSONAS_DIR = Path(__file__).parent.parent / "personas"` — always resolves to the installed package, never the target repo.
3. **All agents share `WorkflowState` via LangGraph.** Never pass data between agents any other way.
4. **LLM calls go through `call_llm()` only.** Never instantiate an OpenAI/Ollama client directly in agent code.
5. **Reviewer loops until "APPROVED".** The graph has a coder → reviewer → coder loop. Reviewer output must contain "APPROVED" (case-insensitive) to exit.
6. **Verifier trusts execution, not the LLM.** `executor.run_test()` is ground truth. The LLM generates test code; Docker runs it.

## Wiki Index

| File | Contents |
|------|---------|
| [architecture.md](architecture.md) | Detailed architecture, data flow, design decisions |
| [state.md](state.md) | `WorkflowState` field-by-field reference |
| [llm-gateway.md](llm-gateway.md) | LLM routing — Ollama vs OpenRouter, how to call |
| [agent-personas.md](agent-personas.md) | Persona file format (SKILL/SOUL/AGENTS.md) |
| [agents.md](agents.md) | Each agent's role, inputs, outputs, behavior |
| [graph.md](graph.md) | LangGraph workflow — nodes, edges, routing logic |
| [api-protocol.md](api-protocol.md) | WebSocket message protocol (server↔client) |
| [frontend.md](frontend.md) | React component tree and UI state |
| [executor.md](executor.md) | Docker sandbox — how tests are run |
| [config.md](config.md) | Config files: benchmark_registry.yaml, agent_personas.yaml |
