# TestForge Multi-Agent SE Team — Product Requirements Document

## 1. Executive Summary

TestForge is being redesigned from a mutation-testing research prototype into a multi-agent software engineering system. The product assembles a team of specialized AI agents — each powered by the optimal LLM for its role based on public benchmark data — that collaborates autonomously on any software engineering task while the user watches and intervenes in real time.

### Why this exists

Current AI coding tools (Claude Code, Cursor, Copilot) use a single model for everything. This is suboptimal: architecture decisions need deep reasoning (Opus-tier), implementation needs strong coding ability (Sonnet-tier), and simple classification needs speed (Haiku-tier). Research shows teams using tiered model routing save 60-70% on cost with no meaningful quality loss, and heterogeneous model review catches bugs that same-model review misses.

No existing tool combines intelligent per-role model selection with a transparent, interruptible multi-agent workflow visible to the user.

### Core differentiators

- **Specialized agents with benchmark-optimal model defaults** — not one model doing everything
- **Heterogeneous review** — Reviewer deliberately uses a different model family than Coder to catch blind spots
- **Full transparency** — user sees every agent's work in real time via web UI
- **User interrupt at any time** — inject guidance mid-task, agents adapt dynamically
- **Researcher with live browser** — visible web research, not hidden RAG

---

## 2. Target User

Individual developers who use AI coding tools and want:
- Better results through model specialization (right model for right task)
- Transparency into what the AI is actually doing
- Ability to guide and correct mid-task rather than accepting/rejecting at the end
- Reduced cost by not using expensive models for simple sub-tasks

---

## 3. Competitive Landscape

| Tool | What it does | Gap TestForge fills |
|------|-------------|-------------------|
| Claude Code / Cursor | Single model does everything | No per-task model optimization, no agent specialization |
| Kilo Code | User picks models per mode (plan/execute) | Modes, not collaborating agent roles. No verification loop. |
| OpenHands | Multi-agent with per-agent model support | No intelligent defaults from benchmarks. No live browser visibility. No user interrupt. |
| Devin | Autonomous coding agent | Proprietary black box. No transparency. No user control. |
| MetaGPT / ChatDev | Software team simulation | Single model across all roles. No real-time UI. No dynamic user interaction. |
| AutoGen | Per-agent model config | Framework, not product. No UI. No benchmark-driven defaults. |

---

## 4. System Architecture

### 4.1 High-level overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                         │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │Agent Sidebar│  │ Chat Stream  │  │ Browser Panel   │  │
│  │(status,cost)│  │(expandable)  │  │(slides in/out)  │  │
│  └────────────┘  └──────────────┘  └─────────────────┘  │
│              WebSocket (real-time streaming)              │
└────────────────────────────┬─────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────┐
│                   FastAPI Backend                          │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              LangGraph Orchestrator                   │  │
│  │  (workflow state, parallel execution, conditional     │  │
│  │   routing, cycles, error recovery)                   │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                │
│                    A2A Protocol Layer                      │
│         (agent discovery, task delegation, status)         │
│                          │                                │
│  ┌────────┬──────────┬───┴───┬─────────┬──────────────┐  │
│  │ Router │Researcher│ Arch  │  Coder  │   Reviewer   │  │
│  │[Haiku] │[Gemini]  │[Opus] │[Sonnet] │  [DeepSeek]  │  │
│  └────────┘────┬─────┘───────┘─────────┘──────────────┘  │
│                │                                          │
│           ┌────▼──────┐    ┌──────────────────┐          │
│           │ Playwright │    │    Verifier      │          │
│           │  Browser   │    │  [Haiku+Docker]  │          │
│           └───────────┘    └──────────────────┘          │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Model Registry (benchmark-sourced YAML config)      │  │
│  │  + LLM Router (OpenRouter / Anthropic / OpenAI /     │  │
│  │    Ollama / any OpenAI-compatible API)               │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### 4.2 Component responsibilities

**LangGraph Orchestrator**
- Defines the workflow graph: nodes are agent roles, edges are conditional transitions
- Manages shared state that all agents read/write
- Supports parallel execution (Researcher and Architect can work simultaneously)
- Handles cycles (Reviewer sends back to Coder, Coder can ask Researcher for help)
- Error recovery: if an agent fails, retry with escalated model or skip gracefully

**A2A Protocol Layer**
- Each agent is an A2A-compliant service with a standard interface
- Agents discover each other ("what agents are available?")
- Agents delegate sub-tasks ("@Researcher, what retry library does this project use?")
- Agents report status (streamed to frontend via WebSocket)
- Inter-agent messages are visible in the chat stream UI

