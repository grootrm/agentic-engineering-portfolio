#!/usr/bin/env python
"""Demo runner: reconciles two synthetic Millbrook Tool Library inventory snapshots.

    python run.py
    python run.py --record-count 100 --seed 7

Always exits 0 -- unlike a scheduled pipeline, a reconciliation run that
finds discrepancies hasn't "failed," it's done its job. The discrepancies
are the point.
"""

from __future__ import annotations

import argparse
import json
import sys

from pipeline.tool_library_pipeline import build_and_run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for synthetic inventory data")
    parser.add_argument(
        "--record-count",
        type=int,
        default=40,
        help="number of synthetic tools to generate before malformed/duplicate rows are layered on",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    run = build_and_run(seed=args.seed, record_count=args.record_count)
    report = run.report

    print("Millbrook Tool Library -- nightly reconciliation\n")

    for batch in (run.ledger_validated, run.sweep_validated):
        print(
            f"  {batch.source}: {len(batch.valid_records)} valid, "
            f"{len(batch.invalid_records)} invalid records"
        )

    print(f"\nComparing {report.source_a} vs {report.source_b}:")
    print(f"  matched:              {len(report.matched)}")
    print(f"  missing in {report.source_a:<15}: {len(report.missing_in_a)}")
    print(f"  missing in {report.source_b:<15}: {len(report.missing_in_b)}")
    print(f"  quantity mismatches:  {len(report.quantity_mismatches)}")
    print(f"  condition mismatches: {len(report.condition_mismatches)}")
    print(f"  duplicate tags:       {sum(len(v) for v in report.duplicate_tags.values())}")

    print("\nDiscrepancy detail:")
    print(
        json.dumps(
            {
                "missing_in_" + report.source_a: report.missing_in_a,
                "missing_in_" + report.source_b: report.missing_in_b,
                "quantity_mismatches": report.quantity_mismatches,
                "condition_mismatches": report.condition_mismatches,
                "duplicate_tags": report.duplicate_tags,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
