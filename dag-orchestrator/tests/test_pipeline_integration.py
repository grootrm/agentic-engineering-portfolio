"""End-to-end test of the synthetic bike-share analytics pipeline.

This is the demonstration pipeline for the portfolio piece: a fictional
city bike-share operator ("CascadeCycle") that used to run its nightly
analytics as one long sequential script. Here it is expressed as a
dependency graph and run through the orchestrator.
"""

from dag_orchestrator.executor import Executor, Status
from pipeline.bikeshare_pipeline import build_pipeline
from pipeline.data_generator import generate_rides


def test_generated_rides_are_deterministic_for_a_given_seed():
    rides_a = generate_rides(seed=7, count=50)
    rides_b = generate_rides(seed=7, count=50)

    assert rides_a == rides_b
    assert len(rides_a) == 50


def test_full_pipeline_runs_end_to_end_and_produces_a_report():
    graph = build_pipeline(seed=42, ride_count=300)

    result = Executor(graph).run()

    assert result.success is True
    for task_name in graph.tasks:
        assert result.status_of(task_name) == Status.SUCCESS

    report = result.context["generate_ops_report"]
    assert "total_rides_ingested" in report
    assert "valid_rides" in report
    assert "rebalancing_recommendations" in report
    assert "ride_duration_stats" in report
    assert report["valid_rides"] <= report["total_rides_ingested"]


def test_pipeline_expected_task_names_and_dependency_shape():
    graph = build_pipeline(seed=1, ride_count=10)

    assert set(graph.tasks) == {
        "ingest_rides",
        "validate_rides",
        "enrich_with_weather",
        "compute_station_demand",
        "compute_ride_duration_stats",
        "compute_rebalancing_recommendations",
        "generate_ops_report",
    }
    # The report is the sink: it must (transitively) depend on every
    # other task so it always runs last.
    order = graph.topological_order()
    assert order[-1] == "generate_ops_report"
    assert order[0] == "ingest_rides"


def test_pipeline_survives_transient_weather_enrichment_failures():
    # The weather-enrichment step simulates an unreliable external call.
    # With enough retry budget the pipeline should still succeed.
    graph = build_pipeline(
        seed=5, ride_count=20, fail_first_n_weather_calls=2, weather_max_retries=3
    )

    result = Executor(graph).run()

    assert result.success is True
    assert result.attempts_of("enrich_with_weather") == 3


def test_pipeline_fails_and_skips_downstream_when_retries_are_exhausted():
    graph = build_pipeline(
        seed=5, ride_count=20, fail_first_n_weather_calls=5, weather_max_retries=1
    )

    result = Executor(graph).run()

    assert result.success is False
    assert result.status_of("enrich_with_weather") == Status.FAILED
    assert result.status_of("compute_station_demand") == Status.SKIPPED
    assert result.status_of("compute_ride_duration_stats") == Status.SKIPPED
    assert result.status_of("compute_rebalancing_recommendations") == Status.SKIPPED
    assert result.status_of("generate_ops_report") == Status.SKIPPED
