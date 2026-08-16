"""A coding problem: a seed implementation plus a fixed acceptance suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MutationRule:
    """One deterministic transformation the rule-based proposer can try.

    ``new_body_source`` is spliced in as the target function's entire body
    via :func:`self_improving_agent.mutator.replace_function_body`, so it
    must be a self-contained implementation, not a diff.
    """

    name: str
    description: str
    new_body_source: str


@dataclass(frozen=True)
class Problem:
    """A pytest-defined coding problem for the propose -> test -> keep loop.

    Attributes:
        name: Human-readable problem name.
        module_name: The module name the fixed test file imports from
            (the Evaluator writes each candidate's source to a file with
            this name so ``from <module_name> import ...`` resolves).
        function_name: Name of the function under test.
        seed_source: Full source of the initial (typically naive) candidate.
        test_file: Path to the frozen pytest suite defining this problem.
        mutation_rules: Ordered, fixed rules the default RuleBasedProposer
            tries, one per generation, against the current best candidate.
    """

    name: str
    module_name: str
    function_name: str
    seed_source: str
    test_file: Path
    mutation_rules: tuple[MutationRule, ...] = field(default_factory=tuple)
