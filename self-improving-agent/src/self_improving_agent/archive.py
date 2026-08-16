"""Lineage-tracked archive of kept candidates.

A candidate enters the archive only if it is a genuine improvement over
its parent: the initial seed is always kept as the baseline, and any
later candidate is kept only if it passes a strict superset of the tests
its parent passed. Regressions and no-op mutations are evaluated (the
caller sees the :class:`~self_improving_agent.evaluator.EvaluationResult`)
but never enter the archive, so the archive always reflects a monotonic
improvement history.
"""

from __future__ import annotations

from dataclasses import dataclass

from self_improving_agent.candidate import Candidate
from self_improving_agent.evaluator import EvaluationResult


@dataclass(frozen=True)
class ArchiveEntry:
    """A kept candidate, together with why it was kept."""

    candidate: Candidate
    passed_tests: frozenset[str]
    failed_tests: frozenset[str]
    kept_reason: str

    @property
    def all_passed(self) -> bool:
        return bool(self.passed_tests) and not self.failed_tests


class Archive:
    """Stores kept candidates, keyed by id, with parent/child lineage."""

    def __init__(self) -> None:
        self._entries: dict[str, ArchiveEntry] = {}

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries.values())

    def get(self, candidate_id: str) -> ArchiveEntry:
        return self._entries[candidate_id]

    def try_add(self, candidate: Candidate, result: EvaluationResult) -> ArchiveEntry | None:
        """Add ``candidate`` to the archive if it is worth keeping.

        Returns the new :class:`ArchiveEntry` if kept, or ``None`` if the
        candidate was rejected (it did not improve on its parent).
        """
        if candidate.parent_id is None:
            reason = f"initial seed -- passes {len(result.passed)}/{result.total} tests"
            entry = ArchiveEntry(candidate, result.passed, result.failed, reason)
            self._entries[candidate.id] = entry
            return entry

        parent = self._entries[candidate.parent_id]
        gained = result.passed - parent.passed_tests
        is_improvement = parent.passed_tests < result.passed  # strict superset
        if not is_improvement or not gained:
            return None

        reason = f"gained {sorted(gained)} beyond its predecessor (via '{candidate.strategy}')"
        entry = ArchiveEntry(candidate, result.passed, result.failed, reason)
        self._entries[candidate.id] = entry
        return entry

    def best(self) -> ArchiveEntry:
        """Return the kept entry with the most passing tests.

        Ties are broken by earliest generation, then insertion order.
        """
        return max(
            self._entries.values(),
            key=lambda entry: (len(entry.passed_tests), -entry.candidate.generation),
        )

    def lineage(self, candidate_id: str) -> list[ArchiveEntry]:
        """Return the chain of entries from the root seed to ``candidate_id``."""
        chain: list[ArchiveEntry] = []
        current: str | None = candidate_id
        while current is not None:
            entry = self._entries[current]
            chain.append(entry)
            current = entry.candidate.parent_id
        chain.reverse()
        return chain
