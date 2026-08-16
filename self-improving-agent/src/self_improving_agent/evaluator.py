"""Scores a candidate by running it against a problem's fixed pytest suite."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of running one candidate against a problem's test suite.

    Attributes:
        passed: Node ids of tests that passed.
        failed: Node ids of tests that failed (including collection/import
            errors attributed to specific tests, when pytest can do so).
        errored: True if the candidate could not be evaluated at all (e.g.
            a syntax error, or a collection failure with no per-test
            results). ``passed``/``failed`` are empty in that case.
    """

    passed: frozenset[str]
    failed: frozenset[str]
    errored: bool = False

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    @property
    def all_passed(self) -> bool:
        return bool(self.passed) and not self.failed and not self.errored
