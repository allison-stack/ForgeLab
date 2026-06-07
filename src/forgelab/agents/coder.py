"""Coder — minimal diff implementation."""
from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _CoderAgent(BaseAgent):
    role = "coder"


_agent = _CoderAgent()

_MAX_ATTEMPTS = 3


def _is_valid_diff(text: str) -> bool:
    return "---" in text and "+++" in text and "@@" in text


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

    raw, tokens_total = "", 0
    for attempt in range(_MAX_ATTEMPTS):
        raw, tokens = _agent.call(user_msg)
        tokens_total += tokens
        if _is_valid_diff(raw):
            break
        if attempt < _MAX_ATTEMPTS - 1:
            user_msg = (
                f"That output is not a unified diff.\n\n"
                f"Your previous output was:\n{raw}\n\n"
                f"Output ONLY a unified diff. Nothing else. "
                f"It must contain --- a/..., +++ b/..., and @@ lines."
            )

    update: dict = {"code_changes": raw, "interrupt": None}
    update.update(BaseAgent._add_cost(state, "coder", tokens_total))
    return update
