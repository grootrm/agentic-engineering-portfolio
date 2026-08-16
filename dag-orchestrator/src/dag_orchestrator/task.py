"""Task node definition for the orchestrator's dependency graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Task:
    """A single unit of work in the pipeline.

    Attributes:
        name: Unique identifier for this task within a graph.
        func: Callable executed when the task runs. Receives the shared
            ``context`` dict as keyword arguments are not passed in;
            instead the executor calls ``func(context)``.
        depends_on: Names of tasks that must complete successfully before
            this task is eligible to run.
        max_retries: Number of retry attempts after an initial failure.
            0 means "try once, do not retry".
        backoff_seconds: Base delay used for exponential backoff between
            retry attempts (delay = backoff_seconds * 2 ** attempt_index).
    """

    name: str
    func: Callable[..., Any]
    depends_on: list[str] = field(default_factory=list)
    max_retries: int = 0
    backoff_seconds: float = 0.0
