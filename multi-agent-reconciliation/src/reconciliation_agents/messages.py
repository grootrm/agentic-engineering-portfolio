"""Message contracts exchanged between agents.

Each agent in this pipeline is a small, single-responsibility worker that
speaks a fixed input/output contract -- these dataclasses -- rather than
being three functions chained together with no boundary between them. The
contract is what makes the handoff real: the Extractor never sees a
Validator's internals, and the Reconciler never sees a raw row. Every
agent only ever receives the exact message type the agent before it
promised to produce, and every agent's ``.run()`` method returns exactly
one of these, never a bag of ad-hoc values.

    RawRecordBatch  --Extractor-->  ExtractedBatch  --Validator-->  ValidatedBatch
                                                                          |
                            ValidatedBatch (source A) --+                |
                                                         Reconciler --> DiscrepancyReport
                            ValidatedBatch (source B) --+
"""

from __future__ import annotations

from dataclasses import dataclass, field

from reconciliation_agents.records import ExtractionError, InvalidRecord, Record


@dataclass(frozen=True)
class RawRecordBatch:
    """Input to the Extractor: one source system's raw, unnormalized rows.

    ``source`` is a free-form label (e.g. ``"checkout_ledger"``) -- the
    Extractor does not branch on it. It normalizes each row purely by
    inspecting which fields are present, so it works for any source that
    speaks a field-name dialect the alias table understands.
    """

    source: str
    rows: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ExtractedBatch:
    """Output of the Extractor / input to the Validator.

    Every row from the originating :class:`RawRecordBatch` ends up in
    exactly one of ``records`` or ``extraction_errors`` -- nothing is
    silently dropped.
    """

    source: str
    records: list[Record] = field(default_factory=list)
    extraction_errors: list[ExtractionError] = field(default_factory=list)


@dataclass(frozen=True)
class ValidatedBatch:
    """Output of the Validator / input to the Reconciler.

    Every record from the originating :class:`ExtractedBatch` ends up in
    exactly one of ``valid_records`` or ``invalid_records``.
    """

    source: str
    valid_records: list[Record] = field(default_factory=list)
    invalid_records: list[InvalidRecord] = field(default_factory=list)


@dataclass(frozen=True)
class DiscrepancyReport:
    """Output of the Reconciler: where two sources' inventories disagree.

    ``source_a`` / ``source_b`` name the two inputs so the report reads
    as "A says X, B says Y" rather than losing provenance. Every tag_id
    that is a duplicate within one source is excluded from the matching
    logic (its identity is already unreliable) and reported separately
    in ``duplicate_tags``.
    """

    source_a: str
    source_b: str
    matched: list[str] = field(default_factory=list)
    missing_in_a: list[str] = field(default_factory=list)
    missing_in_b: list[str] = field(default_factory=list)
    quantity_mismatches: list[dict] = field(default_factory=list)
    condition_mismatches: list[dict] = field(default_factory=list)
    duplicate_tags: dict[str, list[str]] = field(default_factory=dict)
