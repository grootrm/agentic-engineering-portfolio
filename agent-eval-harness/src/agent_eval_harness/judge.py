"""Pluggable judging for free-text explanation fields.

The deterministic checks in :mod:`agent_eval_harness.checks` can verify an
output's structure and its exact/numeric fields, but they have nothing to
say about a free-text explanation. A :class:`Judge` is the seam for that:
given a :class:`~agent_eval_harness.spec.TaskSpec` and an agent's output, it
returns a :class:`~agent_eval_harness.result.JudgeResult`. This module ships
one concrete, fully deterministic judge (:class:`KeywordJudge`) so the
harness runs standalone with no external calls or API keys; a later,
LLM-backed judge can implement the same :class:`Judge` protocol and drop in
without changing anything else in the harness.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agent_eval_harness.result import JudgeResult
from agent_eval_harness.spec import TaskSpec


@runtime_checkable
class Judge(Protocol):
    """Anything that can score a task's free-text explanation field."""

    def evaluate(self, spec: TaskSpec, output: dict[str, Any]) -> JudgeResult:
        """Score ``output`` against ``spec``'s free-text expectations."""
        ...


class KeywordJudge:
    """Deterministic judge: scores an explanation by keyword coverage.

    Reads ``spec.explanation_field`` out of the output and checks, case
    insensitively, that every one of ``spec.required_keywords`` appears as a
    substring and that none of ``spec.forbidden_phrases`` do. This is a
    heuristic stand-in for a real judge -- it has no notion of meaning, only
    of substring presence -- but it is exact and reproducible, which keeps
    the harness deterministic by default even when a task has a free-text
    component.
    """

    def evaluate(self, spec: TaskSpec, output: dict[str, Any]) -> JudgeResult:
        if spec.explanation_field is None:
            return JudgeResult(
                passed=True,
                score=1.0,
                rationale="task has no explanation_field to judge",
            )

        text = output.get(spec.explanation_field)
        if not isinstance(text, str):
            return JudgeResult(
                passed=False,
                score=0.0,
                rationale=(
                    f"field '{spec.explanation_field}' is missing or not a string "
                    f"(got {text!r})"
                ),
            )

        normalized = text.lower()

        found = [kw for kw in spec.required_keywords if kw.lower() in normalized]
        missing = [kw for kw in spec.required_keywords if kw.lower() not in normalized]
        hit_forbidden = [p for p in spec.forbidden_phrases if p.lower() in normalized]

        score = 1.0 if not spec.required_keywords else len(found) / len(spec.required_keywords)
        passed = score >= 1.0 and not hit_forbidden

        parts: list[str] = []
        if spec.required_keywords:
            parts.append(f"found keywords {found}" if found else "found no required keywords")
            if missing:
                parts.append(f"missing keywords {missing}")
        else:
            parts.append("no required keywords declared")
        if hit_forbidden:
            parts.append(f"forbidden phrases present: {hit_forbidden}")

        return JudgeResult(passed=passed, score=score, rationale="; ".join(parts))