**Model Registry**
- YAML config mapping agent roles to model IDs with reasoning and benchmark source
- Updated manually when significant benchmark results drop (new model releases, SWE-bench updates)
- User overrides stored per-session, optionally persisted per-project
- Full product: auto-pull from leaderboard APIs with admin review gate

**LLM Router**
- Unified interface wrapping multiple providers
- All agent LLM calls go through: `call_llm(model_id, messages) → (response, tokens, cost)`
- Supports: OpenRouter, Anthropic API, OpenAI API, Ollama (local)
- Tracks tokens and cost per-agent for real-time display

---

## 5. Agent Specifications

### 5.1 Router Agent

**Purpose:** Classify incoming tasks and decide which agents to activate and in what order.

**Default model:** Haiku 4.5 (task classification is easy — use cheapest fast model)

**Input:** User's task description + optional repo context

**Output:** Task classification + agent activation plan

**Classifications:**
- `bug_fix` → Researcher → Coder → Reviewer → Verifier
- `new_feature` → Researcher + Architect (parallel) → Coder → Reviewer → Verifier
- `code_review` → Researcher → Reviewer → (if issues) Coder → Verifier
- `refactor` → Researcher → Architect → Coder → Verifier
- `explain` → Researcher only

### 5.2 Researcher Agent

**Purpose:** Gather context by searching the codebase and browsing the web. Has its own Playwright-controlled browser visible in the UI.

**Default model:** Gemini 2.5 Pro (strong at synthesis and multi-document QA)

**Capabilities:**
- Read/search files in the target repository
- Browse the web via Playwright (search engines, documentation, Stack Overflow, GitHub)
- Synthesize findings into structured context for other agents
- Respond to ad-hoc requests from other agents via A2A

**Browser behavior:**
- Browser panel slides into the UI when Researcher starts browsing
- Shows real web pages with agent's highlighted notes/annotations
- Tab bar shows browsing history
- Screenshots streamed to frontend in real-time
- Panel slides out when browsing is complete

### 5.3 Architect Agent

**Purpose:** Plan implementation approaches, break tasks into steps, make design decisions that affect multiple files.

**Default model:** Opus 4.6 / o1 (architecture requires genuine reasoning — worth the premium)

**Input:** Task description + Researcher's findings

**Output:** Implementation plan with ordered steps, file modifications needed, dependencies between changes

**When activated:** New features, refactors, any task touching 3+ files

### 5.4 Coder Agent

**Purpose:** Write the actual code. Implements plans from the Architect or fixes from the Researcher's analysis.

**Default model:** Sonnet 4.6 / GPT-5.5 Codex (best cost/performance for implementation — 79.6% SWE-bench Verified, 3-4x cheaper than Opus)

**Input:** Architect's plan OR Researcher's bug analysis + relevant file contents

**Output:** Code changes (diffs streamed to UI in real-time)

**Behavior:**
- Streams code as it's written (visible in chat stream)
- Can request help from Researcher via A2A
- Responds to user interrupts by adjusting approach
- If Reviewer rejects, receives specific feedback and rewrites

### 5.5 Reviewer Agent

**Purpose:** Review code for bugs, security issues, quality problems. MUST use a different model family than the Coder to catch blind spots.

