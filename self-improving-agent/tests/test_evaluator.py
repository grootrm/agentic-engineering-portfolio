"""Tests for the Evaluator: runs a candidate's source against a problem's
fixed pytest suite in an isolated temp directory and reports which tests
passed/failed.

Uses tiny fixture problems (not the real text-parsing problem) so these
tests are fast and independent of any specific domain.
"""

from self_improving_agent.evaluator import Evaluator
from self_improving_agent.problem import Problem


def _write_fixture_test_file(tmp_path):
    test_file = tmp_path / "test_fixture.py"
    test_file.write_text(
        "from solution import add_one\n"
        "\n"
        "\n"
        "def test_positive():\n"
        "    assert add_one(1) == 2\n"
        "\n"
        "\n"
        "def test_zero():\n"
        "    assert add_one(0) == 1\n"
    )
    return test_file


def _problem(tmp_path, seed_source="def add_one(x):\n    return x + 1\n"):
    return Problem(
        name="fixture",
        module_name="solution",
        function_name="add_one",
        seed_source=seed_source,
        test_file=_write_fixture_test_file(tmp_path),
    )


def _candidate(source, candidate_id="c1"):
    from self_improving_agent.candidate import Candidate

    return Candidate(id=candidate_id, source=source, strategy="seed", parent_id=None, generation=0)


def test_fully_correct_candidate_passes_all_tests(tmp_path):
    problem = _problem(tmp_path)
    evaluator = Evaluator(problem)
    candidate = _candidate("def add_one(x):\n    return x + 1\n")

    result = evaluator.evaluate(candidate)

    assert result.passed == frozenset({"test_fixture.py::test_positive", "test_fixture.py::test_zero"})
    assert result.failed == frozenset()
    assert result.all_passed is True


def test_partially_correct_candidate_reports_failures(tmp_path):
    problem = _problem(tmp_path)
    evaluator = Evaluator(problem)
    # Special-cases 0 correctly but is wrong for every other input, so
    # exactly one of the two fixture tests fails.
    candidate = _candidate("def add_one(x):\n    return 1 if x == 0 else x\n")

    result = evaluator.evaluate(candidate)

    assert result.passed == frozenset({"test_fixture.py::test_zero"})
    assert result.failed == frozenset({"test_fixture.py::test_positive"})
    assert result.all_passed is False


def test_syntactically_broken_candidate_is_reported_as_errored(tmp_path):
    problem = _problem(tmp_path)
    evaluator = Evaluator(problem)
    candidate = _candidate("def add_one(x)\n    this is not valid python\n")

    result = evaluator.evaluate(candidate)

    assert result.errored is True
    assert result.passed == frozenset()
    assert result.all_passed is False


def test_evaluation_is_isolated_between_candidates(tmp_path):
    problem = _problem(tmp_path)
    evaluator = Evaluator(problem)

    bad = evaluator.evaluate(_candidate("def add_one(x):\n    return x\n", "bad"))
    good = evaluator.evaluate(_candidate("def add_one(x):\n    return x + 1\n", "good"))

    assert bad.all_passed is False
    assert good.all_passed is True
