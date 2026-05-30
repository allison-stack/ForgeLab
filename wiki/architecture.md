# Architecture — ForgeLab v2

## Design Philosophy

**One model, seven minds.** A single Ollama model is shaped into 7 distinct expert agents entirely through persona files (SKILL.md, SOUL.md, AGENTS.md). The same base weights produce a cautious gatekeeper (Evaluator), a fast classifier (Router), and an adversarial reviewer (Reviewer) because each agent's system prompt, temperature, and character definition are distinct.

**Repo-agnostic.** `pip install forgelab` + `forgelab start` from any project root. ForgeLab never modifies the target repo directly — agents read it (via grep/read_file tools) and produce diff output that the user applies.

**LangGraph as shared memory.** `WorkflowState` is the single source of truth. No agent-to-agent function calls — they all read from and write to state.

## Data Flow

```
1. User submits task via WebSocket {type: "task", task: "..."}
2. api.py creates initial WorkflowState, calls _graph.astream()
3. LangGraph executes nodes in sequence:

   evaluator.run(state) → {complexity, upgrade_recommendation, session_cost}
     ↓
   [Optional] api.py sends upgrade_prompt to UI, waits for user response
     ↓
   router.run(state) → {task_type, session_cost}
     ↓
   researcher.run(state) → {findings, session_cost}
     ↓
   [If new_feature/architecture] architect.run(state) → {plan, session_cost}
     ↓
   coder.run(state) → {code_changes, interrupt: None, session_cost}
     ↓
   reviewer.run(state) → {review_feedback, session_cost}
     ↓
   [Loop back to coder if "APPROVED" not in review_feedback]
     ↓
   verifier.run(state) → {test_results, session_cost}
     ↓
4. api.py sends workflow_complete to UI
```

## Streaming Events (api.py → frontend)

Each node completion emits:
- `agent_status` (running → done/reviewing)
- `chat_message` (the agent's output)
- `cost_update` (tokens used)
- `upgrade_prompt` (evaluator only, if recommended)
- `browser_update` (researcher, if browsed web)
- `test_result` (verifier, per test)
- `workflow_complete`

## Conditional Routing

```python
# After router:
always → researcher  # all task types start with research

# After researcher:
explain → END
code_review → reviewer
new_feature, architecture → architect
bug_fix, refactor, else → coder

# After reviewer:
"APPROVED" in feedback → verifier
else → coder  # revision loop
```

## Package Structure

```
src/forgelab/           # Python package
├── state.py            # WorkflowState TypedDict
├── llm.py              # Unified LLM gateway
├── cli.py              # forgelab start command
├── graph.py            # LangGraph workflow
├── api.py              # FastAPI + WebSocket
├── executor.py         # Docker test sandbox
├── agents/
│   ├── base.py         # BaseAgent + AGENTS.md parser
│   ├── evaluator.py    # Complexity + upgrade recommendation
│   ├── router.py       # Task classification
│   ├── researcher.py   # Codebase + web research
│   ├── architect.py    # Implementation planning
│   ├── coder.py        # Code generation
│   ├── reviewer.py     # Adversarial review
│   └── verifier.py     # Test generation + execution
└── personas/           # Bundled persona data (package data)
    ├── _shared/MEMORY_SCHEMA.md
    ├── evaluator/{SKILL,SOUL,AGENTS}.md
    ├── router/{SKILL,SOUL,AGENTS}.md
    ├── researcher/{SKILL,SOUL,AGENTS}.md
    ├── architect/{SKILL,SOUL,AGENTS}.md
    ├── coder/{SKILL,SOUL,AGENTS}.md
    ├── reviewer/{SKILL,SOUL,AGENTS}.md
    └── verifier/{SKILL,SOUL,AGENTS}.md

frontend/               # React + TypeScript + Vite
├── src/
│   ├── types.ts        # WSMessage + UI state types
│   ├── styles.css      # CSS variables + animations
│   ├── hooks/useWorkflow.ts  # WebSocket state machine
│   └── components/
│       ├── TopBar.tsx
│       ├── AgentPanel.tsx
│       ├── ChatArea.tsx
│       └── DetailsPanel.tsx
```

## Technology Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| LLM serving | Ollama (OpenAI-compatible API) | Local, free, no API key needed |
| LLM routing | OpenAI SDK | Works with both Ollama and OpenRouter |
| Agent orchestration | LangGraph | StateGraph gives conditional routing + shared state |
| Streaming | WebSocket | Bidirectional: server pushes events, client sends interrupts |
| Frontend | React + Vite + CSS vars | Fast dev, no framework overhead, full design control |
| Test execution | Docker sandbox | Deterministic, isolated, prevents LLM hallucination about test results |
| Package distribution | hatchling + pip | `pip install forgelab` installs personas as package data |
