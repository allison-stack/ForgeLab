# ForgeLab — MVP

## The Problem

Every AI coding tool today — Claude Code, Cursor, Copilot, Devin — uses a single model for everything. One model plans your architecture, writes your code, reviews it, and tests it. This is like hiring one person to be your architect, engineer, QA lead, and researcher simultaneously.

The result:
- **96% of developers don't fully trust AI-generated code** (Stack Overflow 2026)
- **45% say debugging AI code takes longer than debugging their own** (SmartBear)
- **69% of frequent AI users report regular deployment problems** (CodeRabbit)
- Developers pay premium model prices for simple tasks that a cheaper model handles equally well

The fundamental issue: **one model cannot be optimal at every type of work.** Research proves this — Opus-tier models are 3-4x more expensive than Sonnet-tier but only 1-2% better at implementation tasks, while significantly stronger at architectural reasoning. Teams using tiered model routing save 60-70% with no quality loss.

---

## The Solution: ForgeLab

ForgeLab is a **multi-agent software engineering team** where each agent is powered by the optimal AI model for its specific role — based on real, public benchmark data.

Instead of one AI doing everything, you get a team:

| Agent | Role | Why a specialized model matters |
|-------|------|-------------------------------|
| **Router** | Classifies your task, activates the right agents | Simple classification — use the cheapest, fastest model |
| **Researcher** | Searches your codebase + browses the web live | Needs strong synthesis across many sources |
| **Architect** | Plans implementation, makes design decisions | Needs genuine reasoning — worth the premium |
| **Coder** | Writes the actual code | Best cost/performance for pure implementation |
| **Reviewer** | Reviews code with a *different* model family | Heterogeneous review catches bugs same-model misses |
| **Verifier** | Runs code in Docker sandbox, proves it works | Deterministic execution — no hallucination possible |

**The key insight:** The Reviewer deliberately uses a different model family than the Coder. Our research (from TestForge v1) demonstrated that heterogeneous models catch blind spots that same-model review misses — the same way a second opinion from a different doctor catches what the first one missed.

---

## What Makes It "Can't Go Back"

Once you've watched a team of specialized agents:
1. Research your codebase and the web (you can see the browser live)
2. Plan the architecture with a reasoning-optimized model
3. Implement with a coding-optimized model
4. Get reviewed by a completely different model that catches different bugs
5. Get verified in a real Docker sandbox that proves correctness

...going back to a single model guessing at everything feels like going from a team back to a solo freelancer.

**The three hooks that create stickiness:**
- **Transparency** — you see everything happening in real-time, not a black box
- **Control** — interrupt and redirect agents at any time, they adapt dynamically
- **Cost efficiency** — pay for Opus reasoning only when you need it; simple tasks use Haiku at 5x savings

---

## Competitive Position

```
                    ┌─────────────────────────────────┐
                    │     HIGH MODEL FLEXIBILITY       │
                    │                                  │
         Kilo Code │                    ★ ForgeLab    │
   (pick per mode) │          (specialized agents +   │
                    │           benchmark defaults +   │
                    │           live transparency)     │
                    │                                  │
  LOW TRANSPARENCY ─┼──────────────────────────────────┼─ HIGH TRANSPARENCY
                    │                                  │
             Devin │              OpenHands            │
      (black box,  │        (multi-agent, per-agent   │
       one model)  │         models, no live UI)      │
                    │                                  │
                    │     LOW MODEL FLEXIBILITY        │
                    └─────────────────────────────────┘

  Claude Code, Cursor, Copilot: bottom-left (single model, limited visibility)
```

**No existing tool combines:**
- Intelligent per-role model selection with benchmark-driven defaults
- A transparent, real-time UI showing agent collaboration
- User interrupt capability with dynamic agent adaptation
- Heterogeneous model review (deliberate cross-family verification)
- Deterministic Docker verification (not just LLM "I think it works")

---

## Market Opportunity

- AI coding tools market: growing rapidly, every developer will use one within 2 years
- **The trust gap is the #1 adoption blocker** — 96% don't fully trust AI code
- ForgeLab directly addresses trust through: transparency, verification, and heterogeneous review
- Cost optimization (60-70% savings from model routing) is a strong secondary value prop
- No tool currently owns the "multi-agent + model specialization + transparency" space

---

## Demo Flow (5 minutes)

### Scenario: Fix a bug reported in a GitHub issue

**0:00 — User pastes a task**
> "Fix the login timeout issue — users report OAuth flow times out on slow connections"

**0:15 — Router activates (Haiku, 0.2s)**
Classifies as `bug_fix`, activates Researcher → Coder → Reviewer → Verifier. Visible in UI.

**0:20 — Researcher starts (Gemini 2.5 Pro)**
- Searches codebase → finds `auth.py` with hardcoded `timeout=5`
- Browser panel slides in → browses Python requests docs for timeout best practices
- User can watch the browser in real-time
- Reports findings: "Timeout is hardcoded at 5s, OAuth flows need 30s+"

**1:00 — Coder starts (Sonnet 4.6)**
- Reads Researcher's findings
- Streams code live in the chat: adds `timeout=(10, 30)` tuple
- User watches code being written character by character

**1:30 — User interrupts**
> "Also add retry with exponential backoff — we see flaky networks in prod"

- Coder pauses, acknowledges
- Asks Researcher via A2A: "what retry library does this project use?"
- Researcher checks → responds: "uses `tenacity`"
- Coder adapts, adds retry decorator

