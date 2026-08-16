"""Tests for cycle detection in the dependency graph."""

import pytest

from dag_orchestrator.errors import CycleError
from dag_orchestrator.graph import Graph
from dag_orchestrator.task import Task


def _noop(**kwargs):
    return None


def test_self_dependency_is_a_cycle():
    graph = Graph()
    graph.add_task(Task(name="a", func=_noop, depends_on=["a"]))

    with pytest.raises(CycleError):
        graph.topological_order()


def test_two_node_cycle_is_detected():
    graph = Graph()
    graph.add_task(Task(name="a", func=_noop, depends_on=["b"]))
    graph.add_task(Task(name="b", func=_noop, depends_on=["a"]))

    with pytest.raises(CycleError):
        graph.topological_order()


def test_longer_cycle_is_detected():
    graph = Graph()
    graph.add_task(Task(name="a", func=_noop, depends_on=["c"]))
    graph.add_task(Task(name="b", func=_noop, depends_on=["a"]))
    graph.add_task(Task(name="c", func=_noop, depends_on=["b"]))

    with pytest.raises(CycleError) as exc_info:
        graph.topological_order()

    # The reported cycle should mention every task involved.
    assert set(exc_info.value.cycle) == {"a", "b", "c"}


def test_cycle_detection_does_not_hang_on_large_cyclic_graph():
    """A cycle must be reported as an error, never cause an infinite loop."""
    graph = Graph()
    n = 200
    for i in range(n):
        graph.add_task(
            Task(name=f"t{i}", func=_noop, depends_on=[f"t{(i - 1) % n}"])
        )

    with pytest.raises(CycleError):
        graph.topological_order()


def test_acyclic_graph_with_shared_dependency_is_not_flagged_as_cycle():
    # Not a true cycle: two branches converge on the same task, they don't
    # depend on each other.
    graph = Graph()
    graph.add_task(Task(name="root", func=_noop))
    graph.add_task(Task(name="left", func=_noop, depends_on=["root"]))
    graph.add_task(Task(name="right", func=_noop, depends_on=["root"]))
    graph.add_task(
        Task(name="sink", func=_noop, depends_on=["left", "right"])
    )

    order = graph.topological_order()

    assert len(order) == 4
