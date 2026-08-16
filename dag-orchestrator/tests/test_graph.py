"""Tests for graph construction and topological ordering."""

from dag_orchestrator.graph import Graph
from dag_orchestrator.task import Task


def _noop(**kwargs):
    return None


def test_single_task_graph_orders_that_task_alone():
    graph = Graph()
    graph.add_task(Task(name="a", func=_noop))

    order = graph.topological_order()

    assert order == ["a"]


def test_linear_chain_is_ordered_upstream_first():
    graph = Graph()
    graph.add_task(Task(name="extract", func=_noop))
    graph.add_task(Task(name="transform", func=_noop, depends_on=["extract"]))
    graph.add_task(Task(name="load", func=_noop, depends_on=["transform"]))

    order = graph.topological_order()

    assert order.index("extract") < order.index("transform")
    assert order.index("transform") < order.index("load")


def test_diamond_shaped_graph_respects_all_dependencies():
    # ingest -> {clean_a, clean_b} -> merge
    graph = Graph()
    graph.add_task(Task(name="ingest", func=_noop))
    graph.add_task(Task(name="clean_a", func=_noop, depends_on=["ingest"]))
    graph.add_task(Task(name="clean_b", func=_noop, depends_on=["ingest"]))
    graph.add_task(
        Task(name="merge", func=_noop, depends_on=["clean_a", "clean_b"])
    )

    order = graph.topological_order()

    assert order.index("ingest") < order.index("clean_a")
    assert order.index("ingest") < order.index("clean_b")
    assert order.index("clean_a") < order.index("merge")
    assert order.index("clean_b") < order.index("merge")


def test_unknown_dependency_raises_value_error():
    graph = Graph()
    graph.add_task(Task(name="a", func=_noop, depends_on=["missing"]))

    import pytest

    with pytest.raises(ValueError, match="missing"):
        graph.topological_order()


def test_duplicate_task_name_raises_value_error():
    graph = Graph()
    graph.add_task(Task(name="a", func=_noop))

    import pytest

    with pytest.raises(ValueError, match="a"):
        graph.add_task(Task(name="a", func=_noop))
