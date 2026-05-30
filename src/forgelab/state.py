"""
WorkflowState — the shared memory all LangGraph nodes read and write.
Agents access fields directly; they do not touch LangGraph internals.
"""
from typing import TypedDict


class UpgradeRecommendation(TypedDict):
    task_type: str
    recommended_model: str
    benchmark_reason: str
    score: str
    cost_per_1m: str


class AgentCost(TypedDict):
    tokens: int
    cost_usd: float


class WorkflowState(TypedDict):
    # Core task
    task: str
    task_type: str | None
    complexity: str | None                        # simple|moderate|complex|critical
    upgrade_recommendation: UpgradeRecommendation | None
    model_in_use: str                             # active model ID

    # Agent outputs
    findings: str | None
    plan: str | None
    code_changes: str | None
    review_feedback: str | None
    test_results: dict | None                     # {passed, stdout, stderr, tests_run}
    test_framework: str                           # pytest (default) · cargo · jest · ctest · go-test

    # Communication
    agent_messages: list[dict]                    # {from, to, content, ts}
    session_cost: dict[str, AgentCost]            # keyed by agent name
    interrupt: str | None                         # user mid-task injection
