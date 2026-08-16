"""Result types produced by deterministic checks, judges, and the scorer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CheckResult:
    """Outcome of a single deterministic check (schema, exact-match, ...)."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class JudgeResult:
    """Outcome of a :class:`agent_eval_harness.judge.Judge` evaluation."""

    passed: bool
    score: float
    rationale: str = ""


@dataclass
class ScoreResult:
    """Full scoring outcome for one task: deterministic checks + judge.

    ``score`` is in [0, 1]:
      - with both checks and a judge, it's the even average of the
        fraction of checks that passed and the judge's own score;
      - with only checks (no judge), it's just the fraction that passed;
      - with no checks at all, the check half is treated as 1.0 (nothing
        to fail), so a task with neither checks nor a judge scores 1.0.
    """

    task_id: str
    checks: list[CheckResult] = field(default_factory=list)
    judge: JudgeResult | None = None

    @property
    def passed(self) -> bool:
        checks_passed = all(check.passed for check in self.checks)
        judge_passed = self.judge is None or self.judge.passed
        return checks_passed and judge_passed

    @property
    def score(self) -> float:
        if self.checks:
            checks_score = sum(1 for c in self.checks if c.passed) / len(self.checks)
        else:
            checks_score = 1.0

        if self.judge is None:
            return checks_score

        return (checks_score + self.judge.score) / 2
