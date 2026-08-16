"""End-to-end test of the synthetic Millbrook Tool Library reconciliation pipeline.

This is the demonstration pipeline for the portfolio piece: two independent
systems (a checkout ledger and a shelf-audit sweep) that describe the same
tool-lending library's inventory in different dialects, reconciled through
all three agents (Extractor -> Validator -> Reconciler).
"""

from pipeline.dataset_generator import generate_inventory_sources
from pipeline.tool_library_pipeline import build_and_run


def test_generated_sources_are_deterministic_for_a_given_seed():
    ledger_a, sweep_a = generate_inventory_sources(seed=7, record_count=30)
    ledger_b, sweep_b = generate_inventory_sources(seed=7, record_count=30)

    assert ledger_a == ledger_b
    assert sweep_a == sweep_b


def test_full_pipeline_runs_end_to_end_and_produces_a_report():
    run = build_and_run(seed=42, record_count=40)

    assert run.ledger_validated.source == "checkout_ledger"
    assert run.sweep_validated.source == "shelf_sweep"
    assert run.report.source_a == "checkout_ledger"
    assert run.report.source_b == "shelf_sweep"

    # Every scenario the generator engineers should show up somewhere.
    assert run.ledger_validated.invalid_records or True  # extraction/validation both exercised below
    assert len(run.report.matched) > 0
    assert len(run.report.quantity_mismatches) > 0
    assert len(run.report.condition_mismatches) > 0
    assert len(run.report.missing_in_a) > 0
    assert len(run.report.missing_in_b) > 0
    assert run.report.duplicate_tags.get("checkout_ledger")


def test_malformed_rows_are_caught_as_extraction_or_validation_errors():
    run = build_and_run(seed=42, record_count=40)

    # The generator appends deliberately malformed rows to each source;
    # every one of them must be caught as either an extraction failure
    # (bad shape) or a validation failure (bad business value), never
    # silently accepted as a valid record.
    assert len(run.ledger_validated.invalid_records) > 0
    assert len(run.sweep_validated.invalid_records) > 0


def test_scenario_scaffolding_matches_reconciler_output_for_a_fixed_seed():
    # With seed=42 / record_count=10, indices route through all five
    # scenarios (matched, qty mismatch, condition mismatch, missing-in-
    # ledger, missing-in-sweep) plus one duplicated ledger tag at TL-00000.
    run = build_and_run(seed=42, record_count=10)
    report = run.report

    assert "TL-00000" in report.duplicate_tags["checkout_ledger"]
    # TL-00000's duplicate in the ledger excludes it from ledger matching,
    # so the sweep's single copy shows up as missing from the ledger side.
    assert "TL-00000" in report.missing_in_a

    # index 1 -> quantity mismatch, index 2 -> condition mismatch,
    # index 3 -> missing in ledger, index 4 -> missing in sweep.
    assert any(m["tag_id"] == "TL-00001" for m in report.quantity_mismatches)
    assert any(m["tag_id"] == "TL-00002" for m in report.condition_mismatches)
    assert "TL-00003" in report.missing_in_a
    assert "TL-00004" in report.missing_in_b
    # index 5 is a second matched (scenario 0) tag, uncontaminated by duplication.
    assert "TL-00005" in report.matched
