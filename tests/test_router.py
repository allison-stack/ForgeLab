import json
import pytest
from unittest.mock import patch
from forgelab.agents.router import run as router_run
from forgelab.state import WorkflowState


def _base_state(task: str, complexity: str | None = None) -> WorkflowState:
    return WorkflowState(
        task=task, task_type=None, complexity=complexity,
        upgrade_recommendation=None, model_in_use="qwen2.5-coder:7b",
        findings=None, plan=None, code_changes=None,
        review_feedback=None, test_results=None,
        test_framework="pytest",
        agent_messages=[], session_cost={}, interrupt=None,
    )


def test_router_classifies_bug_fix():
    state = _base_state("Fix the login timeout bug in auth/oauth.py", complexity="complex")
    llm_output = json.dumps({
        "task_type": "bug_fix",
        "pipeline": ["researcher", "coder", "reviewer", "verifier"],
    })
    with patch("forgelab.agents.router._agent.call", return_value=(llm_output, 80)):
        result = router_run(state)
    assert result["task_type"] == "bug_fix"


def test_router_defaults_to_bug_fix_on_invalid_type():
    state = _base_state("Fix the login timeout bug", complexity="moderate")
    llm_output = json.dumps({
        "task_type": "invalid_type",
        "pipeline": [],
    })
    with patch("forgelab.agents.router._agent.call", return_value=(llm_output, 50)):
        result = router_run(state)
    assert result["task_type"] == "bug_fix"


def test_router_defaults_to_bug_fix_on_malformed_json():
    state = _base_state("Some task", complexity="simple")
    llm_output = "This is not JSON"
    with patch("forgelab.agents.router._agent.call", return_value=(llm_output, 30)):
        result = router_run(state)
    assert result["task_type"] == "bug_fix"


def test_router_includes_cost():
    state = _base_state("Fix a bug", complexity="moderate")
    llm_output = json.dumps({"task_type": "bug_fix"})
    with patch("forgelab.agents.router._agent.call", return_value=(llm_output, 75)):
        result = router_run(state)
    assert "session_cost" in result
    assert "router" in result["session_cost"]
    assert result["session_cost"]["router"]["tokens"] == 75
