"""Tests for the result types produced by checks, judges, and the scorer."""

from agent_eval_harness.result import CheckResult, JudgeResult, ScoreResult


def test_check_result_holds_name_pass_flag_and_detail():
    result = CheckResult(name="schema", passed=True, detail="ok")

    assert result.name == "schema"
    assert result.passed is True
    assert result.detail == "ok"


def test_check_result_detail_defaults_to_empty_string():
    result = CheckResult(name="schema", passed=True)

    assert result.detail == ""


def test_judge_result_holds_score_pass_flag_and_rationale():
    result = JudgeResult(passed=True, score=0.9, rationale="covers all keywords")

    assert result.passed is True
    assert result.score == 0.9
    assert result.rationale == "covers all keywords"


def test_score_result_passed_is_true_when_all_checks_and_judge_pass():
    checks = [CheckResult(name="schema", passed=True), CheckResult(name="exact:x", passed=True)]
    judge = JudgeResult(passed=True, score=1.0, rationale="fine")

    result = ScoreResult(task_id="t1", checks=checks, judge=judge)

    assert result.passed is True


def test_score_result_passed_is_false_when_any_check_fails():
    checks = [CheckResult(name="schema", passed=True), CheckResult(name="exact:x", passed=False)]

    result = ScoreResult(task_id="t1", checks=checks, judge=None)

    assert result.passed is False


def test_score_result_passed_is_false_when_judge_fails_even_if_checks_pass():
    checks = [CheckResult(name="schema", passed=True)]
    judge = JudgeResult(passed=False, score=0.2, rationale="missing keywords")

    result = ScoreResult(task_id="t1", checks=checks, judge=judge)

    assert result.passed is False


def test_score_result_passed_true_with_no_checks_and_no_judge():
    result = ScoreResult(task_id="t1", checks=[], judge=None)

    assert result.passed is True


def test_score_result_score_is_fraction_of_checks_passed_when_no_judge():
    checks = [
        CheckResult(name="a", passed=True),
        CheckResult(name="b", passed=True),
        CheckResult(name="c", passed=False),
        CheckResult(name="d", passed=True),
    ]

    result = ScoreResult(task_id="t1", checks=checks, judge=None)

    assert result.score == 0.75


def test_score_result_score_blends_checks_and_judge_score_evenly():
    checks = [CheckResult(name="a", passed=True), CheckResult(name="b", passed=False)]
    judge = JudgeResult(passed=True, score=1.0, rationale="fine")

    result = ScoreResult(task_id="t1", checks=checks, judge=judge)

    # deterministic checks: 0.5, judge: 1.0 -> averaged 0.75
    assert result.score == 0.75


def test_score_result_score_is_one_when_no_checks_and_no_judge():
    result = ScoreResult(task_id="t1", checks=[], judge=None)

    assert result.score == 1.0
