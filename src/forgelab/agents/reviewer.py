"""Reviewer — adversarial code review."""
from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _ReviewerAgent(BaseAgent):
    role = "reviewer"


_agent = _ReviewerAgent()


def run(state: WorkflowState) -> dict:
    user_msg = (
        f"Task: {state['task']}\n\n"
        f"Code changes to review:\n{state.get('code_changes', '(none)')}\n\n"
        f"Researcher context:\n{state.get('findings', '(none)')}"
    )
    raw, tokens = _agent.call(user_msg)
    update: dict = {"review_feedback": raw}
    update.update(BaseAgent._add_cost(state, "reviewer", tokens))
    return update
