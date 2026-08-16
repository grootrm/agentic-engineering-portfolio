"""Tests for topological execution order via the Executor."""

from dag_orchestrator.executor import Executor, Status
from dag_orchestrator.graph import Graph
from dag_orchestrator.task import Task


def test_executor_runs_every_task_exactly_once():
    calls: list[str] = []

    def make(name):
        def _fn(context):
            calls.append(name)
            return name

        return _fn

    graph = Graph()
    graph.add_task(Task(name="extract", func=make("extract")))
    graph.add_task(Task(name="transform", func=make("transform"), depends_on=["extract"]))
    graph.add_task(Task(name="load", func=make("load"), depends_on=["transform"]))

    result = Executor(graph).run()

    assert calls == ["extract", "transform", "load"]
    assert result.status_of("extract") == Status.SUCCESS
    assert result.status_of("transform") == Status.SUCCESS
    assert result.status_of("load") == Status.SUCCESS


def test_executor_runs_dependencies_before_dependents_in_diamond():
    calls: list[str] = []

    def make(name):
        def _fn(context):
            calls.append(name)

        return _fn

    graph = Graph()
    graph.add_task(Task(name="ingest", func=make("ingest")))
    graph.add_task(Task(name="clean_a", func=make("clean_a"), depends_on=["ingest"]))
    graph.add_task(Task(name="clean_b", func=make("clean_b"), depends_on=["ingest"]))
    graph.add_task(
        Task(name="merge", func=make("merge"), depends_on=["clean_a", "clean_b"])
    )

    Executor(graph).run()

    assert calls[0] == "ingest"
    assert calls[-1] == "merge"
    assert set(calls[1:3]) == {"clean_a", "clean_b"}


def test_task_return_value_is_stored_in_shared_context():
    def produce(context):
        return 42

    def consume(context):
        context["seen"] = context["produce"]

    graph = Graph()
    graph.add_task(Task(name="produce", func=produce))
    graph.add_task(Task(name="consume", func=consume, depends_on=["produce"]))

    result = Executor(graph).run()

    assert result.context["produce"] == 42
    assert result.context["seen"] == 42


def test_failed_task_marks_downstream_dependents_as_skipped():
    def boom(context):
        raise RuntimeError("upstream broke")

    def never_runs(context):
        raise AssertionError("should not have run")

    graph = Graph()
    graph.add_task(Task(name="broken", func=boom))
    graph.add_task(Task(name="downstream", func=never_runs, depends_on=["broken"]))

    result = Executor(graph).run()

    assert result.status_of("broken") == Status.FAILED
    assert result.status_of("downstream") == Status.SKIPPED
    assert result.success is False


def test_independent_task_still_runs_after_unrelated_task_fails():
    calls: list[str] = []

    def boom(context):
        raise RuntimeError("boom")

    def fine(context):
        calls.append("fine")

    graph = Graph()
    graph.add_task(Task(name="broken", func=boom))
    graph.add_task(Task(name="independent", func=fine))

    result = Executor(graph).run()

    assert calls == ["fine"]
    assert result.status_of("independent") == Status.SUCCESS


def test_all_success_result_reports_overall_success():
    graph = Graph()
    graph.add_task(Task(name="a", func=lambda context: None))

    result = Executor(graph).run()

    assert result.success is True
