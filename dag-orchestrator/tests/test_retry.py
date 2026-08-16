"""Tests for retry-with-backoff behavior on task failure."""

from unittest.mock import patch

from dag_orchestrator.executor import Executor, Status
from dag_orchestrator.graph import Graph
from dag_orchestrator.task import Task


def test_task_succeeds_after_transient_failures_within_retry_budget():
    attempts: list[int] = []

    def flaky(context):
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("transient failure")
        return "ok"

    graph = Graph()
    graph.add_task(Task(name="flaky", func=flaky, max_retries=3, backoff_seconds=0))

    with patch("time.sleep") as mock_sleep:
        result = Executor(graph).run()

    assert len(attempts) == 3
    assert result.status_of("flaky") == Status.SUCCESS
    assert mock_sleep.call_count == 2  # slept between attempt 1->2 and 2->3


def test_task_fails_after_exhausting_all_retries():
    attempts: list[int] = []

    def always_fails(context):
        attempts.append(1)
        raise RuntimeError("permanent failure")

    graph = Graph()
    graph.add_task(
        Task(name="doomed", func=always_fails, max_retries=2, backoff_seconds=0)
    )

    with patch("time.sleep"):
        result = Executor(graph).run()

    # initial attempt + 2 retries = 3 total calls
    assert len(attempts) == 3
    assert result.status_of("doomed") == Status.FAILED


def test_zero_retries_means_single_attempt():
    attempts: list[int] = []

    def always_fails(context):
        attempts.append(1)
        raise RuntimeError("nope")

    graph = Graph()
    graph.add_task(Task(name="a", func=always_fails, max_retries=0))

    result = Executor(graph).run()

    assert len(attempts) == 1
    assert result.status_of("a") == Status.FAILED


def test_backoff_delay_grows_exponentially_between_attempts():
    def always_fails(context):
        raise RuntimeError("nope")

    graph = Graph()
    graph.add_task(
        Task(name="a", func=always_fails, max_retries=3, backoff_seconds=1.0)
    )

    with patch("time.sleep") as mock_sleep:
        Executor(graph).run()

    delays = [call.args[0] for call in mock_sleep.call_args_list]
    assert delays == [1.0, 2.0, 4.0]


def test_retry_count_is_recorded_in_result():
    attempts: list[int] = []

    def flaky(context):
        attempts.append(1)
        if len(attempts) < 2:
            raise RuntimeError("transient")

    graph = Graph()
    graph.add_task(Task(name="flaky", func=flaky, max_retries=3, backoff_seconds=0))

    with patch("time.sleep"):
        result = Executor(graph).run()

    assert result.attempts_of("flaky") == 2
