"""Reconciler agent: cross-references two independently validated
inventories and reports where they disagree.

This is the agent that actually does the "reconciliation" the project is
named for. It takes the *valid* records from two sources -- never the
raw rows, never the invalid ones, only what the Validator already
promised are well-formed -- and produces a :class:`DiscrepancyReport`:
records present in only one source, records present in both but with
conflicting quantity or condition, and tag_ids that are internally
duplicated within a single source (which makes that source's claim
about the tag unreliable, so those tags are excluded from matching and
reported on their own).
"""

from __future__ import annotations

from collections import Counter

from reconciliation_agents.messages import DiscrepancyReport, ValidatedBatch
from reconciliation_agents.records import Record


def _duplicate_tags(records: list[Record]) -> list[str]:
    counts = Counter(r.tag_id for r in records)
    return sorted(tag for tag, count in counts.items() if count > 1)


def _by_tag_excluding_duplicates(records: list[Record], duplicates: set[str]) -> dict[str, Record]:
    return {r.tag_id: r for r in records if r.tag_id not in duplicates}


class ReconcilerAgent:
    """Compares two :class:`ValidatedBatch` inputs and reports discrepancies."""

    def run(self, batch_a: ValidatedBatch, batch_b: ValidatedBatch) -> DiscrepancyReport:
        dup_a = set(_duplicate_tags(batch_a.valid_records))
        dup_b = set(_duplicate_tags(batch_b.valid_records))

        by_tag_a = _by_tag_excluding_duplicates(batch_a.valid_records, dup_a)
        by_tag_b = _by_tag_excluding_duplicates(batch_b.valid_records, dup_b)

        tags_a, tags_b = set(by_tag_a), set(by_tag_b)
        shared_tags = tags_a & tags_b

        matched: list[str] = []
        quantity_mismatches: list[dict] = []
        condition_mismatches: list[dict] = []

        for tag_id in sorted(shared_tags):
            record_a, record_b = by_tag_a[tag_id], by_tag_b[tag_id]
            has_mismatch = False

            if record_a.quantity != record_b.quantity:
                quantity_mismatches.append(
                    {"tag_id": tag_id, "quantity_a": record_a.quantity, "quantity_b": record_b.quantity}
                )
                has_mismatch = True

            if record_a.condition != record_b.condition:
                condition_mismatches.append(
                    {"tag_id": tag_id, "condition_a": record_a.condition, "condition_b": record_b.condition}
                )
                has_mismatch = True

            if not has_mismatch:
                matched.append(tag_id)

        duplicate_tags = {}
        if dup_a:
            duplicate_tags[batch_a.source] = sorted(dup_a)
        if dup_b:
            duplicate_tags[batch_b.source] = sorted(dup_b)

        return DiscrepancyReport(
            source_a=batch_a.source,
            source_b=batch_b.source,
            matched=matched,
            missing_in_a=sorted(tags_b - tags_a),
            missing_in_b=sorted(tags_a - tags_b),
            quantity_mismatches=quantity_mismatches,
            condition_mismatches=condition_mismatches,
            duplicate_tags=duplicate_tags,
        )
