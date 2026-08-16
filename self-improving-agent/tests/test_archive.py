"""Tests for the lineage-tracking archive.

An archive holds only candidates that are worth keeping: the initial
seed, plus any later candidate that passes a strict superset of the
tests its parent passed. Everything else is evaluated but discarded.
"""

from self_improving_agent.archive import Archive
from self_improving_agent.candidate import Candidate
from self_improving_agent.evaluator import EvaluationResult


def _seed():
    return Candidate(
        id="seed",
        source="def solve(x): return x",
        strategy="seed",
        parent_id=None,
        generation=0,
    )


def _child(parent_id, strategy="mutation", generation=1):
    return Candidate(
        id=strategy,
        source="def solve(x): return x",
        strategy=strategy,
        parent_id=parent_id,
        generation=generation,
    )


def test_seed_candidate_is_always_kept():
    archive = Archive()
    seed = _seed()
    result = EvaluationResult(passed=frozenset({"test_a"}), failed=frozenset({"test_b"}))

    entry = archive.try_add(seed, result)

    assert entry is not None
    assert len(archive) == 1
    assert archive.get("seed").candidate is seed


def test_child_passing_strict_superset_of_parent_is_kept():
    archive = Archive()
    seed = _seed()
    archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b", "c"})))

    child = _child("seed")
    result = EvaluationResult(passed=frozenset({"a", "b"}), failed=frozenset({"c"}))
    entry = archive.try_add(child, result)

    assert entry is not None
    assert len(archive) == 2
    assert entry.passed_tests == frozenset({"a", "b"})


def test_child_that_regresses_is_rejected():
    archive = Archive()
    seed = _seed()
    archive.try_add(seed, EvaluationResult(passed=frozenset({"a", "b"}), failed=frozenset({"c"})))

    child = _child("seed")
    # Loses "b" relative to parent -- not a superset.
    result = EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b", "c"}))
    entry = archive.try_add(child, result)

    assert entry is None
    assert len(archive) == 1


def test_child_identical_to_parent_is_rejected():
    archive = Archive()
    seed = _seed()
    archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b"})))

    child = _child("seed")
    result = EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b"}))
    entry = archive.try_add(child, result)

    assert entry is None
    assert len(archive) == 1


def test_kept_reason_names_the_newly_passing_tests():
    archive = Archive()
    seed = _seed()
    archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b", "c"})))

    child = _child("seed")
    result = EvaluationResult(passed=frozenset({"a", "b"}), failed=frozenset({"c"}))
    entry = archive.try_add(child, result)

    assert "b" in entry.kept_reason


def test_seed_kept_reason_reports_pass_count():
    archive = Archive()
    seed = _seed()
    entry = archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b", "c"})))

    assert "1" in entry.kept_reason
    assert "3" in entry.kept_reason  # total test count


def test_best_returns_entry_with_most_passed_tests():
    archive = Archive()
    seed = _seed()
    archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b", "c"})))
    child = _child("seed")
    archive.try_add(child, EvaluationResult(passed=frozenset({"a", "b"}), failed=frozenset({"c"})))

    assert archive.best().candidate.id == "mutation"


def test_lineage_returns_chain_from_root_to_entry():
    archive = Archive()
    seed = _seed()
    archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b", "c"})))
    child = _child("seed", strategy="gen1")
    archive.try_add(child, EvaluationResult(passed=frozenset({"a", "b"}), failed=frozenset({"c"})))
    grandchild = _child("gen1", strategy="gen2", generation=2)
    archive.try_add(grandchild, EvaluationResult(passed=frozenset({"a", "b", "c"}), failed=frozenset()))

    chain = archive.lineage("gen2")

    assert [entry.candidate.id for entry in chain] == ["seed", "gen1", "gen2"]


def test_fully_passing_entry_reports_all_passed():
    archive = Archive()
    seed = _seed()
    entry = archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset()))

    assert entry.all_passed is True


def test_partially_passing_entry_reports_not_all_passed():
    archive = Archive()
    seed = _seed()
    entry = archive.try_add(seed, EvaluationResult(passed=frozenset({"a"}), failed=frozenset({"b"})))

    assert entry.all_passed is False
