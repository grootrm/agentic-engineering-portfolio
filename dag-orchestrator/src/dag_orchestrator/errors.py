"""Exceptions raised by the orchestrator."""


class CycleError(ValueError):
    """Raised when the task graph contains a dependency cycle."""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"dependency cycle detected: {cycle_str}")


class TaskFailedError(RuntimeError):
    """Raised when a task exhausts its retries without succeeding."""

    def __init__(self, task_name: str, cause: BaseException):
        self.task_name = task_name
        self.cause = cause
        super().__init__(f"task '{task_name}' failed: {cause!r}")
