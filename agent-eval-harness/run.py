#!/usr/bin/env python
"""Demo runner: scores the synthetic benchmark scenarios and prints a scorecard.

    python run.py

Exits 0 if every sample output passed, 1 otherwise (so it can be dropped
into a CI job the same way a real eval run would be).
"""

from __future__ import annotations

import sys

from agent_eval_harness.checks import run_deterministic_checks
from agent_eval_harness.judge import KeywordJudge
from agent_eval_harness.result import ScoreResult
from benchmarks import SCENARIOS

_judge = KeywordJudge()


def score_sample(spec, output) -> ScoreResult:
    checks = run_deterministic_checks(spec, output)
    judge_result = _judge.evaluate(spec, output) if spec.explanation_field else None
    return ScoreResult(task_id=spec.task_id, checks=checks, judge=judge_result)


def main() -> int:
    total = 0
    passed_count = 0
    scores: list[float] = []

    for scenario in SCENARIOS:
        print(f"== {scenario.spec.task_id} ==")
        print(f"   {scenario.spec.description}")

        for sample in scenario.samples:
            total += 1
            result = score_sample(scenario.spec, sample.output)
            scores.append(result.score)
            status = "PASS" if result.passed else "FAIL"
            if result.passed:
                passed_count += 1

            print(f"  [{status}] {sample.label}  score={result.score:.2f}")

            failing_checks = [c.name for c in result.checks if not c.passed]
            if failing_checks:
                print(f"        failing checks: {', '.join(failing_checks)}")
            if result.judge is not None:
                judge_status = "judge OK" if result.judge.passed else "judge FAILED"
                print(f"        {judge_status}: {result.judge.rationale}")
        print()

    mean_score = sum(scores) / len(scores) if scores else 0.0
    print(f"Summary: {passed_count}/{total} outputs passed, mean score {mean_score:.2f}")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
