"""Researcher — codebase search + web browsing synthesis.
Searches Path.cwd() — always the target repo since `forgelab start` runs from its root.
"""
import subprocess
from pathlib import Path

from forgelab.agents.base import BaseAgent
from forgelab.state import WorkflowState


class _ResearcherAgent(BaseAgent):
    role = "researcher"


_agent = _ResearcherAgent()


def _search_codebase(pattern: str) -> str:
    target = Path.cwd()
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", pattern, str(target)],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout[:3000] or "(no matches)"
    except Exception as e:
        return f"(search error: {e})"


def run(state: WorkflowState) -> dict:
    context = f"Task: {state['task']}\nTask type: {state.get('task_type', 'unknown')}"
    keywords = state["task"].split()[:5]
    grep_results = "\n".join(
        f"=== grep: {kw} ===\n{_search_codebase(kw)}" for kw in keywords if len(kw) > 4
    )
    user_msg = f"{context}\n\nCodebase search results:\n{grep_results}"

    raw, tokens = _agent.call(user_msg)
    update: dict = {"findings": raw}
    update.update(BaseAgent._add_cost(state, "researcher", tokens))
    return update
