# Agentic Engineering Portfolio

Original systems demonstrating agentic AI orchestration, data pipeline, and platform engineering patterns.

Each project here is independently designed and built with synthetic data — none of it is derived from, or a
translation of, any employer's proprietary systems. It demonstrates the same class of engineering (pipeline
orchestration, validation workflows, reconciliation engines, agentic tooling) using original logic and invented
data throughout.

## Workflow

- `main` is protected — changes land via pull request only.
- `dev` is the working branch.

## Projects

- [`dag-orchestrator/`](dag-orchestrator/) -- a small dependency-aware task
  orchestrator (topological execution, retry-with-backoff, cycle
  detection), demonstrated on a synthetic bike-share analytics pipeline.
  Built test-first.
