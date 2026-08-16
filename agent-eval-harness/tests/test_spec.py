"""Tests for the TaskSpec contract objects."""

import dataclasses

import pytest

from agent_eval_harness.spec import FieldSpec, NumericToleranceSpec, TaskSpec


def test_task_spec_defaults_are_empty_and_non_strict():
    spec = TaskSpec(task_id="t1", description="a task")

    assert spec.schema == []
    assert spec.exact_fields == {}
    assert spec.numeric_fields == []
    assert spec.required_keywords == []
    assert spec.forbidden_phrases == []
    assert spec.explanation_field is None
    assert spec.strict_schema is False


def test_field_spec_holds_name_type_and_required_flag():
    field = FieldSpec(name="total", type=float, required=True)

    assert field.name == "total"
    assert field.type is float
    assert field.required is True


def test_field_spec_required_defaults_to_true():
    field = FieldSpec(name="total", type=float)

    assert field.required is True


def test_numeric_tolerance_spec_holds_expected_value_and_tolerances():
    tol = NumericToleranceSpec(
        field="total", expected=100.0, abs_tolerance=0.5, rel_tolerance=0.0
    )

    assert tol.field == "total"
    assert tol.expected == 100.0
    assert tol.abs_tolerance == 0.5
    assert tol.rel_tolerance == 0.0


def test_task_spec_is_immutable():
    spec = TaskSpec(task_id="t1", description="a task")

    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.task_id = "t2"
