# ForgeLab v2 — MVP Pitch

## The Problem

AI coding tools today have two failure modes:

1. **The Trust Gap** — You ask an AI to fix a bug. It says "done." Tests fail. You spent 10 minutes reviewing a broken suggestion. LLMs don't know when they're wrong.

2. **The Cost Trap** — Using the best model for every task (Opus for "rename this variable") burns money on tasks that don't need it.

ForgeLab solves both.

---

## The Solution: One Local Model, Seven Expert Minds

ForgeLab runs **one Ollama model** on your machine. No API keys needed by default. Zero cost for 99% of tasks.

But the same base weights produce 7 completely different agents — because each agent gets a unique `SOUL.md` (personality), `SKILL.md` (job description), and `AGENTS.md` (system prompt + temperature). The Reviewer isn't a different model — it's the same model with a fundamentally different character: adversarial, higher temperature, built to disagree with the Coder.

```
User task → Evaluator → Router → Researcher → [Architect] → Coder → Reviewer → Verifier
```

---

## Why One Model Works

The same model produces different behavior when its cognitive style is changed:

- **Evaluator** (temp 0.0): Deterministic complexity scorer. Outputs only JSON. Refuses to hedge.
- **Coder** (temp 0.1): Near-deterministic. Focused. Never refactors beyond the task.
- **Reviewer** (temp 0.5): Same model, intentionally higher temperature. Shaped to find what the focused Coder missed. Assumes bugs exist.

The higher Reviewer temperature isn't a mistake — it's the mechanism. Adversarial perspective requires variability.

---

## The Evaluator: Benchmark-Driven Upgrades

The Evaluator scores task complexity and checks `benchmark_registry.yaml`. If a task is genuinely complex and a premium model outperforms on benchmarks for that task type, it recommends an upgrade — with the exact benchmark score and cost per 1M tokens.

**The user always decides.** Accept → run on the premium model (via OpenRouter). Decline → stay on local Ollama. No surprise bills.

| Task Type | Upgrade Model | Benchmark | Threshold |
|-----------|--------------|-----------|-----------|
| bug_fix | claude-sonnet-4-6 | SWE-bench 79.6% | complex |
| new_feature | claude-opus-4-8 | SWE-bench 87.6% | complex |
| architecture | claude-opus-4-8 | SWE-bench 87.6% | moderate |
| research_synthesis | gemini-2.5-pro | MMLU-Pro 87.2% | complex |
| code_review | deepseek-r1 | strong reasoning | complex |

---

## The Verifier: Deterministic Ground Truth

Every code change goes through the Verifier. It generates tests and runs them in a Docker sandbox. The LLM says what it thinks — Docker says what's true. ForgeLab only reports PASS when `pytest` exit code is 0.

This is the key reason ForgeLab closes the trust gap. You see actual test output, not an LLM's self-assessment.

---

## Cost

- **Default:** $0. Local Ollama, no API calls.
- **On upgrade acceptance:** Only the specific task uses the premium model, at the published rate.
- **Typical session:** 0-3 upgrade prompts. User chooses each one.

---

## Architecture

```
pip install forgelab
forgelab start        # run from any project root
```

ForgeLab never modifies your codebase directly. It reads it (grep, file access) and produces diffs. You apply them.

React frontend at localhost:5173 — three-column layout, live agent pipeline visualization, streaming output, interrupt support.
