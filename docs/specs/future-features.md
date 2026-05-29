# ForgeLab — Future Features

Planned enhancements beyond the v2 MVP. Each entry captures the intent and open design questions so the idea isn't lost.

---

## Agent Tool Access via MCP + Composio

**Status:** Concept  
**Motivation:** The v2 implementation plan gives each agent a small set of hand-rolled Python tools (`search_codebase`, `read_file`, `browse_web`, `executor`). These cover the demo scenario but are brittle — every new capability requires writing and maintaining a custom function. Real engineering workflows need agents to reach GitHub issues, Jira tickets, Slack threads, CI logs, database schemas, and more. Building each of those from scratch doesn't scale.

**Current tool coverage per agent (v2 plan):**

| Agent | Current tools |
|---|---|
| Evaluator | none |
| Router | none |
| Researcher | search_codebase, read_file, browse_web (Playwright) |
| Architect | search_codebase, read_file |
| Coder | search_codebase, read_file |
| Reviewer | search_codebase, read_file |
| Verifier | executor (Docker sandbox), read_file |

**Proposed design:**  
Replace or augment bespoke tools with [MCP (Model Context Protocol)](https://modelcontextprotocol.io) — the emerging standard for connecting LLM agents to external tools. Use **Composio** as the MCP tool provider: it exposes 250+ pre-authenticated integrations as MCP-compatible tools, handling OAuth, credential management, and schema generation so agents can call real services without custom wiring.

LangGraph supports tool-calling natively via `ToolNode`; wiring Composio MCP tools in means each agent's AGENTS.md `## Tools` section lists real Composio action slugs rather than bespoke functions.

**High-value tools per agent:**

| Agent | Composio / MCP tools to add |
|---|---|
| Researcher | `GITHUB_GET_AN_ISSUE`, `GITHUB_LIST_PULL_REQUESTS`, `JIRA_GET_ISSUE`, `LINEAR_GET_ISSUE`, `GITHUB_SEARCH_CODE` |
| Coder | `GITHUB_CREATE_A_PULL_REQUEST`, `GITHUB_CREATE_BLOB`, `GITHUB_UPDATE_A_FILE` |
| Reviewer | `GITHUB_CREATE_REVIEW_COMMENT`, `GITHUB_REQUEST_REVIEWERS` |
| Verifier | `GITHUB_LIST_WORKFLOW_RUNS` (check CI), `SLACK_SENDS_A_MESSAGE` (notify on pass/fail) |
| Architect | `NOTION_CREATE_PAGE`, `LINEAR_CREATE_ISSUE` (write plan to tracker) |

**Why Composio specifically:**
- Auth is managed once per app (OAuth flow in CLI: `composio add github`) — agents never handle tokens
- Every tool has a typed JSON schema; LangGraph can pass it directly to the OpenAI function-calling API
- New integrations are added by listing a slug, not writing code
- Works with any LLM backend (Ollama via OpenAI-compatible API supports function calling)

**Integration sketch:**
```python
from composio_langchain import ComposioToolSet, Action

toolset = ComposioToolSet()
researcher_tools = toolset.get_tools(actions=[
    Action.GITHUB_GET_AN_ISSUE,
    Action.GITHUB_SEARCH_CODE,
    Action.LINEAR_GET_ISSUE,
])
# Pass to LangGraph ToolNode — no other changes needed
```

**Open questions:**
- Should tool access be declared in each agent's AGENTS.md `## Tools` section (keeping persona files authoritative) or configured separately in `agent_personas.yaml`?
- Composio requires a cloud account for auth management — is there a self-hosted or local-only option acceptable for privacy-focused users who don't want to send credentials to a third party?
- For Ollama models that don't support function calling natively, how are tool calls handled — ReAct prompting, a local tool-calling shim, or restrict MCP tools to premium-model sessions only?
- Should the user explicitly grant each agent its tool permissions, or inherit a default set from the task type?

---

## Planning Agent (Task Decomposition)

**Status:** Concept  
**Motivation:** The current Router selects a pre-defined pipeline for a single task type. It has no way to handle compound tasks like *"fix the login bug, refactor the auth module, and update the API docs"* — it classifies the whole input as one task type and runs a single pipeline.

**Proposed design:**  
Insert a **Planning Agent** as the second node in the graph, between Evaluator and Router:

```
Evaluator → Planner → Router(s) → [agent pipelines]
```

The Planner's job:
1. Analyze the raw task for multiple independent concerns
2. If compound: decompose into N atomic subtasks, each with a clear scope and expected output
3. Assign each subtask to the appropriate role pipeline (bug_fix → researcher→coder→reviewer→verifier, etc.)
4. If atomic: pass through unchanged

Each decomposed subtask would then flow through Evaluator → Router as an independent unit — enabling parallel execution of independent concerns and clean per-subtask cost tracking.

**Open questions:**
- Should subtasks execute in parallel (fan-out from Planner) or sequentially?
- How does the UI represent multiple in-flight subtask pipelines simultaneously?
- Should the user review and approve the decomposition before execution begins?
- For dependent subtasks (e.g., "refactor auth, then update the tests that rely on it"), how is ordering enforced?
- Does the Planner also estimate which subtasks benefit from a premium model, or does each subtask's Evaluator do that independently?

---

## Evaluator — Per-Subtask Model Recommendation

**Status:** Concept  
**Motivation:** In v2, the Evaluator runs first and scores the entire task as one unit. Once the Planning Agent exists, scoring the whole task is too coarse — a compound task like "fix auth bug + write API docs + add logging" has three subtasks with very different complexity profiles and optimal models. Recommending one premium model for everything wastes money on the easy parts.

**Proposed design:**  
Move the Evaluator to run *after* the Planner, once subtasks exist:

```
Planner → Evaluator (per subtask) → Router(s) → [agent pipelines]
```

The Evaluator would receive the full list of subtasks from the Planner and score each one independently — assigning a complexity level and, where warranted, a benchmark-optimal model recommendation specific to that subtask's type and scope. Simple subtasks stay on the local Ollama model; only the subtasks that genuinely need it get routed to a premium model.

This makes the upgrade prompt more granular and honest: *"Subtask 2 of 3 (new feature, complex) — recommend claude-opus-4-8 at $75/1M. Subtasks 1 and 3 are simple, no upgrade needed."*

**Open questions:**
- Should the user get one combined upgrade decision or a separate prompt per subtask?
- If a subtask is marked for upgrade but the user declines, does it still run on local or get skipped?
- Does per-subtask scoring change `benchmark_registry.yaml`'s structure, or just how the Evaluator calls it?

---

## Evaluator — Live Benchmark Refresh

**Status:** Concept  
**Motivation:** `benchmark_registry.yaml` is static — written once and committed. Model rankings change frequently: new models release, SWE-bench leaderboard updates, cost per token shifts. A hardcoded registry becomes stale within weeks, and the Evaluator's recommendations quietly degrade in accuracy without anyone noticing.

**Proposed design:**  
Add a background refresh job that periodically scrapes authoritative benchmark sources and updates `benchmark_registry.yaml` (or a cached overlay) in place:

- **Sources to watch:** SWE-bench Verified leaderboard, MMLU-Pro leaderboard, Chatbot Arena ELO rankings, OpenRouter model pricing API
- **Cadence:** Weekly cron or on-demand via a CLI flag (`forgelab update-benchmarks`)
- **Update strategy:** Only overwrite entries where a newer model scores meaningfully higher (e.g., >2% on the same benchmark) — avoid churn from noise
- **Transparency:** Log what changed and why; show a "last updated" timestamp in the UI's model recommendation card so the user knows how fresh the data is

**Open questions:**
- Should the refresh be a separate Python script, a scheduled FastAPI background task, or a standalone CLI command?
- How should conflicting data across sources be resolved (e.g., model A wins SWE-bench but loses Chatbot Arena for the same task type)?
- Should users be able to pin a registry version to avoid unexpected model switches mid-project?
