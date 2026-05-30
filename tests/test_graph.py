from unittest.mock import patch
from forgelab.graph import build_graph
from forgelab.state import WorkflowState


def test_graph_compiles_without_error():
    graph = build_graph()
    assert graph is not None


def test_graph_has_evaluator_as_entry():
    graph = build_graph()
    assert "evaluator" in graph.nodes