**Default model:** DeepSeek R1 (different family from Coder's Claude/GPT — heterogeneous review)

**Input:** Coder's output + original task + Researcher's context

**Output:** Approval OR list of issues with specific line references and suggested fixes

**Key design decision:** The Reviewer is deliberately a different model family from the Coder. This carries forward the research finding from the original TestForge: heterogeneous models catch bugs that same-model review misses.

### 5.6 Verifier Agent

**Purpose:** Prove the code actually works by running it in a Docker sandbox. Generates tests if none exist.

**Default model:** Haiku 4.5 (for test generation) + deterministic Docker executor

**Capabilities:**
- Run existing test suites in Docker sandbox
- Generate new tests for the specific change (using mutation testing from original TestForge)
- Confirm no regressions
- Report: PASS with evidence, or FAIL with stdout/stderr → routed back to Coder

**Docker sandbox (carried from original TestForge):**
- Isolated container per verification run
- Pre-installs project dependencies
- 60-second timeout per test run
- Returns structured results: passed/failed, stdout, stderr, timed_out

---

## 6. User Interface Specification

### 6.1 Layout: Three columns

| Column | Content | Behavior |
|--------|---------|----------|
| Left (160px) | Agent sidebar | Always visible. Shows all 6 agents with status (idle/active/done), model name, elapsed time, cost. Click agent → full history + model config. |
| Center (flex) | Chat stream | Main interaction area. Agent messages appear as color-coded cards. Expandable on click. User input bar at bottom. Expands to fill space when browser panel is hidden. |
| Right (280px) | Browser panel | Slides in from right when Researcher is browsing. Shows real web pages with agent annotations. URL bar, tab history. Slides out when done. |

### 6.2 Chat stream messages

Each message has:
- Color-coded left border (unique per agent)
- Agent name + model + elapsed time
- Summary text (always visible)
- Expandable detail (click to show): full code diffs, browser screenshots, reasoning chains, search results
- A2A inter-agent messages shown inline (e.g., "→ @Researcher what retry library?")

### 6.3 User interrupt

- Always-visible input bar at the bottom of the chat stream
- User types and sends at any time — no need to wait for agents to finish
- Message appears in the chat stream with distinct styling (purple border, "YOU" label)
- Broadcast to all active agents via A2A
- Active agent pauses, acknowledges, and adapts
- If interrupt implies new work, Router can activate additional agents

### 6.4 Real-time updates

- WebSocket connection streams all agent activity
- Code is streamed character-by-character as Coder writes (typewriter effect)
- Agent status transitions animate in sidebar
- Browser panel shows live page loads
- Cost/token counters update in real-time

### 6.5 Model configuration

- Accessible from agent sidebar (click any agent → settings icon)
- Dropdown showing available models per provider
- Shows current benchmark data for the default choice
- Changes apply immediately to the next agent invocation
- Per-session by default, option to save as project default

---

## 7. Workflow Specifications

### 7.1 Bug fix workflow

```
User submits task
  → Router classifies as bug_fix (Haiku, ~0.2s)
  → Researcher activated (Gemini)
      • Searches codebase for relevant files
      • Opens browser if external context needed
      • Reports findings to shared state
  → Coder activated (Sonnet)
      • Reads Researcher's findings
      • Writes fix (streamed to UI)
      • Can ask Researcher for more context via A2A
  → Reviewer activated (DeepSeek)
      • Reviews fix with different model family
      • If issues → sends back to Coder with specific feedback (cycle)
      • If approved → passes to Verifier
  → Verifier activated (Haiku + Docker)
      • Runs existing tests
      • Generates regression test for the specific bug
      • Reports PASS or FAIL
      • If FAIL → sends back to Coder with test output
  → Complete: shows summary with all changes, test results, cost
```

### 7.2 New feature workflow

```
User submits task
  → Router classifies as new_feature (Haiku)
  → Researcher + Architect activated IN PARALLEL
      • Researcher: gathers context, browses docs for best practices
      • Architect: begins planning (receives Researcher's findings as they arrive)
  → Architect finalizes plan (Opus)
      • Breaks into implementation steps
      • Identifies file modifications needed
  → Coder implements step-by-step (Sonnet)
      • Each step: write code → Reviewer checks → Verifier tests
      • Can request Researcher help mid-implementation
  → Final verification
      • Full test suite run
      • Integration test for the complete feature
  → Complete: summary with plan, all changes, test results
```

### 7.3 Code review workflow

```
User submits code or points to PR/files
  → Router classifies as code_review (Haiku)
  → Researcher activated (Gemini)
      • Analyzes the code and surrounding context
      • Identifies the code's intent and dependencies
  → Reviewer activated (DeepSeek)
      • Reviews for: correctness, security, performance, edge cases
      • Produces issue list with severity and specific line references
  → If issues found and user approves fixes:
      → Coder activated (Sonnet) to implement fixes
      → Verifier confirms fixes don't break anything
  → Complete: review report with findings and optional fixes applied
```

### 7.4 Dynamic re-planning on interrupt

When a user interrupt changes the task:
1. Active agent pauses generation
2. Router re-evaluates: does this change the workflow?
   - If yes (e.g., "actually, make this a new feature not a fix") → re-route
   - If no (e.g., "use Redis instead of in-memory") → active agent adapts
3. Updated context is propagated to all agents via shared LangGraph state
4. Execution resumes with new constraints

---

## 8. Technical Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | React + TypeScript | Component model for complex UI, strong ecosystem |
| Real-time | WebSocket via FastAPI | Native async support, bidirectional streaming |
| Backend | FastAPI (Python) | Matches existing codebase, async-native, fast |
| Orchestration | LangGraph | Directed graph with cycles, parallel execution, state management |
| Agent communication | A2A Protocol (Google) | Standardized inter-agent messaging, future-proof for distributed deployment |
| Browser automation | Playwright | Reliable, supports screenshots and page content extraction |
| Code execution | Docker | Isolated sandbox for Verifier, carried from existing TestForge |
| LLM access | OpenRouter + direct provider APIs | Access to all models, single unified interface |
| Local models | Ollama | For users who want to run models locally |

---

## 9. Model Registry Specification

### 9.1 Config format

```yaml
# model_defaults.yaml
# Updated: 2026-05-28
# Sources: SWE-bench Verified, HumanEval, Chatbot Arena, MMLU-Pro

registry_version: "1.0"
last_updated: "2026-05-28"

agents:
  router:
    model: "anthropic/claude-haiku-4-5"
    reason: "Task classification is simple — cheapest fast model"
    benchmarks:
      humaneval: "92%"
      cost_per_1m_output: "$5"
    alternatives:
      - "google/gemini-flash-2.0"
      - "openai/gpt-4o-mini"

  researcher:
    model: "google/gemini-2.5-pro"
    reason: "Best at synthesis and multi-document information gathering"
    benchmarks:
      mmlu_pro: "87.2%"
      cost_per_1m_output: "$10"
    alternatives:
      - "anthropic/claude-sonnet-4-6"
      - "openai/gpt-5.5"

  architect:
    model: "anthropic/claude-opus-4-6"
    reason: "Architecture requires genuine reasoning — worth premium"
    benchmarks:
      swe_bench_verified: "87.6%"
      cost_per_1m_output: "$25"
    alternatives:
      - "openai/o1"
      - "google/gemini-2.5-pro"

  coder:
    model: "anthropic/claude-sonnet-4-6"
    reason: "Best cost/performance for implementation"
    benchmarks:
      swe_bench_verified: "79.6%"
      cost_per_1m_output: "$15"
    alternatives:
      - "openai/gpt-5.5-codex"
      - "deepseek/deepseek-coder-v3"

  reviewer:
    model: "deepseek/deepseek-r1"
    reason: "Different model family from Coder — heterogeneous review catches more bugs"
    benchmarks:
      reasoning: "Strong"
      cost_per_1m_output: "$8"
    constraint: "MUST be different model family than coder"
    alternatives:
      - "google/gemini-2.5-pro"
      - "anthropic/claude-opus-4-6"

  verifier:
    model: "anthropic/claude-haiku-4-5"
    reason: "Test generation is straightforward; Docker execution is deterministic"
    benchmarks:
      humaneval: "92%"
      cost_per_1m_output: "$5"
    alternatives:
      - "openai/gpt-4o-mini"
```

### 9.2 Update process

**MVP (manual):**
1. Monitor major benchmark releases (SWE-bench, Chatbot Arena, new model launches)
2. Update `model_defaults.yaml` with new model IDs, benchmarks, and reasoning
3. Ship as part of regular releases

**Full product (semi-automated):**
1. Scheduled job pulls latest rankings from benchmark APIs
2. Proposes config changes via internal review
3. Admin approves/rejects
4. Users get updated defaults on next session

### 9.3 User override behavior

- User can change any agent's model from the UI
- Override persists for the session by default
- Optional "Save as project default" stores in `.testforge/config.yaml` in the repo
- Overrides are shown in the UI with a "custom" badge

---

## 10. Data Flow

### 10.1 Shared workspace (LangGraph state)

All agents read from and write to a shared state object managed by LangGraph:

```python
class WorkflowState(TypedDict):
    task: str                    # Original user request
    task_type: str              # Router's classification
    repo_path: str             # Path to target repository
    context: list[str]         # Researcher's findings
    plan: list[dict]           # Architect's implementation steps
    code_changes: list[dict]   # Coder's file modifications
    review_feedback: list[dict] # Reviewer's issues
    test_results: dict         # Verifier's test output
    user_interrupts: list[str] # All user messages injected mid-task
    agent_messages: list[dict] # A2A inter-agent communication log
    cost_tracker: dict         # Per-agent token/cost accumulation
```

### 10.2 WebSocket event stream

Frontend receives a continuous stream of events:

```json
{"type": "agent_status", "agent": "researcher", "status": "active", "model": "gemini-2.5-pro"}
{"type": "agent_message", "agent": "researcher", "content": "Found auth.py at src/auth/...", "expandable": {...}}
{"type": "browser_update", "url": "https://docs.python-requests.org/...", "screenshot": "base64..."}
{"type": "code_stream", "agent": "coder", "chunk": "+ response = requests.post(\n"}
{"type": "agent_a2a", "from": "coder", "to": "researcher", "content": "What retry library?"}
{"type": "cost_update", "agent": "coder", "tokens": 1240, "cost": 0.018}
{"type": "agent_status", "agent": "coder", "status": "paused", "reason": "user_interrupt"}
```

---

## 11. MVP Scope

### 11.1 In scope

- 6 agents: Router, Researcher, Architect, Coder, Reviewer, Verifier
- 3 workflow types: bug fix, new feature, code review
- Researcher browser via Playwright with real-time UI streaming
- Docker sandbox for Verifier (carried from existing TestForge executor)
- Model config UI with benchmark-sourced defaults and user override
- User interrupt with dynamic agent response
- WebSocket real-time streaming of all agent activity
- Expandable chat messages with full detail view
- Three-column responsive layout (sidebar + chat + browser panel)
- Works on a single repo (user provides GitHub URL or local path)
- LangGraph orchestration + A2A inter-agent communication
- Cost and token tracking per-agent, per-session

### 11.2 Deferred to full product

- Auto-pull benchmark updates from leaderboard APIs
- Persistent project memory across sessions
- Multiple concurrent tasks
- Team collaboration (multiple users watching/interrupting)
- Self-hosted model support beyond Ollama
- CI/CD integration (GitHub Action for automated review)
- Agent plugins (user-defined custom agents)
- Conversation history / session replay
- Adaptive routing (auto-escalate model on failure)

---

## 12. Success Criteria

### Demo success

- User submits a task → agents visibly collaborate in real-time
- Researcher's browser activity is visible and comprehensible
- User interrupts mid-task → agents adapt dynamically
- Different models are visibly used for different agents
- Task completes with working code verified by Docker sandbox
- Total demo flow: under 3 minutes for a bug fix, under 5 minutes for a feature

### Product success

- Users report they can't go back to single-model tools after using TestForge
- Model specialization produces measurably better results than single-model baseline
- Cost savings of 40-60% vs. using the strongest model for everything
- User interrupts resolve correctly 90%+ of the time

---

## 13. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Agent coordination failures (loops, conflicts) | High | LangGraph provides deterministic state management. Max iteration limits per cycle. Supervisor timeout. |
| Context degradation across agent handoffs | Medium | Structured shared state (not raw text accumulation). Each agent reads only what it needs. |
| Playwright browser flakiness | Medium | Graceful fallback to web search API if browser fails. Screenshots cached. |
| A2A protocol complexity for MVP | Low | Start with simplified A2A (direct function calls between agents). Full protocol compliance can be incremental. |
| Model provider rate limits / downtime | Medium | LLM Router supports fallback to alternative models per agent. Retry with exponential backoff. |
| Demo reliability (must not crash during presentation) | High | Record a backup demo video. Test on the exact demo scenarios repeatedly. Docker sandbox has hard timeout. |

---

## 14. Relationship to Original TestForge

This redesign builds on the existing TestForge codebase:

| Original component | New role |
|-------------------|----------|
| `llm.py` (LLM router) | Evolves into the Model Registry + LLM Router |
| `executor.py` (Docker sandbox) | Becomes the Verifier agent's execution engine |
| `orchestrator.py` | Replaced by LangGraph orchestrator (much more capable) |
| `supervisor.py` (budget guardrail) | Integrated into LangGraph state as cost_tracker |
| `author.py` | Concept evolves into the Coder agent |
| `judge.py` | Concept evolves into the Reviewer agent (heterogeneous model insight preserved) |
| `adversary.py` (mutation generation) | Optional capability within Verifier for enhanced test quality |
| Research finding: heterogeneous models catch more bugs | Core architectural principle: Reviewer MUST be different model family than Coder |

---

## 15. Open Questions (Resolved)

| Question | Resolution |
|----------|-----------|
| What problem does this solve? | AI coding tools use one model for everything; TestForge uses specialized agents with optimal models per role |
| Who is the target user? | Individual developers using AI coding tools |
| How do users interact? | Web UI with real-time visibility, not CLI |
| What architecture? | Autonomous swarm with LangGraph + A2A |
| What's the coordination mechanism? | LangGraph manages workflow state; A2A handles inter-agent messaging |
| How are models selected? | Smart defaults from public benchmarks (YAML config); user can override any assignment |
| How do defaults stay current? | MVP: manual YAML updates. Full product: auto-pull from benchmark APIs |
| What's the MVP scope? | 6 agents, 3 workflows, browser panel, Docker verification, user interrupt |
