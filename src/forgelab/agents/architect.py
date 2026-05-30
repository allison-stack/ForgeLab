"""Architect — implementation planning."""
from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _ArchitectAgent(BaseAgent):
    role = "architect"


_agent = _ArchitectAgent()


def run(state: WorkflowState) -> dict:
    user_msg = (
        f"Task: {state['task']}\n\n"
        f"Researcher findings:\n{state.get('findings', '(none)')}"
    )
    raw, tokens = _agent.call(user_msg)
    update: dict = {"plan": raw}
    update.update(BaseAgent._add_cost(state, "architect", tokens))
    return update