**2:30 — Reviewer (DeepSeek R1)**
- Reviews with a different model family than what wrote the code
- Catches: "retry should have max_attempts limit to avoid infinite loops"
- Sends back to Coder → Coder adds `stop_after_attempt(3)`

**3:00 — Verifier (Haiku + Docker)**
- Runs existing tests in sandbox → all pass
- Generates new test for the timeout scenario
- Reports: ✅ PASS — 14 tests passing, 0 regressions

**3:30 — Complete**
- Summary card: files changed, tests added, cost ($0.08), time (3.5 min)
- Different models visibly used for each role throughout

**Key demo moments:**
- The browser panel sliding in (visual wow)
- User interrupt mid-task with dynamic agent adaptation
- Reviewer catching something the Coder's model missed (heterogeneous review payoff)
- Docker proving it actually works (not just "I think it's correct")

---

## Technical Architecture (Summary)

```
React Frontend ←WebSocket→ FastAPI Backend
                               │
                        LangGraph Orchestrator
                        (state, parallel execution, cycles)
                               │
                         A2A Protocol Layer
                         (inter-agent messaging)
                               │
              ┌────┬──────┬────┼────┬─────────┬────────┐
           Router  Researcher  Architect  Coder  Reviewer  Verifier
           [Haiku] [Gemini]   [Opus]    [Sonnet] [DeepSeek] [Haiku+Docker]
                      │                                        │
                 Playwright                              Docker Sandbox
                  Browser
```

- **LangGraph** manages workflow state, parallel agent execution, and conditional routing
- **A2A Protocol** (Google) standardizes inter-agent communication
- **Model Registry** (YAML) maps agent roles to benchmark-optimal models; user can override
- **Playwright** gives the Researcher a real browser visible in the UI
- **Docker** gives the Verifier deterministic proof of correctness

---

## MVP Deliverables

| Component | What's included |
|-----------|----------------|
| **6 agents** | Router, Researcher, Architect, Coder, Reviewer, Verifier — all functional |
| **3 workflows** | Bug fix, new feature, code review — each uses different agent paths |
| **Web UI** | Three-column layout: agent sidebar, chat stream, browser panel |
| **Real-time streaming** | WebSocket streaming of all agent activity |
| **Browser panel** | Playwright-driven, slides in/out as Researcher browses |
| **User interrupt** | Type mid-task, agents pause and adapt dynamically |
| **Model config** | Benchmark-sourced defaults + per-agent user override from UI |
| **Docker verification** | Isolated sandbox proving code correctness |
| **Cost tracking** | Per-agent token/cost displayed in real-time |

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + TypeScript | Component model for complex real-time UI |
| Backend | FastAPI (Python) | Async-native, WebSocket support, fast |
| Orchestration | LangGraph | Directed graphs, parallel execution, cycles |
| Agent communication | A2A Protocol | Standardized, future-proof |
| Browser | Playwright | Reliable automation, screenshots |
| Sandbox | Docker | Deterministic code execution |
| LLM access | OpenRouter + direct APIs | Any model from any provider |
| Local models | Ollama | Privacy-focused users |

---

## Why Now

1. **Model diversity has exploded** — Claude, GPT, Gemini, DeepSeek, Qwen, Llama — each with different strengths. Using one for everything wastes this diversity.
2. **Benchmarks are mature enough** — SWE-bench Verified, HumanEval, Chatbot Arena give reliable signal on which model excels at what.
3. **LangGraph + A2A exist** — the orchestration infrastructure for multi-agent systems is now production-ready.
4. **Developer trust is the bottleneck** — speed of AI code generation has outpaced trust. The market needs verification, not more generation.
5. **MCP/A2A ecosystem growing** — standardized protocols mean agents can interoperate; building now puts us in the ecosystem early.

---

## Key Metrics to Track

| Metric | Target | How measured |
|--------|--------|-------------|
| Task completion rate | >85% for bug fixes, >70% for features | Tasks that reach "Verifier: PASS" without human takeover |
| Cost savings vs. single-model | 40-60% reduction | Compare ForgeLab total cost vs. running same task on Opus only |
| Heterogeneous review catch rate | >15% additional issues found | Issues Reviewer catches that Coder's model didn't prevent |
| User interrupt success | >90% correct adaptation | Interrupts that result in correct behavioral change |
| Time to completion | <3 min bug fix, <5 min feature | Wall clock from task submission to verified completion |

---

## What We're NOT Building (Anti-scope)

- Not a general-purpose AI assistant (it's for software engineering tasks only)
- Not a replacement for CI/CD (it's a development-time tool)
- Not an IDE plugin (it's a standalone web app — IDE integration is deferred)
- Not a hosted service for MVP (runs locally, user brings own API keys)
- Not trying to beat SWE-bench scores (we optimize for trust + transparency + cost, not raw autonomy)

---

## From Here: Implementation Path

1. **Backend foundation** — FastAPI server, LangGraph workflow graph, A2A agent interfaces
2. **Core agents** — Router + Researcher + Coder (minimum viable workflow)
3. **Docker verification** — Carry executor from TestForge, wire into Verifier agent
4. **Frontend** — React app with WebSocket streaming, three-column layout
5. **Browser panel** — Playwright integration for Researcher, screenshot streaming
6. **Remaining agents** — Architect + Reviewer (complete the team)
7. **User interrupt** — Injection into LangGraph state, agent adaptation logic
8. **Polish** — Model config UI, cost tracking, animations, demo scenarios
