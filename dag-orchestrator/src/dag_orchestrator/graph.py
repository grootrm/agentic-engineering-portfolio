"""Dependency graph: task registration, cycle detection, topological order."""

from __future__ import annotations

from dag_orchestrator.errors import CycleError
from dag_orchestrator.task import Task


class Graph:
    """A directed graph of :class:`Task` nodes keyed by task name."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        if task.name in self._tasks:
            raise ValueError(f"duplicate task name: '{task.name}'")
        self._tasks[task.name] = task

    def __contains__(self, name: str) -> bool:
        return name in self._tasks

    def __getitem__(self, name: str) -> Task:
        return self._tasks[name]

    def __len__(self) -> int:
        return len(self._tasks)

    @property
    def tasks(self) -> dict[str, Task]:
        return self._tasks

    def _validate_dependencies_exist(self) -> None:
        for task in self._tasks.values():
            for dep in task.depends_on:
                if dep not in self._tasks:
                    raise ValueError(
                        f"task '{task.name}' depends on unknown task '{dep}' (missing)"
                    )

    def topological_order(self) -> list[str]:
        """Return task names ordered so every dependency precedes its dependents.

        Raises:
            ValueError: if a task depends on a name not present in the graph.
            CycleError: if the graph contains a dependency cycle.
        """
        self._validate_dependencies_exist()

        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {name: WHITE for name in self._tasks}
        order: list[str] = []
        path: list[str] = []

        def visit(name: str) -> None:
            color[name] = GRAY
            path.append(name)
            for dep in self._tasks[name].depends_on:
                if color[dep] == WHITE:
                    visit(dep)
                elif color[dep] == GRAY:
                    cycle_start = path.index(dep)
                    raise CycleError(path[cycle_start:] + [dep])
            path.pop()
            color[name] = BLACK
            order.append(name)

        for name in self._tasks:
            if color[name] == WHITE:
                visit(name)

        return order
