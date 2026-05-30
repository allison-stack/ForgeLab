"""Evaluator — complexity scorer and benchmark-driven upgrade recommender."""
import json
import re

from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _EvaluatorAgent(BaseAgent):
    role = "evaluator"


_agent = _EvaluatorAgent()


def run(state: WorkflowState) -> dict:
    user_msg = f"Task: {state['task']}"
    raw, tokens = _agent.call(user_msg)

    # Strip markdown fences if model wraps output
    raw = re.sub(r"```[^\n]*\n?", "", raw).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"complexity": "moderate", "upgrade_recommendation": None}

    update = {
        "complexity": parsed.get("complexity", "moderate"),
        "upgrade_recommendation": parsed.get("upgrade_recommendation"),
    }
    update.update(BaseAgent._add_cost(state, "evaluator", tokens))
    return update
