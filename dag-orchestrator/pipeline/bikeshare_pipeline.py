"""CascadeCycle bike-share nightly analytics, expressed as a task graph.

CascadeCycle is a fictional city bike-share operator invented for this
portfolio piece. The scenario: analytics used to run as one long
sequential script (ingest, then validate, then enrich, then aggregate,
then report) where a hiccup anywhere meant re-running everything from
the top. Here the same work is expressed as a dependency graph so that
independent branches can be reasoned about (and, in a concurrent
executor, run) independently, transient failures are retried instead of
blowing up the whole run, and a broken step only takes down the parts of
the report that actually depend on it.

    ingest_rides
         |
    validate_rides
         |
    enrich_with_weather  (flaky external call -> retried with backoff)
       /            \\
station_demand   ride_duration_stats
      |                  |
rebalancing_recs         |
       \\                /
        generate_ops_report
"""

from __future__ import annotations

import random
from collections import defaultdict
from statistics import mean, median

from dag_orchestrator.graph import Graph
from dag_orchestrator.task import Task
from pipeline.data_generator import generate_rides

WEATHER_CONDITIONS = ["clear", "rain", "cloudy", "windy"]
REBALANCE_THRESHOLD = 3


def _make_ingest_rides(seed: int, ride_count: int):
    def _ingest(context):
        return generate_rides(seed=seed, count=ride_count)

    return _ingest


def _validate_rides(context):
    rides = context["ingest_rides"]
    valid = [
        r for r in rides if r["start_station"] and r["duration_minutes"] > 0
    ]
    return {
        "valid_rides": valid,
        "total": len(rides),
        "dropped": len(rides) - len(valid),
    }


def _make_enrich_with_weather(fail_first_n_calls: int):
    call_count = {"n": 0}

    def _enrich(context):
        call_count["n"] += 1
        if call_count["n"] <= fail_first_n_calls:
            raise RuntimeError("weather service timeout (simulated)")

        valid_rides = context["validate_rides"]["valid_rides"]
        rng = random.Random(len(valid_rides))
        return [
            {**ride, "weather": rng.choice(WEATHER_CONDITIONS)}
            for ride in valid_rides
        ]

    return _enrich


def _compute_station_demand(context):
    rides = context["enrich_with_weather"]
    demand: dict[str, dict[str, int]] = defaultdict(
        lambda: {"departures": 0, "arrivals": 0}
    )
    for ride in rides:
        demand[ride["start_station"]]["departures"] += 1
        demand[ride["end_station"]]["arrivals"] += 1
    return dict(demand)


def _compute_ride_duration_stats(context):
    durations = [ride["duration_minutes"] for ride in context["enrich_with_weather"]]
    if not durations:
        return {"count": 0, "mean_minutes": 0.0, "median_minutes": 0.0, "max_minutes": 0.0}
    return {
        "count": len(durations),
        "mean_minutes": round(mean(durations), 2),
        "median_minutes": round(median(durations), 2),
        "max_minutes": round(max(durations), 2),
    }


def _compute_rebalancing_recommendations(context):
    demand = context["compute_station_demand"]
    recommendations = []
    for station, counts in sorted(demand.items()):
        net = counts["departures"] - counts["arrivals"]
        if net > REBALANCE_THRESHOLD:
            recommendations.append(
                {"station": station, "action": "restock", "urgency": net}
            )
        elif net < -REBALANCE_THRESHOLD:
            recommendations.append(
                {"station": station, "action": "collect", "urgency": -net}
            )
    return recommendations


def _generate_ops_report(context):
    validation = context["validate_rides"]
    return {
        "total_rides_ingested": len(context["ingest_rides"]),
        "valid_rides": len(validation["valid_rides"]),
        "dropped_rides": validation["dropped"],
        "ride_duration_stats": context["compute_ride_duration_stats"],
        "rebalancing_recommendations": context["compute_rebalancing_recommendations"],
    }


def build_pipeline(
    seed: int,
    ride_count: int,
    fail_first_n_weather_calls: int = 0,
    weather_max_retries: int = 2,
    weather_backoff_seconds: float = 0.0,
) -> Graph:
    """Assemble the CascadeCycle nightly analytics task graph.

    Args:
        seed: RNG seed for reproducible synthetic ride generation.
        ride_count: number of synthetic ride records to generate.
        fail_first_n_weather_calls: how many times the (simulated) weather
            enrichment call should fail before succeeding — lets the demo
            and tests exercise retry-with-backoff on demand.
        weather_max_retries: retry budget for the weather enrichment task.
        weather_backoff_seconds: base backoff delay for that task.
    """
    graph = Graph()
    graph.add_task(Task(name="ingest_rides", func=_make_ingest_rides(seed, ride_count)))
    graph.add_task(
        Task(name="validate_rides", func=_validate_rides, depends_on=["ingest_rides"])
    )
    graph.add_task(
        Task(
            name="enrich_with_weather",
            func=_make_enrich_with_weather(fail_first_n_weather_calls),
            depends_on=["validate_rides"],
            max_retries=weather_max_retries,
            backoff_seconds=weather_backoff_seconds,
        )
    )
    graph.add_task(
        Task(
            name="compute_station_demand",
            func=_compute_station_demand,
            depends_on=["enrich_with_weather"],
        )
    )
    graph.add_task(
        Task(
            name="compute_ride_duration_stats",
            func=_compute_ride_duration_stats,
            depends_on=["enrich_with_weather"],
        )
    )
    graph.add_task(
        Task(
            name="compute_rebalancing_recommendations",
            func=_compute_rebalancing_recommendations,
            depends_on=["compute_station_demand"],
        )
    )
    graph.add_task(
        Task(
            name="generate_ops_report",
            func=_generate_ops_report,
            depends_on=[
                "compute_rebalancing_recommendations",
                "compute_ride_duration_stats",
            ],
        )
    )
    return graph
