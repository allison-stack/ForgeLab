"""Coder — minimal diff implementation."""
from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _CoderAgent(BaseAgent):
    role = "coder"


_agent = _CoderAgent()


def run(state: WorkflowState) -> dict:
    interrupt_note = ""
    if state.get("interrupt"):
        interrupt_note = f"\n\n⚡ User interrupt: {state['interrupt']}\nAdapt your implementation accordingly."

    user_msg = (
        f"Task: {state['task']}\n\n"
        f"Researcher findings:\n{state.get('findings', '(none)')}\n\n"
        f"Architect plan:\n{state.get('plan', '(none)')}"
        f"{interrupt_note}"
    )
    raw, tokens = _agent.call(user_msg)
    update: dict = {"code_changes": raw, "interrupt": None}
    update.update(BaseAgent._add_cost(state, "coder", tokens))
    return update
