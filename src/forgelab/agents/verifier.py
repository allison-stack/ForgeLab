"""Verifier — test generation + Docker sandbox execution."""
import re

from forgelab.agents.base import BaseAgent
from forgelab.executor import run_test
from forgelab.state import WorkflowState


def _extract_python(text: str) -> str:
    """Pull the last Python code block from a markdown diff, or return text as-is."""
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if blocks:
        # Take the last block — likely the "new code" in a before/after diff
        return blocks[-1].strip()
    return text


class _VerifierAgent(BaseAgent):
    role = "verifier"


_agent = _VerifierAgent()

_TEST_STUB = "def target(): pass"


def run(state: WorkflowState) -> dict:
    user_msg = (
        f"Task: {state['task']}\n\n"
        f"Code changes:\n{state.get('code_changes', '(none)')}"
    )
    test_code, tokens = _agent.call(user_msg)

    raw_changes = state.get("code_changes") or _TEST_STUB
    target_code = _extract_python(raw_changes) or raw_changes

    exec_result = run_test(
        target_code=target_code,
        test_code=test_code,
        framework=state.get("test_framework", "pytest"),
    )

    test_results = {
        "passed": exec_result.passed,
        "stdout": exec_result.stdout,
        "stderr": exec_result.stderr,
        "timed_out": exec_result.timed_out,
        "tests_run": test_code.count("def test_"),
    }
    update: dict = {"test_results": test_results}
    update.update(BaseAgent._add_cost(state, "verifier", tokens))
    return update
