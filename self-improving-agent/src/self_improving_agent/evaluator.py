"""Scores a candidate by running it against a problem's fixed pytest suite."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from self_improving_agent.candidate import Candidate
from self_improving_agent.problem import Problem

_OUTCOME_LINE = re.compile(r"^(?P<nodeid>\S+::\S+)\s+(?P<outcome>PASSED|FAILED|ERROR)\b")


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of running one candidate against a problem's test suite.

    Attributes:
        passed: Node ids of tests that passed.
        failed: Node ids of tests that failed (including collection/import
            errors attributed to specific tests, when pytest can do so).
        errored: True if the candidate could not be evaluated at all (e.g.
            a syntax error, or a collection failure with no per-test
            results). ``passed``/``failed`` are empty in that case.
    """

    passed: frozenset[str]
    failed: frozenset[str]
    errored: bool = False

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    @property
    def all_passed(self) -> bool:
        return bool(self.passed) and not self.failed and not self.errored


class Evaluator:
    """Runs a candidate against a :class:`Problem`'s fixed pytest suite.

    Each evaluation happens in a fresh temporary directory: the candidate's
    source is written out as ``<module_name>.py`` next to a copy of the
    frozen test file, and pytest is invoked as a subprocess against that
    isolated directory. Isolation this way -- a real subprocess, a throwaway
    directory -- means a broken candidate (bad syntax, an infinite loop,
    whatever) can never contaminate a later candidate's evaluation.
    """

    def __init__(self, problem: Problem):
        self.problem = problem

    def evaluate(self, candidate: Candidate) -> EvaluationResult:
        with tempfile.TemporaryDirectory(prefix="sia-eval-") as tmp:
            tmp_path = Path(tmp)
            (tmp_path / f"{self.problem.module_name}.py").write_text(candidate.source)
            test_file_copy = tmp_path / self.problem.test_file.name
            shutil.copyfile(self.problem.test_file, test_file_copy)

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(test_file_copy.name),
                    "-v",
                    "--tb=no",
                    "-p",
                    "no:cacheprovider",
                ],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )

            passed: set[str] = set()
            failed: set[str] = set()
            for line in proc.stdout.splitlines():
                match = _OUTCOME_LINE.match(line)
                if not match:
                    continue
                nodeid = match.group("nodeid")
                if match.group("outcome") == "PASSED":
                    passed.add(nodeid)
                else:
                    failed.add(nodeid)

            if not passed and not failed:
                return EvaluationResult(passed=frozenset(), failed=frozenset(), errored=True)

            return EvaluationResult(passed=frozenset(passed), failed=frozenset(failed))
