"""agent_eval_harness: a small harness for scoring AI agent outputs.

Deterministic, rule-based checks (schema validation, exact match, numeric
tolerance) run with no external calls and no API keys. A pluggable
``Judge`` interface adds a seam for softer, free-text scoring; it ships
with a default heuristic judge so the whole harness runs standalone.
"""
