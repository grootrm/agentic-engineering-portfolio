"""Tests for the pluggable judge interface and the default KeywordJudge.

Like the deterministic checks, KeywordJudge is pure Python with no
external calls -- these tests exercise it the same way test_checks.py
exercises the schema/exact/numeric checkers.
"""

from agent_eval_harness.judge import Judge, KeywordJudge
from agent_eval_harness.spec import TaskSpec


def test_keyword_judge_satisfies_judge_protocol():
    assert isinstance(KeywordJudge(), Judge)


def test_keyword_judge_passes_when_all_required_keywords_present():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        explanation_field="explanation",
        required_keywords=["refund", "processed"],
    )
    output = {"explanation": "The refund has been processed successfully."}

    result = KeywordJudge().evaluate(spec, output)

    assert result.passed is True
    assert result.score == 1.0


def test_keyword_judge_scores_partial_credit_for_some_missing_keywords():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        explanation_field="explanation",
        required_keywords=["refund", "processed", "confirmation"],
    )
    output = {"explanation": "The refund has been processed."}

    result = KeywordJudge().evaluate(spec, output)

    assert result.passed is False
    assert result.score == 2 / 3
    assert "confirmation" in result.rationale


def test_keyword_judge_is_case_insensitive():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        explanation_field="explanation",
        required_keywords=["REFUND"],
    )
    output = {"explanation": "your refund is on its way"}

    result = KeywordJudge().evaluate(spec, output)

    assert result.passed is True
    assert result.score == 1.0


def test_keyword_judge_fails_when_forbidden_phrase_present_even_with_all_keywords():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        explanation_field="explanation",
        required_keywords=["refund"],
        forbidden_phrases=["not our problem"],
    )
    output = {"explanation": "Your refund is not our problem to solve."}

    result = KeywordJudge().evaluate(spec, output)

    assert result.passed is False
    assert "not our problem" in result.rationale


def test_keyword_judge_passes_trivially_when_no_explanation_field_declared():
    spec = TaskSpec(task_id="t1", description="d")

    result = KeywordJudge().evaluate(spec, {"anything": "goes"})

    assert result.passed is True
    assert result.score == 1.0


def test_keyword_judge_fails_when_explanation_field_missing_from_output():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        explanation_field="explanation",
        required_keywords=["refund"],
    )

    result = KeywordJudge().evaluate(spec, {})

    assert result.passed is False
    assert result.score == 0.0


def test_keyword_judge_fails_when_explanation_field_is_not_a_string():
    spec = TaskSpec(
        task_id="t1",
        description="d",
        explanation_field="explanation",
        required_keywords=["refund"],
    )

    result = KeywordJudge().evaluate(spec, {"explanation": 12345})

    assert result.passed is False
    assert result.score == 0.0


def test_keyword_judge_passes_with_empty_required_keywords_and_no_forbidden_hits():
    spec = TaskSpec(task_id="t1", description="d", explanation_field="explanation")
    output = {"explanation": "Whatever the agent felt like saying."}

    result = KeywordJudge().evaluate(spec, output)

    assert result.passed is True
    assert result.score == 1.0
