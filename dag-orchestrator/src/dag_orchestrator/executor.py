"""Executes a task graph in dependency order with retry-with-backoff."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from dag_orchestrator.graph import Graph


class Status(Enum):
    PENDING = auto()
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class RunResult:
    """Outcome of an :meth:`Executor.run` call."""

    context: dict[str, Any] = field(default_factory=dict)
    _status: dict[str, Status] = field(default_factory=dict)
    _attempts: dict[str, int] = field(default_factory=dict)

    def status_of(self, task_name: str) -> Status:
        return self._status.get(task_name, Status.PENDING)

    def attempts_of(self, task_name: str) -> int:
        return self._attempts.get(task_name, 0)

    @property
    def success(self) -> bool:
        return all(
            status != Status.FAILED for status in self._status.values()
        )


class Executor:
    """Runs every task in ``graph`` in topological order.

    On failure, a task is retried up to ``task.max_retries`` additional
    times with exponential backoff (``backoff_seconds * 2 ** attempt``
    between attempts). If a task ultimately fails, every task that
    (transitively) depends on it is marked SKIPPED rather than executed.
    """

    def __init__(self, graph: Graph):
        self.graph = graph

    def run(self) -> RunResult:
        order = self.graph.topological_order()
        result = RunResult()

        for name in order:
            task = self.graph[name]

            if any(
                result.status_of(dep) in (Status.FAILED, Status.SKIPPED)
                for dep in task.depends_on
            ):
                result._status[name] = Status.SKIPPED
                continue

            success, value = self._run_with_retries(task, result)
            if success:
                result._status[name] = Status.SUCCESS
                result.context[name] = value
            else:
                result._status[name] = Status.FAILED

        return result

    def _run_with_retries(self, task, result: RunResult) -> tuple[bool, Any]:
        total_attempts = task.max_retries + 1
        last_error: BaseException | None = None

        for attempt in range(total_attempts):
            result._attempts[task.name] = attempt + 1
            try:
                value = task.func(result.context)
                return True, value
            except Exception as exc:  # noqa: BLE001 - intentional catch-all
                last_error = exc
                is_last_attempt = attempt == total_attempts - 1
                if not is_last_attempt:
                    delay = task.backoff_seconds * (2 ** attempt)
                    time.sleep(delay)

        return False, last_error
