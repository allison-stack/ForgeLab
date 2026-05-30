# LLM Gateway — `src/forgelab/llm.py`

## Purpose

Single entry point for all LLM calls. Every agent goes through `call_llm()`. No agent creates an OpenAI client directly.

## Routing Logic

```
model arg contains '/'  →  OpenRouter  (e.g., "anthropic/claude-sonnet-4-6")
model arg is None/local →  Ollama      (e.g., "qwen2.5-coder:7b")
```

The `/` in model ID is the discriminator. OpenRouter model IDs always have `provider/model-name` format.

## Functions

### `get_client(use_openrouter=False) → OpenAI`

Returns an OpenAI SDK client pointed at:
- **Ollama:** `{OLLAMA_BASE_URL}/v1` with `api_key="ollama"` (Ollama accepts any key)
- **OpenRouter:** `{OPENROUTER_BASE_URL}` with `api_key=OPENROUTER_API_KEY` from env

### `call_llm(system, user, model=None, *, temperature=0.2, max_tokens=2000) → (str, int)`

Makes a single chat completion call. Returns `(output_text, total_tokens)`.

- If `model` is None → reads `OLLAMA_MODEL` env var, defaults to `qwen2.5-coder:7b`
- If `model` contains `/` → routes to OpenRouter automatically

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server location |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Default local model |
| `OPENROUTER_API_KEY` | (required for upgrades) | OpenRouter auth |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |

## Usage in Agent Modules

Agents do NOT call `call_llm()` directly — they inherit from `BaseAgent` and call `self.call(user_message)`. BaseAgent handles system prompt injection and temperature from AGENTS.md.

The only place to call `call_llm()` directly is `BaseAgent.call()` in `agents/base.py`.
