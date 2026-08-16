"""Extractor agent: normalizes raw, source-specific rows into canonical
:class:`~reconciliation_agents.records.Record` objects.

The two source systems in the demo domain describe the same tool with
different field names and different condition encodings (a checkout
ledger uses abbreviated codes like ``"cond": "G"``, a shelf-audit sweep
spells them out as ``"condition": "good"``). This agent's whole job is to
absorb that dialect difference so nothing downstream of it ever has to
know which system a record came from.

A row that cannot be identified (no tag) or cannot be type-coerced (a
quantity that isn't a number) is a *shape* failure and becomes an
:class:`~reconciliation_agents.records.ExtractionError` rather than a
:class:`~reconciliation_agents.records.Record` -- business-rule failures
(unknown category, non-positive quantity, and so on) are the Validator's
concern, not this agent's.
"""

from __future__ import annotations

from reconciliation_agents.messages import ExtractedBatch, RawRecordBatch
from reconciliation_agents.records import ExtractionError, Record

# Each canonical field may appear under any of these raw key names,
# depending on which source system produced the row.
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "tag_id": ("tag_id", "tag"),
    "tool_name": ("tool_name", "name"),
    "category": ("category", "cat"),
    "condition": ("condition", "cond"),
    "quantity": ("quantity", "qty"),
    "location_bin": ("location_bin", "bin", "bin_location"),
}

# Condition values as they might arrive: abbreviated ledger codes and
# already-spelled-out sweep values both normalize to the same three
# canonical strings.
_CONDITION_CODES: dict[str, str] = {
    "g": "good",
    "f": "fair",
    "r": "needs_repair",
    "good": "good",
    "fair": "fair",
    "needs_repair": "needs_repair",
}

_DEFAULT_QUANTITY = 1


def _first_present(row: dict, aliases: tuple[str, ...]) -> object | None:
    for key in aliases:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


class ExtractorAgent:
    """Normalizes a :class:`RawRecordBatch` into an :class:`ExtractedBatch`.

    Every row in the input batch ends up in exactly one of
    ``result.records`` or ``result.extraction_errors`` -- extraction never
    silently drops a row.
    """

    def run(self, batch: RawRecordBatch) -> ExtractedBatch:
        records: list[Record] = []
        errors: list[ExtractionError] = []

        for row in batch.rows:
            try:
                records.append(self._extract_row(row))
            except _ExtractionFailure as failure:
                errors.append(ExtractionError(raw_row=row, reason=failure.reason))

        return ExtractedBatch(source=batch.source, records=records, extraction_errors=errors)

    def _extract_row(self, row: dict) -> Record:
        tag_id = _first_present(row, _FIELD_ALIASES["tag_id"])
        if tag_id is None:
            raise _ExtractionFailure("missing tag_id: row does not identify a tool")

        tool_name = _first_present(row, _FIELD_ALIASES["tool_name"]) or ""
        category = str(_first_present(row, _FIELD_ALIASES["category"]) or "").strip().lower()
        condition_raw = str(_first_present(row, _FIELD_ALIASES["condition"]) or "").strip().lower()
        location_bin = _first_present(row, _FIELD_ALIASES["location_bin"]) or ""

        quantity_raw = _first_present(row, _FIELD_ALIASES["quantity"])
        quantity = self._coerce_quantity(quantity_raw)

        condition = _CONDITION_CODES.get(condition_raw, condition_raw)

        return Record(
            tag_id=str(tag_id).strip(),
            tool_name=str(tool_name).strip(),
            category=category,
            condition=condition,
            quantity=quantity,
            location_bin=str(location_bin).strip(),
        )

    def _coerce_quantity(self, quantity_raw: object | None) -> int:
        if quantity_raw is None:
            return _DEFAULT_QUANTITY
        try:
            return int(quantity_raw)
        except (TypeError, ValueError) as exc:
            raise _ExtractionFailure(
                f"quantity is not a valid integer: {quantity_raw!r}"
            ) from exc


class _ExtractionFailure(Exception):
    """Internal control-flow exception carrying a human-readable reason."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)
