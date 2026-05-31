# ForgeLab

**A local-first multi-agent software engineering team**

<!-- TODO: replace with a screenshot or demo GIF -->
<!-- Reference: docs/demo.html has an interactive prototype -->

---

## The Problem

Every AI coding tool works the same way. You describe a task. It responds. You review it. You prompt again. Rinse, repeat. The AI is basically a really fast assistant — it waits for you at every step, doing what you ask, one request at a time.

The problem is that real software development isn't one step. It's digging through the codebase to understand the context, planning an approach, writing the code, catching your own mistakes, and actually running tests to prove it works. That's a team doing different jobs with different mindsets — not one person doing everything in a single pass.

When you ask one AI to do all of that in one shot, stuff gets missed. Tests fail. Bugs slip through. And if you're using a premium model, you're burning expensive API credits to fix a typo.

---

## What ForgeLab Does

ForgeLab replaces the prompt-response loop with a team.

Seven specialized agents collaborate on every task — each one shaped from the same underlying model through different personalities, instructions, and parameters. Same base model. Seven different minds.

| Agent | What it does |
|-------|-------------|
| **Evaluator** | Scores task complexity. Recommends a premium model upgrade only when benchmarks show it's worth it — and always asks you first. |
| **Router** | Figures out what kind of task this is (bug fix, new feature, code review, etc.) and assembles the right pipeline. |
| **Researcher** | Searches your codebase for relevant context before anyone writes a line of code. |
| **Architect** | Plans the implementation for new features and architecture tasks. Skipped for simpler work. |
| **Coder** | Writes minimal diffs that match your existing code style. Doesn't refactor things you didn't ask to change. |
| **Reviewer** | Reviews the code with an "assume bugs exist" mindset. Runs at a higher temperature on purpose — adversarial perspective needs variability. |
| **Verifier** | Runs actual tests in a Docker sandbox. The LLM says what it thinks. Docker says what's true. |

Not every agent runs every time. The Router figures out the task type and the pipeline assembles itself: a bug fix goes straight to the Coder, a new feature gets the Architect involved first, a code explanation ends right after research. The Reviewer → Coder loop repeats until the code is approved — only then does the Verifier run real tests.

---

## Why Local-First

ForgeLab defaults to [Ollama](https://ollama.com) — free, private, runs entirely on your machine. No API keys. No surprise bills. For most tasks, a local model gets the job done just as well as the expensive ones.

When a task is genuinely complex — something where a premium model actually performs better on benchmarks — the Evaluator flags it and shows you the numbers. You decide whether to accept the upgrade. One task, one decision. Nothing runs on a premium model without your go-ahead.

It's model-agnostic by design. Swap the local model, connect your own API key, or stay on Ollama forever. It doesn't care.

---

## See It In Action

1. Install ForgeLab and start the server (`forgelab start`) from your project root
2. Open `http://localhost:5173` in your browser
3. Type a task — for example: *"Fix the login timeout bug"*
4. Watch the agents work in real time: research, plan, code, review, test
5. Interrupt at any point to add context or change direction
6. Get a diff + test results you can actually trust

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **[Ollama](https://ollama.com)** — install and pull a model:
  ```bash
  ollama pull qwen2.5-coder:7b
  ```
- **Node.js 18+** — for the frontend
- **Docker** *(optional)* — used by the Verifier to run tests in an isolated sandbox; falls back to subprocess if unavailable

### Install

```bash
git clone <repo-url>
cd forgelab
pip install -e .
```

### Run

```bash
forgelab start
```

Open `http://localhost:5173` — that's it.

### Optional: Enable premium model upgrades

```bash
export OPENROUTER_API_KEY=your_key
forgelab start
```

The Evaluator will surface upgrade recommendations when a premium model meaningfully outperforms the local one for your task type.

---

## Architecture

ForgeLab uses [LangGraph](https://github.com/langchain-ai/langgraph) to orchestrate a directed graph of agents. All seven agents share a single `WorkflowState` — no direct agent-to-agent communication, everything flows through state. The backend is FastAPI with WebSocket streaming so you see agent activity in real time. The frontend is React 19 + TypeScript.

ForgeLab never modifies your codebase directly. It reads it and produces diffs. You apply them.

For deeper documentation, see the [wiki](wiki/):

- [`wiki/architecture.md`](wiki/architecture.md) — design philosophy and data flow
- [`wiki/agents.md`](wiki/agents.md) — each agent's role, inputs, and parameters
- [`wiki/graph.md`](wiki/graph.md) — LangGraph routing logic

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, LangGraph |
| Frontend | React 19, TypeScript, Vite |
| Local LLM | Ollama (default: `qwen2.5-coder:7b`) |
| Premium LLMs | OpenRouter (Claude, Gemini, DeepSeek) |
| Test Execution | Docker sandbox, subprocess fallback |
| Agent Orchestration | LangGraph StateGraph |
