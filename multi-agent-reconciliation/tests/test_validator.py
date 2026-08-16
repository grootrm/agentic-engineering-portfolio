"""Tests for the Validator agent: business-rule checks on extracted Records.

The Validator never silently drops a bad record -- it routes every record
into either ``valid_records`` or ``invalid_records`` (with reasons), so a
data-quality problem is visible in the report rather than swallowed.
"""

from reconciliation_agents.messages import ExtractedBatch
from reconciliation_agents.records import Record
from reconciliation_agents.validator import ValidatorAgent


def _record(**overrides) -> Record:
    defaults = dict(
        tag_id="TL-04231",
        tool_name="Cordless Drill",
        category="power_tool",
        condition="good",
        quantity=1,
        location_bin="A3",
    )
    defaults.update(overrides)
    return Record(**defaults)


def test_valid_record_passes_through_unchanged():
    batch = ExtractedBatch(source="checkout_ledger", records=[_record()])

    result = ValidatorAgent().run(batch)

    assert result.valid_records == [_record()]
    assert result.invalid_records == []


def test_malformed_tag_id_is_flagged():
    batch = ExtractedBatch(source="checkout_ledger", records=[_record(tag_id="not-a-tag")])

    result = ValidatorAgent().run(batch)

    assert result.valid_records == []
    assert len(result.invalid_records) == 1
    assert any("tag_id" in reason for reason in result.invalid_records[0].reasons)


def test_unknown_category_is_flagged():
    batch = ExtractedBatch(source="checkout_ledger", records=[_record(category="spaceship_part")])

    result = ValidatorAgent().run(batch)

    assert any("category" in reason for reason in result.invalid_records[0].reasons)


def test_unknown_condition_is_flagged():
    batch = ExtractedBatch(source="checkout_ledger", records=[_record(condition="pristine")])

    result = ValidatorAgent().run(batch)

    assert any("condition" in reason for reason in result.invalid_records[0].reasons)


def test_non_positive_quantity_is_flagged():
    batch = ExtractedBatch(source="checkout_ledger", records=[_record(quantity=0)])

    result = ValidatorAgent().run(batch)

    assert any("quantity" in reason for reason in result.invalid_records[0].reasons)


def test_missing_location_bin_is_flagged():
    batch = ExtractedBatch(source="checkout_ledger", records=[_record(location_bin="")])

    result = ValidatorAgent().run(batch)

    assert any("location_bin" in reason for reason in result.invalid_records[0].reasons)


def test_record_can_have_multiple_violations_flagged_at_once():
    batch = ExtractedBatch(
        source="checkout_ledger",
        records=[_record(category="spaceship_part", quantity=-1)],
    )

    result = ValidatorAgent().run(batch)

    reasons = result.invalid_records[0].reasons
    assert len(reasons) == 2
    assert any("category" in r for r in reasons)
    assert any("quantity" in r for r in reasons)


def test_batch_separates_valid_from_invalid_records_and_preserves_source():
    batch = ExtractedBatch(
        source="checkout_ledger",
        records=[_record(tag_id="TL-1"), _record(tag_id="TL-2", condition="pristine")],
    )

    result = ValidatorAgent().run(batch)

    assert result.source == "checkout_ledger"
    assert [r.tag_id for r in result.valid_records] == ["TL-1"]
    assert [ir.record.tag_id for ir in result.invalid_records] == ["TL-2"]
