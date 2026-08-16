"""Millbrook Tool Library nightly reconciliation, wired end to end.

Two independent systems each take their own snapshot of the same
tool-lending library's inventory -- a front-desk checkout ledger and a
periodic shelf-audit sweep -- in their own dialects. This module wires the
three reconciliation agents together to turn those two raw snapshots into
one :class:`~reconciliation_agents.messages.DiscrepancyReport`:

    ledger rows  --Extractor--> ExtractedBatch --Validator--> ValidatedBatch --+
                                                                                |
                                                                          Reconciler --> DiscrepancyReport
                                                                                |
    sweep rows   --Extractor--> ExtractedBatch --Validator--> ValidatedBatch --+
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.dataset_generator import generate_inventory_sources
from reconciliation_agents.extractor import ExtractorAgent
from reconciliation_agents.messages import DiscrepancyReport, RawRecordBatch, ValidatedBatch
from reconciliation_agents.reconciler import ReconcilerAgent
from reconciliation_agents.validator import ValidatorAgent

LEDGER_SOURCE = "checkout_ledger"
SWEEP_SOURCE = "shelf_sweep"


@dataclass(frozen=True)
class PipelineRun:
    """Everything a caller needs from one end-to-end reconciliation run."""

    ledger_validated: ValidatedBatch
    sweep_validated: ValidatedBatch
    report: DiscrepancyReport


def _extract_and_validate(source: str, rows: list[dict]) -> ValidatedBatch:
    extracted = ExtractorAgent().run(RawRecordBatch(source=source, rows=rows))
    return ValidatorAgent().run(extracted)


def build_and_run(seed: int = 42, record_count: int = 40) -> PipelineRun:
    """Generate synthetic ledger/sweep data and run it through all three agents.

    Args:
        seed: RNG seed for reproducible synthetic inventory data.
        record_count: number of "true" tools to generate before malformed
            rows and duplicate-tag scenarios are layered on top.
    """
    ledger_rows, sweep_rows = generate_inventory_sources(seed=seed, record_count=record_count)

    ledger_validated = _extract_and_validate(LEDGER_SOURCE, ledger_rows)
    sweep_validated = _extract_and_validate(SWEEP_SOURCE, sweep_rows)

    report = ReconcilerAgent().run(ledger_validated, sweep_validated)

    return PipelineRun(
        ledger_validated=ledger_validated,
        sweep_validated=sweep_validated,
        report=report,
    )
