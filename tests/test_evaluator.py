import json
import pytest
from unittest.mock import patch, MagicMock
from forgelab.agents.evaluator import run as evaluator_run
from forgelab.state import WorkflowState


def _base_state(task: str) -> WorkflowState:
    return WorkflowState(
        task=task, task_type=None, complexity=None,
        upgrade_recommendation=None, model_in_use="qwen2.5-coder:7b",
        findings=None, plan=None, code_changes=None,
        review_feedback=None, test_results=None,
        test_framework="pytest",
        agent_messages=[], session_cost={}, interrupt=None,
    )


def test_evaluator_writes_complexity():
    state = _base_state("Fix the login timeout bug in auth/oauth.py line 47")
    llm_output = json.dumps({
        "complexity": "complex",
        "upgrade_recommendation": {
            "task_type": "bug_fix",
            "recommended_model": "anthropic/claude-sonnet-4-6",
            "benchmark_reason": "SWE-bench 79.6%",
            "score": "79.6%",
            "cost_per_1m": "$15",
        },
    })
    with patch("forgelab.agents.evaluator._agent.call", return_value=(llm_output, 100)):
        result = evaluator_run(state)
    assert result["complexity"] == "complex"


def test_evaluator_sets_null_recommendation_for_simple():
    state = _base_state("fix typo in README")
    llm_output = json.dumps({"complexity": "simple", "upgrade_recommendation": None})
    with patch("forgelab.agents.evaluator._agent.call", return_value=(llm_output, 50)):
        result = evaluator_run(state)
    assert result["upgrade_recommendation"] is None
