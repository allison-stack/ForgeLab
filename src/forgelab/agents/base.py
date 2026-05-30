"""
BaseAgent — loads AGENTS.md and exposes a typed call() interface.
All agent modules define a run(state: WorkflowState) function and
optionally subclass BaseAgent for shared LLM call logic.
"""
import re
from pathlib import Path

from forgelab.llm import call_llm
from forgelab.state import WorkflowState

# Persona data is bundled inside the package at src/forgelab/personas/.
# Path(__file__).parent = src/forgelab/agents/ → go up one level to src/forgelab/
# This always resolves to the installed package location, never the target repo.
_PERSONAS_DIR = Path(__file__).parent.parent / "personas"


def parse_agents_md(content: str) -> dict:
    """
    Extract system_prompt and numeric parameters from an AGENTS.md file.
    Returns {"system_prompt": str, "temperature": float, "top_p": float, "num_ctx": int}.
    """
    # Extract System Prompt section (between ## System Prompt and next ##)
    prompt_match = re.search(
        r"## System Prompt\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
    )
    system_prompt = prompt_match.group(1).strip() if prompt_match else ""

    # Strip inner markdown code fences from system prompt
    system_prompt = re.sub(r"```[^\n]*\n.*?```", "", system_prompt, flags=re.DOTALL).strip()

    # Extract Parameters section
    params_match = re.search(r"## Parameters\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    params: dict = {}
    if params_match:
        for line in params_match.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                k, v = k.strip(), v.strip()
                try:
                    params[k] = float(v) if "." in v else int(v)
                except ValueError:
                    params[k] = v

    return {
        "system_prompt": system_prompt,
        "temperature": float(params.get("temperature", 0.2)),
        "top_p": float(params.get("top_p", 0.95)),
        "num_ctx": int(params.get("num_ctx", 8192)),
    }


class BaseAgent:
    """Loads AGENTS.md for a given role and exposes call()."""

    role: str  # set by subclasses

    def __init__(self, model_override: str | None = None) -> None:
        agents_md_path = _PERSONAS_DIR / self.role / "AGENTS.md"
        content = agents_md_path.read_text(encoding="utf-8")
        parsed = parse_agents_md(content)
        self._system_prompt = parsed["system_prompt"]
        self._temperature = parsed["temperature"]
        self._model_override = model_override

    def call(self, user_message: str, *, model: str | None = None) -> tuple[str, int]:
        effective_model = model or self._model_override
        return call_llm(
            system=self._system_prompt,
            user=user_message,
            model=effective_model,
            temperature=self._temperature,
        )

    @staticmethod
    def _add_cost(state: WorkflowState, agent_name: str, tokens: int) -> dict:
        """Return a partial state update with updated session_cost."""
        cost_per_token = 0.0  # local model — zero cost
        existing = state.get("session_cost", {})
        entry = existing.get(agent_name, {"tokens": 0, "cost_usd": 0.0})
        return {
            "session_cost": {
                **existing,
                agent_name: {
                    "tokens": entry["tokens"] + tokens,
                    "cost_usd": entry["cost_usd"] + (tokens * cost_per_token),
                },
            }
        }
