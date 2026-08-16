"""Task specifications: the contract an agent's output is scored against.

A ``TaskSpec`` is deliberately just data -- no behavior lives here. The
checkers in :mod:`agent_eval_harness.checks` and the judges in
:mod:`agent_eval_harness.judge` read a spec and an agent's output and
produce results; the spec never scores itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    """One required-or-optional field in an agent output's structural schema.

    Attributes:
        name: Key expected in the agent's output dict.
        type: Python type the value at ``name`` must be an instance of.
        required: If True, a missing key fails the schema check. If False,
            the field is only checked when present.
    """

    name: str
    type: type
    required: bool = True


@dataclass(frozen=True)
class NumericToleranceSpec:
    """A numeric field scored by closeness to an expected value, not equality.

    A value passes if it is within ``abs_tolerance`` OR within
    ``rel_tolerance`` (as a fraction of ``expected``) of ``expected`` --
    the same "close enough" semantics as :func:`math.isclose`.
    """

    field: str
    expected: float
    abs_tolerance: float = 0.0
    rel_tolerance: float = 0.0


@dataclass(frozen=True)
class TaskSpec:
    """The full contract an agent output is scored against for one task.

    Attributes:
        task_id: Unique identifier for this task.
        description: Human-readable description of what the agent was
            asked to do (shown in scorecards, not used for scoring).
        schema: Structural fields the output dict must (or may) contain.
        exact_fields: name -> expected value; the output's value at that
            key must compare equal.
        numeric_fields: fields scored by tolerance rather than equality.
        explanation_field: name of a free-text field to hand to the judge,
            or None if this task has no free-text component to judge.
        required_keywords: substrings the judge expects to find (case
            insensitively) somewhere in the explanation text.
        forbidden_phrases: substrings that should NOT appear in the
            explanation text (e.g. refusal or non-answer boilerplate).
        strict_schema: if True, any key in the output not declared in
            ``schema`` fails the schema check. If False (default), extra
            keys are ignored.
    """

    task_id: str
    description: str
    schema: list[FieldSpec] = field(default_factory=list)
    exact_fields: dict[str, Any] = field(default_factory=dict)
    numeric_fields: list[NumericToleranceSpec] = field(default_factory=list)
    explanation_field: str | None = None
    required_keywords: list[str] = field(default_factory=list)
    forbidden_phrases: list[str] = field(default_factory=list)
    strict_schema: bool = False
