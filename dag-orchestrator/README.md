# DAG Orchestrator

A small, dependency-aware task orchestrator, built test-first from scratch.
This is a portfolio piece demonstrating the general engineering pattern
behind most workflow schedulers (Airflow, Dagster, and friends, and the
in-house orchestration most data teams eventually build): replace a
fragile sequential batch script with a graph of tasks that declare their
own dependencies, get scheduled in the correct order automatically,
retry transient failures instead of taking down the whole run, and fail
loudly instead of hanging when someone accidentally introduces a
circular dependency.

There is no proprietary logic, schema, or data here. Everything --
including the demo domain -- is invented for this project.

## What it demonstrates

- **Dependency resolution / topological execution** -- tasks declare the
  names of the tasks they depend on; the orchestrator computes a valid
  run order (`Graph.topological_order`) and the executor runs each task
  only after all of its dependencies have completed.
- **Cycle detection** -- the same graph walk that computes run order
  uses a three-color DFS to detect back-edges. A circular dependency is
  reported as a `CycleError` naming the cycle, rather than causing an
  infinite loop or a hang. See `tests/test_cycle_detection.py`, including
  a 200-node cyclic graph that must fail fast rather than hang.
- **Retry with exponential backoff** -- each task carries its own
  `max_retries` and `backoff_seconds`. On failure the executor retries
  with delay `backoff_seconds * 2 ** attempt` between attempts, and
  records how many attempts each task took.
- **Failure isolation** -- if a task exhausts its retries, everything
  that (transitively) depends on it is marked `SKIPPED` rather than run,
  while unrelated branches of the graph still complete normally.

## The demo pipeline

`pipeline/bikeshare_pipeline.py` wires up a small nightly-analytics job
for "CascadeCycle," an invented city bike-share operator, over synthetic
ride data (`pipeline/data_generator.py`, seeded and reproducible, with a
deliberate ~8% malformed-record rate to give validation real work to
do):

```
ingest_rides
     |
validate_rides
     |
enrich_with_weather   (simulated flaky external call -> retried)
   /            \
station_demand   ride_duration_stats
    |                  |
rebalancing_recs       |
    \                 /
     generate_ops_report
```

`enrich_with_weather` stands in for the kind of unreliable external
dependency (an API, a downstream service) that a real pipeline has to
tolerate -- the demo runner can force it to fail its first N calls so
you can watch the retry logic recover, or exhaust its retry budget so
you can watch failure isolation kick in.

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python run.py                                       # happy path
python run.py --ride-count 5000 --seed 7             # bigger run
python run.py --fail-weather 2 --weather-retries 3   # watch a retry recover
python run.py --fail-weather 5 --weather-retries 1   # watch it fail + skip downstream (exit code 1)
```

## Tests

Built test-first throughout: for every capability, a failing test was
written and confirmed to fail for the right reason before any
implementation code was added.

```bash
pytest
```

26 tests across:
- `tests/test_graph.py` -- graph construction and topological ordering
- `tests/test_cycle_detection.py` -- cycle detection, including a
  large cyclic graph that must fail fast instead of hanging
- `tests/test_executor.py` -- execution order and shared-context
  propagation
- `tests/test_retry.py` -- retry-with-backoff semantics
- `tests/test_pipeline_integration.py` -- the full synthetic pipeline
  end to end, including forced retry and forced-failure scenarios

## Layout

```
dag-orchestrator/
  src/dag_orchestrator/   core engine: task, graph, executor, errors
  pipeline/                the synthetic bike-share demo pipeline
  tests/                   pytest suite (unit + integration)
  run.py                   CLI entry point
```
