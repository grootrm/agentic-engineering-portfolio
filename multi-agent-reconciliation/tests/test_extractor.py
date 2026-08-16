"""Tests for the Extractor agent: raw rows -> canonical Records.

The two source systems in the demo domain (a checkout ledger and a
shelf-audit sweep) speak different field-name dialects for the same
underlying tool. The Extractor's job is to normalize both into the same
canonical shape without knowing in advance which dialect it's looking at.
"""

from reconciliation_agents.extractor import ExtractorAgent
from reconciliation_agents.messages import RawRecordBatch
from reconciliation_agents.records import Record


def test_extracts_ledger_style_row_into_canonical_record():
    batch = RawRecordBatch(
        source="checkout_ledger",
        rows=[
            {
                "tag": "TL-04231",
                "name": "Cordless Drill",
                "cat": "power_tool",
                "cond": "G",
                "qty": "1",
                "bin": "A3",
            }
        ],
    )

    result = ExtractorAgent().run(batch)

    assert result.source == "checkout_ledger"
    assert result.extraction_errors == []
    assert result.records == [
        Record(
            tag_id="TL-04231",
            tool_name="Cordless Drill",
            category="power_tool",
            condition="good",
            quantity=1,
            location_bin="A3",
        )
    ]


def test_extracts_sweep_style_row_into_canonical_record():
    batch = RawRecordBatch(
        source="shelf_sweep",
        rows=[
            {
                "tag_id": "TL-04231",
                "tool_name": "Cordless Drill",
                "category": "power_tool",
                "condition": "good",
                "quantity": 1,
                "location_bin": "A3",
            }
        ],
    )

    result = ExtractorAgent().run(batch)

    assert result.records == [
        Record(
            tag_id="TL-04231",
            tool_name="Cordless Drill",
            category="power_tool",
            condition="good",
            quantity=1,
            location_bin="A3",
        )
    ]


def test_expands_abbreviated_condition_codes():
    batch = RawRecordBatch(
        source="checkout_ledger",
        rows=[
            {"tag": "TL-1", "name": "Hammer", "cat": "hand_tool", "cond": "F", "qty": "1", "bin": "B1"},
            {"tag": "TL-2", "name": "Ladder", "cat": "ladder", "cond": "R", "qty": "1", "bin": "C1"},
        ],
    )

    result = ExtractorAgent().run(batch)

    assert [r.condition for r in result.records] == ["fair", "needs_repair"]


def test_defaults_missing_quantity_to_one():
    batch = RawRecordBatch(
        source="shelf_sweep",
        rows=[
            {
                "tag_id": "TL-9",
                "tool_name": "Rake",
                "category": "yard_equipment",
                "condition": "good",
                "location_bin": "D2",
            }
        ],
    )

    result = ExtractorAgent().run(batch)

    assert result.records[0].quantity == 1


def test_row_missing_tag_identifier_becomes_extraction_error():
    batch = RawRecordBatch(
        source="checkout_ledger",
        rows=[{"name": "Mystery Tool", "cat": "other", "cond": "G", "qty": "1", "bin": "A1"}],
    )

    result = ExtractorAgent().run(batch)

    assert result.records == []
    assert len(result.extraction_errors) == 1
    assert "tag" in result.extraction_errors[0].reason.lower()


def test_non_numeric_quantity_becomes_extraction_error():
    batch = RawRecordBatch(
        source="checkout_ledger",
        rows=[
            {
                "tag": "TL-5",
                "name": "Wheelbarrow",
                "cat": "yard_equipment",
                "cond": "G",
                "qty": "several",
                "bin": "E4",
            }
        ],
    )

    result = ExtractorAgent().run(batch)

    assert result.records == []
    assert len(result.extraction_errors) == 1
    assert "quantity" in result.extraction_errors[0].reason.lower()


def test_batch_keeps_valid_records_and_errors_from_mixed_rows_separate():
    batch = RawRecordBatch(
        source="checkout_ledger",
        rows=[
            {"tag": "TL-1", "name": "Hammer", "cat": "hand_tool", "cond": "G", "qty": "1", "bin": "A1"},
            {"name": "No Tag Row", "cat": "other", "cond": "G", "qty": "1", "bin": "A1"},
        ],
    )

    result = ExtractorAgent().run(batch)

    assert len(result.records) == 1
    assert len(result.extraction_errors) == 1
    assert result.extraction_errors[0].raw_row == batch.rows[1]
