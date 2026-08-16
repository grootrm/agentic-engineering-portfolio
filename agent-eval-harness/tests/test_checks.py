"""Tests for the deterministic, rule-based checkers.

No external calls, no API keys -- every check here is pure Python
comparing an agent's output dict against a TaskSpec.
"""

from agent_eval_harness.checks import (
    check_exact_fields,
    check_numeric_tolerance,
    check_schema,
    run_deterministic_checks,
)
from agent_eval_harness.spec import FieldSpec, NumericToleranceSpec, TaskSpec


# ---------------------------------------------------------------------------
# check_schema
# ---------------------------------------------------------------------------


def test_schema_check_passes_when_all_required_fields_present_with_correct_types():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        schema=[FieldSpec(name="order_id", type=str), FieldSpec(name="total", type=float)],
    )
    output = {"order_id": "ORD-1", "total": 42.5}

    result = check_schema(spec, output)

    assert result.passed is True


def test_schema_check_fails_when_required_field_missing():
    spec = TaskSpec(task_id="t1", description="d", schema=[FieldSpec(name="order_id", type=str)])
    output = {}

    result = check_schema(spec, output)

    assert result.passed is False
    assert "order_id" in result.detail


def test_schema_check_fails_when_field_has_wrong_type():
    spec = TaskSpec(task_id="t1", description="d", schema=[FieldSpec(name="total", type=float)])
    output = {"total": "42.5"}

    result = check_schema(spec, output)

    assert result.passed is False
    assert "total" in result.detail


def test_schema_check_passes_when_optional_field_is_missing():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        schema=[FieldSpec(name="note", type=str, required=False)],
    )
    output = {}

    result = check_schema(spec, output)

    assert result.passed is True


def test_schema_check_checks_optional_field_type_when_present():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        schema=[FieldSpec(name="note", type=str, required=False)],
    )
    output = {"note": 123}

    result = check_schema(spec, output)

    assert result.passed is False


def test_schema_check_ignores_extra_fields_when_not_strict():
    spec = TaskSpec(task_id="t1", description="d", schema=[FieldSpec(name="order_id", type=str)])
    output = {"order_id": "ORD-1", "unexpected": "surprise"}

    result = check_schema(spec, output)

    assert result.passed is True


def test_schema_check_fails_on_extra_fields_when_strict():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        schema=[FieldSpec(name="order_id", type=str)],
        strict_schema=True,
    )
    output = {"order_id": "ORD-1", "unexpected": "surprise"}

    result = check_schema(spec, output)

    assert result.passed is False
    assert "unexpected" in result.detail


def test_schema_check_passes_trivially_when_spec_has_no_schema():
    spec = TaskSpec(task_id="t1", description="d")
    output = {"anything": "goes"}

    result = check_schema(spec, output)

    assert result.passed is True


# ---------------------------------------------------------------------------
# check_exact_fields
# ---------------------------------------------------------------------------


def test_exact_fields_check_returns_one_passing_result_per_field():
    spec = TaskSpec(task_id="t1", description="d", exact_fields={"status": "delivered"})
    output = {"status": "delivered"}

    results = check_exact_fields(spec, output)

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].name == "exact_match:status"


def test_exact_fields_check_fails_on_mismatched_value():
    spec = TaskSpec(task_id="t1", description="d", exact_fields={"status": "delivered"})
    output = {"status": "shipped"}

    results = check_exact_fields(spec, output)

    assert results[0].passed is False
    assert "delivered" in results[0].detail
    assert "shipped" in results[0].detail


def test_exact_fields_check_fails_when_field_missing_from_output():
    spec = TaskSpec(task_id="t1", description="d", exact_fields={"status": "delivered"})
    output = {}

    results = check_exact_fields(spec, output)

    assert results[0].passed is False


def test_exact_fields_check_returns_empty_list_when_no_exact_fields_declared():
    spec = TaskSpec(task_id="t1", description="d")
    output = {"status": "delivered"}

    results = check_exact_fields(spec, output)

    assert results == []


def test_exact_fields_check_covers_multiple_fields_independently():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        exact_fields={"status": "delivered", "carrier": "synth-post"},
    )
    output = {"status": "delivered", "carrier": "wrong-carrier"}

    results = check_exact_fields(spec, output)

    by_name = {r.name: r for r in results}
    assert by_name["exact_match:status"].passed is True
    assert by_name["exact_match:carrier"].passed is False


# ---------------------------------------------------------------------------
# check_numeric_tolerance
# ---------------------------------------------------------------------------


def test_numeric_tolerance_check_passes_on_exact_match():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        numeric_fields=[NumericToleranceSpec(field="total", expected=100.0)],
    )
    output = {"total": 100.0}

    results = check_numeric_tolerance(spec, output)

    assert results[0].passed is True


def test_numeric_tolerance_check_passes_within_absolute_tolerance():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        numeric_fields=[
            NumericToleranceSpec(field="total", expected=100.0, abs_tolerance=0.5)
        ],
    )
    output = {"total": 100.4}

    results = check_numeric_tolerance(spec, output)

    assert results[0].passed is True


def test_numeric_tolerance_check_fails_outside_absolute_tolerance():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        numeric_fields=[
            NumericToleranceSpec(field="total", expected=100.0, abs_tolerance=0.5)
        ],
    )
    output = {"total": 101.0}

    results = check_numeric_tolerance(spec, output)

    assert results[0].passed is False
    assert "100.0" in results[0].detail
    assert "101.0" in results[0].detail


def test_numeric_tolerance_check_passes_within_relative_tolerance():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        numeric_fields=[
            NumericToleranceSpec(field="total", expected=1000.0, rel_tolerance=0.05)
        ],
    )
    output = {"total": 1040.0}  # 4% off, within 5%

    results = check_numeric_tolerance(spec, output)

    assert results[0].passed is True


def test_numeric_tolerance_check_fails_when_field_missing():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        numeric_fields=[NumericToleranceSpec(field="total", expected=100.0)],
    )
    output = {}

    results = check_numeric_tolerance(spec, output)

    assert results[0].passed is False


def test_numeric_tolerance_check_fails_when_field_not_numeric():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        numeric_fields=[NumericToleranceSpec(field="total", expected=100.0)],
    )
    output = {"total": "not-a-number"}

    results = check_numeric_tolerance(spec, output)

    assert results[0].passed is False


# ---------------------------------------------------------------------------
# run_deterministic_checks
# ---------------------------------------------------------------------------


def test_run_deterministic_checks_combines_schema_exact_and_numeric_results():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        schema=[FieldSpec(name="order_id", type=str)],
        exact_fields={"status": "delivered"},
        numeric_fields=[NumericToleranceSpec(field="total", expected=100.0)],
    )
    output = {"order_id": "ORD-1", "status": "delivered", "total": 100.0}

    results = run_deterministic_checks(spec, output)

    names = {r.name for r in results}
    assert "schema" in names
    assert "exact_match:status" in names
    assert "numeric_tolerance:total" in names
    assert all(r.passed for r in results)


def test_run_deterministic_checks_reports_every_failure_not_just_the_first():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        schema=[FieldSpec(name="order_id", type=str)],
        exact_fields={"status": "delivered"},
        numeric_fields=[NumericToleranceSpec(field="total", expected=100.0)],
    )
    output = {"status": "shipped", "total": 5.0}  # missing order_id too

    results = run_deterministic_checks(spec, output)

    assert sum(1 for r in results if not r.passed) == 3
