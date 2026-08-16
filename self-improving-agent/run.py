#!/usr/bin/env python
"""Demo runner: drives the propose -> test -> keep loop over a seed problem.

    python run.py
    python run.py --problem text_parsing

For each mutation rule in the chosen problem, splices in a new candidate
function body (AST-level, via
``self_improving_agent.mutator.replace_function_body``), evaluates it
against the problem's frozen pytest suite in an isolated subprocess, and
keeps it only if it passes a strict superset of what its parent passed.
Prints the kept/rejected status of each generation and, at the end, the
lineage of the best kept candidate.

Exits 0 if the final kept candidate passes every test in the problem's
suite, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys

from self_improving_agent.archive import Archive, ArchiveEntry
from self_improving_agent.candidate import Candidate
from self_improving_agent.evaluator import EvaluationResult, Evaluator
from self_improving_agent.mutator import replace_function_body
from self_improving_agent.problem import Problem


def _load_problem(name: str) -> Problem:
    if name == "text_parsing":
        from problems.text_parsing.problem import PROBLEM

        return PROBLEM
    raise ValueError(f"unknown problem {name!r}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--problem", default="text_parsing", help="name of the problem to run (default: text_parsing)"
    )
    return parser.parse_args(argv)


def _report(candidate: Candidate, result: EvaluationResult, entry: ArchiveEntry | None) -> None:
    if result.errored:
        print(f"  [ERROR ] {candidate.strategy:<24} candidate could not be evaluated")
        return
    status = "KEPT  " if entry is not None else "REJECT"
    print(f"  [{status}] {candidate.strategy:<24} {len(result.passed)}/{result.total} tests passed")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    problem = _load_problem(args.problem)
    evaluator = Evaluator(problem)
    archive = Archive()

    print(f"Running propose -> test -> keep loop on problem '{problem.name}' " f"({len(problem.mutation_rules)} candidate generations)...\n")

    seed = Candidate(id="seed", source=problem.seed_source, strategy="seed", parent_id=None, generation=0)
    seed_result = evaluator.evaluate(seed)
    seed_entry = archive.try_add(seed, seed_result)
    _report(seed, seed_result, seed_entry)

    current_id = seed.id
    current_source = problem.seed_source

    for generation, rule in enumerate(problem.mutation_rules, start=1):
        try:
            candidate_source = replace_function_body(current_source, problem.function_name, rule.new_body_source)
        except (SyntaxError, LookupError) as exc:
            print(f"  [ERROR ] {rule.name:<24} mutation could not be applied ({exc})")
            continue

        candidate = Candidate(
            id=rule.name,
            source=candidate_source,
            strategy=rule.name,
            parent_id=current_id,
            generation=generation,
        )
        result = evaluator.evaluate(candidate)
        entry = archive.try_add(candidate, result)
        _report(candidate, result, entry)

        if entry is not None:
            current_id = candidate.id
            current_source = candidate_source

    best = archive.best()
    print("\nLineage of the best kept candidate:")
    for entry in archive.lineage(best.candidate.id):
        print(
            f"  gen {entry.candidate.generation}: {entry.candidate.strategy:<24} "
            f"{len(entry.passed_tests)} passed -- {entry.kept_reason}"
        )

    print()
    if best.all_passed:
        print(f"Final candidate ('{best.candidate.strategy}') passes all tests.")
    else:
        print(f"Final candidate ('{best.candidate.strategy}') still has failing tests -- see above.")

    return 0 if best.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
