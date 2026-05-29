# ForgeLab v2 — Single-Model Persona Architecture Design

**Date:** 2026-05-28  
**Status:** Approved  
**Replaces:** MVP_PITCH.md (v1 multi-model design)

---

## Context & Motivation

ForgeLab v1 routed each agent to a different expensive API model (Opus for Architect, Gemini for Researcher, DeepSeek for Reviewer, etc.). This created two problems:

1. **Cost barrier** — every task incurs API charges across 5–6 models.
2. **Lock-in** — the architecture was tied to specific providers; swapping models meant changing the core design.

v2 pivots to a single locally-hosted model (Ollama by default) that takes on expert personas via per-agent `SKILL.md`, `SOUL.md`, and `AGENTS.md` files. API costs become opt-in: a new Evaluator agent assesses task complexity and recommends the benchmark-optimal premium model only when the task warrants it. The user decides whether to accept.

---

## Architecture

```
Task Input
    │
    ▼
┌─────────────┐
│  Evaluator  │  Scores complexity. Looks up benchmark_registry.yaml.
└─────────────┘  If complexity ≥ task threshold → recommends specific model
    │             with benchmark citation. User accepts or declines.
    ▼
┌──────────────────────────────────────────────────────────┐
│              LangGraph WorkflowState                      │
│  (shared memory — all agents read/write the same state)  │
│  task · findings · plan · code_changes · review_feedback │
│  test_results · agent_messages · complexity · cost       │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────┐
│ Router  │  Classifies task type, activates pipeline
└─────────┘
    │
    ├──► Researcher  (Playwright + codebase search)
    ├──► Architect   (parallel with Researcher for new_feature tasks)
    ├──► Coder  ──►  Reviewer  (catch-and-revise loop)
    └──► Verifier    (Docker sandbox via executor.py)

All 7 agents = same Ollama base model, shaped by different AGENTS.md persona
```

### Why LangGraph state over a separate explicit store

LangGraph's `WorkflowState` is shared memory. Every node reads and writes the same typed dict. Using it natively provides three things that a separate JSON/SQLite store would require hand-rolling:

- **Concurrency safety** — LangGraph serializes concurrent state writes during fan-out (e.g. Researcher + Architect running in parallel), eliminating race conditions.
- **Checkpointing + resume** — built-in checkpointer lets a crashed or interrupted task resume from the last completed node.
- **Interrupt as a first-class primitive** — `interrupt()` and `Command` are native LangGraph concepts; user mid-task injection works without custom plumbing.

Agent code sees a clean `SharedMemory` Pydantic model (e.g. `memory.findings`, `memory.plan`) — not raw LangGraph internals. The orchestration detail is invisible to agents.

---

## Per-Agent Persona Files

Each agent lives in `agents/<role>/` and has three files:

### `SKILL.md` — What this agent does
- Capabilities and tools it can invoke
- Inputs (fields it reads from `WorkflowState`)
- Outputs (fields it writes to `WorkflowState`)
- Step-by-step workflow and thinking procedure
- Domain knowledge relevant to the role

### `SOUL.md` — Who this agent is
- Character and personality
- Communication style
- Core values and non-negotiables
- Cognitive approach to ambiguity, risk, and uncertainty
- Signature behaviors that differentiate this agent's output from others

### `AGENTS.md` — Runtime system prompt + parameters (model-agnostic)
Read by the orchestrator to shape each LLM call. Works with any backend (Ollama, OpenRouter, direct API).

```markdown
# [Role] Agent

## System Prompt
[Compiled from SOUL.md + SKILL.md — becomes the system message]

## Parameters
temperature: [tuned per role]
top_p: [tuned per role]
num_ctx: 8192

## Tools
[tools this agent can invoke]

## Output Format
[structured format the orchestrator expects]
```

---

## Agent Roster

| Agent | Soul (character) | Temperature | Key skill |
|---|---|---|---|
| **Evaluator** | Cautious gatekeeper — calibrated, not pessimistic | 0.0 | Complexity scoring + benchmark lookup |
| **Router** | Fast, decisive, no second-guessing | 0.0 | Task classification, pipeline selection |
| **Researcher** | Insatiably curious, never assumes, always cites | 0.3 | Codebase search + Playwright web browsing |
| **Architect** | Deliberate, thinks in systems, resists shortcuts | 0.4 | Implementation planning, interface design |
| **Coder** | Focused craftsperson — code first, explanation second | 0.1 | Code generation, style-matching, diff production |
| **Reviewer** | Adversarial by design — assumes bugs exist | 0.5 | Edge-case review, security, error handling |
| **Verifier** | Trusts only execution — binary: pass or fail | 0.1 | Test generation, Docker sandbox via executor.py |

