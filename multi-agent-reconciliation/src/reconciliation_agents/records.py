"""Canonical record shape shared by every agent in the pipeline.

This module is the vocabulary the agents speak: the Extractor produces
``Record`` objects, the Validator passes or rejects them, and the
Reconciler compares them across two independently captured sources.
Nobody downstream of the Extractor ever looks at a raw row again.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CATEGORIES = frozenset(
    {"power_tool", "hand_tool", "ladder", "yard_equipment", "other"}
)
VALID_CONDITIONS = frozenset({"good", "fair", "needs_repair"})


@dataclass(frozen=True)
class Record:
    """A single tool's state, normalized to the pipeline's canonical shape.

    Attributes:
        tag_id: Unique asset tag printed on the tool (e.g. ``"TL-04231"``).
        tool_name: Human-readable name (e.g. ``"Cordless Drill"``).
        category: One of ``VALID_CATEGORIES`` once validated -- the
            Extractor does not enforce this, only the Validator does.
        condition: One of ``VALID_CONDITIONS`` once validated.
        quantity: Number of units held under this tag (most tags are 1,
            but consumable-style items like extension cords are pooled).
        location_bin: Storage bin code (e.g. ``"A3"``).
    """

    tag_id: str
    tool_name: str
    category: str
    condition: str
    quantity: int
    location_bin: str


@dataclass(frozen=True)
class ExtractionError:
    """A raw row that could not be parsed into a :class:`Record` at all.

    Distinct from an :class:`InvalidRecord`: this is a *shape* failure
    (we don't even know what tool this row was describing), not a
    business-rule failure.
    """

    raw_row: dict
    reason: str


@dataclass(frozen=True)
class InvalidRecord:
    """A successfully-parsed :class:`Record` that failed business rules."""

    record: Record
    reasons: tuple[str, ...]
