"""Router — task classifier and pipeline selector."""
import json
import re

from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState

_VALID_TYPES = {"bug_fix", "new_feature", "architecture", "code_review", "refactor", "explain"}


class _RouterAgent(BaseAgent):
    role = "router"


_agent = _RouterAgent()


def run(state: WorkflowState) -> dict:
    user_msg = f"Task: {state['task']}\nComplexity: {state.get('complexity', 'unknown')}"
    raw, tokens = _agent.call(user_msg)
    raw = re.sub(r"```[^\n]*\n?", "", raw).strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            task_type = parsed.get("task_type", "bug_fix")
        elif isinstance(parsed, list) and parsed:
            task_type = parsed[0] if isinstance(parsed[0], str) else "bug_fix"
        else:
            task_type = "bug_fix"
        if task_type not in _VALID_TYPES:
            task_type = "bug_fix"
    except (json.JSONDecodeError, IndexError):
        task_type = "bug_fix"

    update: dict = {"task_type": task_type}
    update.update(BaseAgent._add_cost(state, "router", tokens))
    return update
