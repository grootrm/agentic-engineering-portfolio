"""A single candidate implementation proposed for a problem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    """One proposed implementation in the propose -> test -> keep loop.

    Attributes:
        id: Unique identifier within a run (also used as the archive key).
        source: Full Python source of the candidate module.
        strategy: Name of the mutation rule (or "seed") that produced this
            candidate. Used by the proposer to avoid retrying a rule it has
            already tried against a given lineage.
        parent_id: Id of the candidate this one was derived from, or
            ``None`` for the initial seed.
        generation: 0 for the seed, otherwise parent's generation + 1.
    """

    id: str
    source: str
    strategy: str
    parent_id: str | None
    generation: int
