"""Validator agent: applies business rules to extracted Records.

The Extractor already guarantees every :class:`Record` has the right
*shape*. The Validator checks whether the *values* make sense: is the
tag well-formed, is the category one this library actually stocks, is
the condition one of the three the front desk recognizes, is the
quantity sane. A record can fail more than one rule at once -- all
violations are collected and reported together rather than stopping at
the first one, so a single pass tells the whole story.
"""

from __future__ import annotations

import re

from reconciliation_agents.messages import ExtractedBatch, ValidatedBatch
from reconciliation_agents.records import (
    VALID_CATEGORIES,
    VALID_CONDITIONS,
    InvalidRecord,
    Record,
)

_TAG_ID_PATTERN = re.compile(r"^TL-\d{1,6}$")


class ValidatorAgent:
    """Checks an :class:`ExtractedBatch` against business rules.

    Every record in the input batch ends up in exactly one of
    ``result.valid_records`` or ``result.invalid_records`` -- validation
    never silently drops a record, it flags it.
    """

    def run(self, batch: ExtractedBatch) -> ValidatedBatch:
        valid: list[Record] = []
        invalid: list[InvalidRecord] = []

        for record in batch.records:
            reasons = self._violations(record)
            if reasons:
                invalid.append(InvalidRecord(record=record, reasons=tuple(reasons)))
            else:
                valid.append(record)

        return ValidatedBatch(source=batch.source, valid_records=valid, invalid_records=invalid)

    def _violations(self, record: Record) -> list[str]:
        reasons: list[str] = []

        if not _TAG_ID_PATTERN.match(record.tag_id):
            reasons.append(f"malformed tag_id: {record.tag_id!r} (expected TL-#####)")

        if not record.tool_name:
            reasons.append("missing tool_name")

        if record.category not in VALID_CATEGORIES:
            reasons.append(f"unknown category: {record.category!r}")

        if record.condition not in VALID_CONDITIONS:
            reasons.append(f"unknown condition: {record.condition!r}")

        if record.quantity < 1:
            reasons.append(f"quantity must be positive, got {record.quantity}")

        if not record.location_bin:
            reasons.append("missing location_bin")

        return reasons
