"""
LangGraph workflow — wires all agent nodes into a directed graph.
WorkflowState is the shared memory. All agents read/write the same state.
"""
from langgraph.graph import StateGraph, END

from forgelab.state import WorkflowState
from forgelab.agents import evaluator, router, researcher, architect, coder, reviewer, verifier


def _route_after_router(state: WorkflowState) -> str:
    return "researcher"


def _route_after_researcher(state: WorkflowState) -> str:
    task_type = state.get("task_type", "bug_fix")
    if task_type in ("new_feature", "architecture"):
        return "architect"
    if task_type == "code_review":
        return "reviewer"
    if task_type == "explain":
        return END
    return "coder"


def _route_after_reviewer(state: WorkflowState) -> str:
    feedback = state.get("review_feedback", "")
    if "APPROVED" in (feedback or "").upper():
        return "verifier"
    return "coder"


def build_graph():
    g = StateGraph(WorkflowState)

    g.add_node("evaluator", evaluator.run)
    g.add_node("router", router.run)
    g.add_node("researcher", researcher.run)
    g.add_node("architect", architect.run)
    g.add_node("coder", coder.run)
    g.add_node("reviewer", reviewer.run)
    g.add_node("verifier", verifier.run)

    g.set_entry_point("evaluator")
    g.add_edge("evaluator", "router")
    g.add_conditional_edges("router", _route_after_router)
    g.add_conditional_edges("researcher", _route_after_researcher)
    g.add_edge("architect", "coder")
    g.add_edge("coder", "reviewer")
    g.add_conditional_edges("reviewer", _route_after_reviewer)
    g.add_edge("verifier", END)

    return g.compile()
