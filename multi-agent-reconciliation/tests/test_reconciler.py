"""Tests for the Reconciler agent: cross-references two independently
validated inventories and reports where they disagree.

The two ``ValidatedBatch`` inputs represent the "same" real-world tool
inventory as captured by two independent systems (a checkout ledger and
a shelf-audit sweep). They should mostly agree; the Reconciler's job is
to surface exactly where and how they don't.
"""

from reconciliation_agents.messages import ValidatedBatch
from reconciliation_agents.reconciler import ReconcilerAgent
from reconciliation_agents.records import Record


def _record(**overrides) -> Record:
    defaults = dict(
        tag_id="TL-1",
        tool_name="Cordless Drill",
        category="power_tool",
        condition="good",
        quantity=1,
        location_bin="A3",
    )
    defaults.update(overrides)
    return Record(**defaults)


def test_identical_records_in_both_sources_are_matched():
    ledger = ValidatedBatch(source="checkout_ledger", valid_records=[_record()])
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[_record()])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.matched == ["TL-1"]
    assert report.missing_in_b == []
    assert report.missing_in_a == []
    assert report.quantity_mismatches == []
    assert report.condition_mismatches == []


def test_record_present_only_in_ledger_is_missing_in_sweep():
    ledger = ValidatedBatch(source="checkout_ledger", valid_records=[_record(tag_id="TL-1")])
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.missing_in_b == ["TL-1"]
    assert report.missing_in_a == []
    assert report.matched == []


def test_record_present_only_in_sweep_is_missing_in_ledger():
    ledger = ValidatedBatch(source="checkout_ledger", valid_records=[])
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[_record(tag_id="TL-1")])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.missing_in_a == ["TL-1"]
    assert report.missing_in_b == []


def test_quantity_mismatch_is_flagged():
    ledger = ValidatedBatch(source="checkout_ledger", valid_records=[_record(quantity=2)])
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[_record(quantity=3)])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.quantity_mismatches == [
        {"tag_id": "TL-1", "quantity_a": 2, "quantity_b": 3}
    ]
    assert report.matched == []


def test_condition_mismatch_is_flagged():
    ledger = ValidatedBatch(source="checkout_ledger", valid_records=[_record(condition="good")])
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[_record(condition="needs_repair")])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.condition_mismatches == [
        {"tag_id": "TL-1", "condition_a": "good", "condition_b": "needs_repair"}
    ]


def test_record_can_have_both_quantity_and_condition_mismatch():
    ledger = ValidatedBatch(
        source="checkout_ledger", valid_records=[_record(quantity=1, condition="good")]
    )
    sweep = ValidatedBatch(
        source="shelf_sweep", valid_records=[_record(quantity=2, condition="fair")]
    )

    report = ReconcilerAgent().run(ledger, sweep)

    assert len(report.quantity_mismatches) == 1
    assert len(report.condition_mismatches) == 1
    assert report.matched == []


def test_duplicate_tag_within_a_source_is_flagged():
    ledger = ValidatedBatch(
        source="checkout_ledger",
        valid_records=[_record(tag_id="TL-1"), _record(tag_id="TL-1")],
    )
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[_record(tag_id="TL-1")])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.duplicate_tags["checkout_ledger"] == ["TL-1"]


def test_report_carries_source_labels():
    ledger = ValidatedBatch(source="checkout_ledger", valid_records=[])
    sweep = ValidatedBatch(source="shelf_sweep", valid_records=[])

    report = ReconcilerAgent().run(ledger, sweep)

    assert report.source_a == "checkout_ledger"
    assert report.source_b == "shelf_sweep"
