"""Synthetic two-source inventory data for the Millbrook Tool Library demo.

Millbrook Tool Library is an invented community tool-lending library. None
of this data represents any real organization; it exists purely to give the
extractor/validator/reconciler agents something realistic-looking to chew
on, in each source system's own dialect:

- ``checkout_ledger`` -- the front-desk checkout ledger. Abbreviated keys
  (``tag``, ``cond``, ``qty``) and single-letter condition codes
  (``g``/``f``/``r``).
- ``shelf_sweep`` -- a periodic shelf-audit sweep. Fully spelled-out keys
  (``tag_id``, ``condition``, ``quantity``) and spelled-out condition
  values.

Generation is deterministic for a given seed and deliberately engineers
every branch a reconciliation run can take: records that agree, records
with a quantity or condition disagreement, records only one source has
seen, a duplicate tag within one source, and a handful of malformed rows
per source (bad shape, not bad business data) to give the Extractor and
Validator real work to do.
"""

from __future__ import annotations

import random

TOOLS = [
    ("Cordless Drill", "power_tool"),
    ("Circular Saw", "power_tool"),
    ("Belt Sander", "power_tool"),
    ("Claw Hammer", "hand_tool"),
    ("Adjustable Wrench Set", "hand_tool"),
    ("Socket Wrench Set", "hand_tool"),
    ("Extension Ladder", "ladder"),
    ("Step Stool Ladder", "ladder"),
    ("Gas Hedge Trimmer", "yard_equipment"),
    ("Push Mower", "yard_equipment"),
    ("Wheelbarrow", "other"),
    ("Shop Vacuum", "other"),
]

LOCATION_BINS = ["A1", "A2", "A3", "B1", "B2", "C1", "C2", "D1"]

_LEDGER_CONDITION_CODES = {"good": "g", "fair": "f", "needs_repair": "r"}


def _tag_id(index: int) -> str:
    return f"TL-{index:05d}"


def _base_record(rng: random.Random, index: int) -> dict:
    tool_name, category = TOOLS[index % len(TOOLS)]
    return {
        "tag_id": _tag_id(index),
        "tool_name": tool_name,
        "category": category,
        "condition": rng.choice(["good", "fair", "needs_repair"]),
        "quantity": rng.randint(1, 4),
        "location_bin": rng.choice(LOCATION_BINS),
    }


def _to_ledger_row(record: dict) -> dict:
    return {
        "tag": record["tag_id"],
        "name": record["tool_name"],
        "cat": record["category"],
        "cond": _LEDGER_CONDITION_CODES[record["condition"]],
        "qty": record["quantity"],
        "bin": record["location_bin"],
    }


def _to_sweep_row(record: dict) -> dict:
    return {
        "tag_id": record["tag_id"],
        "tool_name": record["tool_name"],
        "category": record["category"],
        "condition": record["condition"],
        "quantity": record["quantity"],
        "location_bin": record["location_bin"],
    }


def _malformed_ledger_rows(rng: random.Random, count: int, start_index: int) -> list[dict]:
    defects = [
        "missing_tag",
        "bad_quantity",
        "malformed_tag_id",
        "missing_name",
        "missing_bin",
    ]
    rows = []
    for i in range(count):
        record = _base_record(rng, start_index + i)
        row = _to_ledger_row(record)
        defect = defects[i % len(defects)]
        if defect == "missing_tag":
            row.pop("tag")
        elif defect == "bad_quantity":
            row["qty"] = "several"
        elif defect == "malformed_tag_id":
            row["tag"] = record["tag_id"].replace("TL-", "TOOL")
        elif defect == "missing_name":
            row["name"] = ""
        elif defect == "missing_bin":
            row["bin"] = ""
        rows.append(row)
    return rows


def _malformed_sweep_rows(rng: random.Random, count: int, start_index: int) -> list[dict]:
    defects = [
        "unknown_category",
        "unknown_condition",
        "non_positive_quantity",
        "missing_bin",
        "missing_name",
    ]
    rows = []
    for i in range(count):
        record = _base_record(rng, start_index + i)
        row = _to_sweep_row(record)
        defect = defects[i % len(defects)]
        if defect == "unknown_category":
            row["category"] = "vehicle"
        elif defect == "unknown_condition":
            row["condition"] = "pristine"
        elif defect == "non_positive_quantity":
            row["quantity"] = 0
        elif defect == "missing_bin":
            row["location_bin"] = ""
        elif defect == "missing_name":
            row["tool_name"] = ""
        rows.append(row)
    return rows


def generate_inventory_sources(
    seed: int, record_count: int, malformed_per_source: int = 4
) -> tuple[list[dict], list[dict]]:
    """Generate raw ledger and sweep rows, deterministic for a given seed.

    ``record_count`` "true" tools are generated and then, index by index,
    deterministically routed into one of five reconciliation scenarios so
    every branch of the pipeline is exercised on every run:

        0: matched            -- identical in both sources
        1: quantity mismatch  -- differs only in quantity
        2: condition mismatch -- differs only in condition
        3: missing in ledger  -- only the sweep saw it
        4: missing in sweep   -- only the ledger saw it

    On top of that, the first true record is duplicated a second time in
    the ledger (to exercise duplicate-tag handling), and each source gets
    ``malformed_per_source`` additional shape-broken rows appended.

    Returns:
        ``(ledger_rows, sweep_rows)`` -- raw dicts in each source's own
        dialect, ready for :class:`~reconciliation_agents.messages.RawRecordBatch`.
    """
    rng = random.Random(seed)

    ledger_rows: list[dict] = []
    sweep_rows: list[dict] = []

    for index in range(record_count):
        record = _base_record(rng, index)
        scenario = index % 5

        if scenario == 0:
            ledger_rows.append(_to_ledger_row(record))
            sweep_rows.append(_to_sweep_row(record))
        elif scenario == 1:
            ledger_rows.append(_to_ledger_row(record))
            mismatched = {**record, "quantity": record["quantity"] + rng.randint(1, 3)}
            sweep_rows.append(_to_sweep_row(mismatched))
        elif scenario == 2:
            other_condition = next(
                c for c in ("good", "fair", "needs_repair") if c != record["condition"]
            )
            ledger_rows.append(_to_ledger_row(record))
            mismatched = {**record, "condition": other_condition}
            sweep_rows.append(_to_sweep_row(mismatched))
        elif scenario == 3:
            sweep_rows.append(_to_sweep_row(record))
        elif scenario == 4:
            ledger_rows.append(_to_ledger_row(record))

        if index == 0:
            # Exercise duplicate-tag handling within a single source.
            ledger_rows.append(_to_ledger_row(record))

    ledger_rows.extend(_malformed_ledger_rows(rng, malformed_per_source, record_count))
    sweep_rows.extend(_malformed_sweep_rows(rng, malformed_per_source, record_count + malformed_per_source))

    return ledger_rows, sweep_rows
