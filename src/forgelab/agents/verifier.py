"""Verifier — test generation + Docker sandbox execution."""
from forgelab.agents.base import BaseAgent
from forgelab.executor import run_test
from forgelab.state import WorkflowState


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

    exec_result = run_test(
        target_code=state.get("code_changes") or _TEST_STUB,
        test_code=test_code,
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
