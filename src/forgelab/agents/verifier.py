"""Verifier — test generation + Docker sandbox execution."""
import re

from forgelab.agents.base import BaseAgent
from forgelab.executor import run_test
from forgelab.state import WorkflowState


def _extract_python(text: str, join_all: bool = False) -> str:
    """
    Extract Python code from markdown-wrapped LLM output.

    join_all=False: return only the last block (for diffs — last block = new code).
    join_all=True:  return all blocks joined (for test output — each test is its own block).
    Falls back to the raw text if no fences found.
    """
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if blocks:
        if join_all:
            return "\n\n".join(b.strip() for b in blocks)
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
    raw_test_code, tokens = _agent.call(user_msg)
    # Defensively strip markdown fences if the model wraps output despite the prompt instruction
    test_code = _extract_python(raw_test_code, join_all=True) or raw_test_code

    raw_changes = state.get("code_changes") or _TEST_STUB
    target_code = _extract_python(raw_changes) or raw_changes

    # Ensure the test file imports from target.py — small models often forget this
    if "from target import" not in test_code and "import target" not in test_code:
        fn_names = re.findall(r"^def (\w+)\(", target_code, re.MULTILINE)
        if fn_names:
            test_code = f"from target import {', '.join(fn_names)}\n\n" + test_code

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
