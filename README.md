# Agentic Engineering Portfolio

Original systems demonstrating agentic AI orchestration, data pipeline, and platform engineering patterns.

Each project here is independently designed and built with synthetic data -- none of it is derived from, or a
translation of, any employer's proprietary systems. It demonstrates the same class of engineering (pipeline
orchestration, validation workflows, reconciliation engines, agentic tooling) using original logic and invented
data throughout.

## Workflow

- `main` is protected -- changes land via pull request only.
- `dev` is the working branch.
- CI (`.github/workflows/ci.yml`) runs each project's `pytest` suite in a
  fresh environment on every push/PR to `main` or `dev`.

## Projects

- [`dag-orchestrator/`](dag-orchestrator/) -- a small dependency-aware task
  orchestrator (topological execution, retry-with-backoff, cycle
  detection, failure isolation), demonstrated end-to-end on a synthetic
  bike-share analytics pipeline with a CLI runner. Built test-first;
  26 tests.

- [`multi-agent-reconciliation/`](multi-agent-reconciliation/) -- three
  cooperating agents (extractor, validator, reconciler) that normalize,
  validate, and cross-reference two independently captured synthetic
  inventory datasets, demonstrated end-to-end on an invented tool-lending
  library with a seeded two-source dataset generator and a CLI runner.
  27 tests across extraction, validation, reconciliation, and the full
  pipeline.

- [`self-improving-agent/`](self-improving-agent/) -- a propose -> test ->
  keep loop: a rule-based proposer mutates candidate implementations at
  the AST level, each candidate is scored against a fixed pytest suite in
  an isolated subprocess, and only variants that strictly improve on
  their parent enter a lineage-tracked archive. Demonstrated end-to-end on
  a text-parsing seed problem (naive -> whitespace-safe -> quote-aware ->
  escape-aware) via a CLI runner that prints each generation's outcome
  and the winning lineage. 20 tests across mutation, evaluation, and
  archive/lineage logic.

- [`agent-eval-harness/`](agent-eval-harness/) -- a deterministic-by-default
  harness for scoring agent outputs against a `TaskSpec` (schema
  validation, exact-match fields, numeric-tolerance fields, and a
  pluggable `Judge` protocol with a deterministic `KeywordJudge`
  implementation), demonstrated end-to-end on four synthetic benchmark
  scenarios via a CLI runner that prints a per-task scorecard. 45 tests
  across specs, checks, judge, and result scoring.

- [`mcp-tool-server/`](mcp-tool-server/) -- a Model Context Protocol server
  exposing search/fetch/scale tools over a synthetic recipe-box dataset,
  with handler logic kept independent of the MCP transport so it's fully
  testable without a running server, plus a thin `server.py` adapter that
  registers the handlers as real MCP tools over stdio. 22 tests across
  the catalog and all three tool handlers.

## Status

All five projects are demo-complete: each has a wired-up synthetic
dataset or pipeline, a CLI entry point that runs it and prints readable
output, a project README (task, what it demonstrates, how to run it, test
count), and a passing test suite exercised by CI.
