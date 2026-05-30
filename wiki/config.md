# Config Files

## benchmark_registry.yaml

Defines which premium model to recommend per task type and complexity threshold.

```yaml
task_types:
  bug_fix:
    recommended: "anthropic/claude-sonnet-4-6"
    reason: "SWE-bench Verified 79.6%"
    benchmark: {swe_bench_verified: "79.6%", cost_per_1m: "$15"}
    threshold: complex   # recommend when complexity >= complex

  new_feature:
    recommended: "anthropic/claude-opus-4-8"
    reason: "SWE-bench Verified 87.6%"
    benchmark: {swe_bench_verified: "87.6%", cost_per_1m: "$75"}
    threshold: complex

  architecture:
    recommended: "anthropic/claude-opus-4-8"
    threshold: moderate  # lower threshold — architecture decisions compound

  research_synthesis:
    recommended: "google/gemini-2.5-pro"
    benchmark: {mmlu_pro: "87.2%", cost_per_1m: "$10"}
    threshold: complex

  code_review:
    recommended: "deepseek/deepseek-r1"
    benchmark: {reasoning: "strong", cost_per_1m: "$8"}
    threshold: complex

  explain:
    recommended: "anthropic/claude-sonnet-4-6"
    benchmark: {chatbot_arena: "top-5", cost_per_1m: "$15"}
    threshold: critical  # highest threshold — explain rarely needs premium
```

**Read by:** Evaluator agent at runtime (embedded in AGENTS.md system prompt — registry values are inlined, not dynamically loaded).

## agent_personas.yaml

Defines the base model and per-agent configuration.

```yaml
base_model: "qwen2.5-coder:7b"      # all agents share this via Ollama
upgrade_threshold: complex            # global threshold (per-agent thresholds in benchmark_registry)

agents:
  evaluator:
    agents_md: "src/forgelab/personas/evaluator/AGENTS.md"
    temperature: 0.0
    description: "Complexity gatekeeper + benchmark-driven upgrade recommender"
  # ... same pattern for all 7 agents
```

**Note:** `agents_md` paths are relative. At runtime, `BaseAgent` resolves persona files via `Path(__file__).parent.parent / "personas"` (package-internal), not these paths. This file is informational config for the package CLI and deployment scripts.

## .env.example

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Only needed when user accepts an Evaluator upgrade recommendation
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```
