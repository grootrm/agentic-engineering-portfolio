"""Deterministic, rule-based scorers.

Every function here is pure: given a :class:`~agent_eval_harness.spec.TaskSpec`
and an agent output dict, it returns one or more
:class:`~agent_eval_harness.result.CheckResult` values. No network calls, no
randomness, no API keys -- the same output always scores the same way.
"""

from __future__ import annotations

import math
from typing import Any

from agent_eval_harness.result import CheckResult
from agent_eval_harness.spec import TaskSpec

_MISSING = object()


def check_schema(spec: TaskSpec, output: dict[str, Any]) -> CheckResult:
    """Validate output structure: required fields present, values well-typed.

    Passes trivially if ``spec.schema`` is empty. If ``spec.strict_schema``
    is True, any key in ``output`` not declared in the schema also fails
    the check.
    """
    problems: list[str] = []
    declared_names = {field.name for field in spec.schema}

    for field in spec.schema:
        value = output.get(field.name, _MISSING)
        if value is _MISSING:
            if field.required:
                problems.append(f"missing required field '{field.name}'")
            continue
        if not isinstance(value, field.type):
            problems.append(
                f"field '{field.name}' expected type {field.type.__name__}, "
                f"got {type(value).__name__}"
            )

    if spec.strict_schema:
        extra = set(output) - declared_names
        for name in sorted(extra):
            problems.append(f"unexpected field '{name}'")

    return CheckResult(name="schema", passed=not problems, detail="; ".join(problems))


def check_exact_fields(spec: TaskSpec, output: dict[str, Any]) -> list[CheckResult]:
    """Compare each of ``spec.exact_fields`` against the matching output value."""
    results: list[CheckResult] = []

    for field_name, expected in spec.exact_fields.items():
        actual = output.get(field_name, _MISSING)
        if actual is _MISSING:
            results.append(
                CheckResult(
                    name=f"exact_match:{field_name}",
                    passed=False,
                    detail=f"field '{field_name}' missing from output",
                )
            )
            continue

        passed = actual == expected
        detail = "" if passed else f"expected {expected!r}, got {actual!r}"
        results.append(CheckResult(name=f"exact_match:{field_name}", passed=passed, detail=detail))

    return results


def check_numeric_tolerance(spec: TaskSpec, output: dict[str, Any]) -> list[CheckResult]:
    """Compare each of ``spec.numeric_fields`` within its declared tolerance."""
    results: list[CheckResult] = []

    for tol in spec.numeric_fields:
        actual = output.get(tol.field, _MISSING)
        name = f"numeric_tolerance:{tol.field}"

        if actual is _MISSING:
            results.append(
                CheckResult(name=name, passed=False, detail=f"field '{tol.field}' missing from output")
            )
            continue

        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            results.append(
                CheckResult(
                    name=name,
                    passed=False,
                    detail=f"field '{tol.field}' is not numeric (got {actual!r})",
                )
            )
            continue

        passed = math.isclose(
            actual, tol.expected, rel_tol=tol.rel_tolerance, abs_tol=tol.abs_tolerance
        )
        detail = "" if passed else f"expected {tol.expected} (+/- tolerance), got {actual}"
        results.append(CheckResult(name=name, passed=passed, detail=detail))

    return results


def run_deterministic_checks(spec: TaskSpec, output: dict[str, Any]) -> list[CheckResult]:
    """Run every deterministic check declared on ``spec`` and combine the results."""
    return [
        check_schema(spec, output),
        *check_exact_fields(spec, output),
        *check_numeric_tolerance(spec, output),
    ]
