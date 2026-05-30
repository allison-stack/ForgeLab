"""
Unified LLM gateway — Ollama-first, OpenRouter fallback.

Every agent call goes through call_llm(). The base model is read from
OLLAMA_MODEL env var. When the user accepts an Evaluator upgrade, the
caller passes model= explicitly (OpenRouter model ID).
"""
import os
from openai import OpenAI


def get_client(use_openrouter: bool = False) -> OpenAI:
    if use_openrouter:
        return OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OpenAI(base_url=f"{base_url}/v1", api_key="ollama")


# module-level alias used by tests
_get_client = get_client


def call_llm(
    system: str,
    user: str,
    model: str | None = None,
    *,
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> tuple[str, int]:
    """
    Single LLM call. Uses Ollama by default; routes to OpenRouter when
    model= is an OpenRouter model ID (contains '/').
    Returns (output_text, total_tokens).
    """
    use_openrouter = model is not None and "/" in model
    client = _get_client(use_openrouter=use_openrouter)

    if model is None:
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    text = response.choices[0].message.content or ""
    tokens = response.usage.total_tokens if response.usage else 0
    return text, tokens