The Reviewer's higher temperature and adversarial SOUL are the v2 equivalent of v1's "heterogeneous review via different model family" — same model, fundamentally different cognitive framework baked into the SOUL.

---

## Evaluator + Benchmark Registry

### `benchmark_registry.yaml`
Maps task type → benchmark-optimal premium model. The Evaluator reads this at runtime — no hardcoded model in env vars.

```yaml
task_types:
  bug_fix:
    recommended: "anthropic/claude-sonnet-4-6"
    reason: "SWE-bench Verified 79.6% — strongest at targeted code fixes"
    benchmark: {swe_bench_verified: "79.6%", cost_per_1m: "$15"}
    threshold: complex

  new_feature:
    recommended: "anthropic/claude-opus-4-8"
    reason: "SWE-bench Verified 87.6% — genuine reasoning for design decisions"
    benchmark: {swe_bench_verified: "87.6%", cost_per_1m: "$75"}
    threshold: complex

  architecture:
    recommended: "anthropic/claude-opus-4-8"
    reason: "Highest reasoning benchmark — architecture decisions compound"
    benchmark: {swe_bench_verified: "87.6%", cost_per_1m: "$75"}
    threshold: moderate

  research_synthesis:
    recommended: "google/gemini-2.5-pro"
    reason: "MMLU-Pro 87.2% — strongest multi-document synthesis"
    benchmark: {mmlu_pro: "87.2%", cost_per_1m: "$10"}
    threshold: complex

  code_review:
    recommended: "deepseek/deepseek-r1"
    reason: "Strong chain-of-thought reasoning catches subtle logic errors"
    benchmark: {reasoning: "strong", cost_per_1m: "$8"}
    threshold: complex

  explain:
    recommended: "anthropic/claude-sonnet-4-6"
    reason: "Chatbot Arena top-ranked for explanation quality"
    benchmark: {chatbot_arena: "top-5", cost_per_1m: "$15"}
    threshold: critical
```

If `complexity < threshold`, Evaluator writes `upgrade_recommendation: null` — no prompt shown. When it does recommend, the UI shows model name, benchmark source, and cost per token. The user always decides.

### `.env.example`
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
# Only needed if user accepts an upgrade recommendation:
OPENROUTER_API_KEY=your_key_here
```

---

## Shared Memory Schema (`WorkflowState`)

```
task                    — raw user input
task_type               — router classification
complexity              — evaluator output (simple/moderate/complex/critical)
upgrade_recommendation  — {task_type, recommended_model, benchmark_reason, score} or null
model_in_use            — active model identifier (set after user decision)
findings                — researcher output
plan                    — architect output
code_changes            — coder output (diffs + explanations)
review_feedback         — reviewer output (issues found)
test_results            — verifier output
agent_messages          — inter-agent messages (A2A-style)
session_cost            — per-agent token/cost accumulation
```

---

## Files to Create / Modify

```
forgelab/
├── agents/
│   ├── _shared/
│   │   └── MEMORY_SCHEMA.md
│   ├── evaluator/
│   │   ├── SKILL.md, SOUL.md, AGENTS.md
│   ├── router/
│   │   ├── SKILL.md, SOUL.md, AGENTS.md
│   ├── researcher/
│   │   ├── SKILL.md, SOUL.md, AGENTS.md
│   ├── architect/
│   │   ├── SKILL.md, SOUL.md, AGENTS.md
│   ├── coder/
│   │   ├── SKILL.md, SOUL.md, AGENTS.md
│   ├── reviewer/
│   │   ├── SKILL.md, SOUL.md, AGENTS.md
│   └── verifier/
│       ├── SKILL.md, SOUL.md, AGENTS.md
├── docs/
│   ├── MVP_PITCH.md              (kept — historical reference)
│   └── MVP_PITCH_V2.md           (new — single-model persona pitch)
├── agent_personas.yaml           (replaces model_defaults.yaml)
├── benchmark_registry.yaml       (new — Evaluator's upgrade lookup table)
└── .env.example                  (updated: OLLAMA vars, no PREMIUM_MODEL)
```

---

## Verification Criteria

1. Each `agents/<role>/` folder contains all three files with substantively different SOUL characters
2. Running the same base Ollama model with Reviewer's `AGENTS.md` vs. Coder's `AGENTS.md` produces noticeably different response styles — confirming SOUL differentiation works on a single model
3. `benchmark_registry.yaml` is valid YAML; Evaluator logic can look up `task_types.bug_fix.recommended` and return a model name + benchmark citation
4. `.env.example` contains no `PREMIUM_MODEL` var — only `OPENROUTER_API_KEY` as the optional unlock
5. `docs/MVP_PITCH_V2.md` accurately describes the new architecture and makes no reference to per-agent API model assignments
