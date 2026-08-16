#!/usr/bin/env python
"""Demo runner: builds the CascadeCycle bike-share pipeline and executes it.

    python run.py
    python run.py --ride-count 5000 --seed 7
    python run.py --fail-weather 5 --weather-retries 2   # force a failed run

Exits 0 if every task succeeded, 1 otherwise (so it can be dropped into a
CI job or scheduler the same way a real orchestrated pipeline would be).
"""

from __future__ import annotations

import argparse
import json
import sys

from dag_orchestrator.executor import Executor, Status
from pipeline.bikeshare_pipeline import build_pipeline


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for synthetic ride data")
    parser.add_argument("--ride-count", type=int, default=2000, help="number of synthetic rides to generate")
    parser.add_argument(
        "--fail-weather",
        type=int,
        default=0,
        metavar="N",
        help="make the weather-enrichment task fail its first N calls (demonstrates retry)",
    )
    parser.add_argument(
        "--weather-retries",
        type=int,
        default=2,
        help="retry budget for the weather-enrichment task",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    graph = build_pipeline(
        seed=args.seed,
        ride_count=args.ride_count,
        fail_first_n_weather_calls=args.fail_weather,
        weather_max_retries=args.weather_retries,
    )

    print(f"Running CascadeCycle nightly analytics ({len(graph)} tasks)...\n")

    order = graph.topological_order()
    result = Executor(graph).run()

    print("Execution order and outcome:")
    for name in order:
        status = result.status_of(name)
        attempts = result.attempts_of(name)
        attempt_note = f" ({attempts} attempt{'s' if attempts != 1 else ''})" if attempts else ""
        print(f"  [{status.name:>7}] {name}{attempt_note}")

    print()
    if result.success:
        report = result.context["generate_ops_report"]
        print("Ops report:")
        print(json.dumps(report, indent=2))
    else:
        print("Pipeline failed -- see task statuses above.")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
