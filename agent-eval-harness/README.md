# Agent Eval Harness

A small, deterministic-by-default harness for scoring an AI agent's
structured output against a task specification, with a pluggable judge
interface for the free-text parts a schema check can't reach. This is a
portfolio piece demonstrating the general shape of an agent-eval framework
(the kind of thing behind most agent benchmarks and offline eval suites):
declare a contract for what a correct output looks like, score an actual
output against it with checks that always give the same answer for the
same input, and leave a clean seam for a softer, LLM-backed judge to plug
in later without changing anything else.

There is no proprietary logic, schema, or data here. Everything --
including the demo domain -- is invented for this project.

## What it demonstrates

- **Deterministic structural scoring** -- `TaskSpec` declares a schema
  (required/optional fields and their types), exact-match fields, and
  numeric fields scored by tolerance rather than equality. `checks.py`
  turns those declarations into `CheckResult`s with no network calls, no
  randomness, and no API keys: the same output always scores the same way.
- **A pluggable `Judge` seam** -- `judge.py` defines a `Judge` protocol
  (`evaluate(spec, output) -> JudgeResult`) for scoring a task's free-text
  `explanation_field`. The harness ships one concrete implementation,
  `KeywordJudge`, which checks case-insensitive keyword coverage and
  forbidden-phrase absence -- deterministic, so the whole harness still
  runs standalone. A future LLM-backed judge is a drop-in second
  implementation of the same protocol.
- **Blended scoring** -- `ScoreResult.score` averages the fraction of
  deterministic checks passed with the judge's score 50/50 when a judge is
  present (and falls back to just the checks fraction, or 1.0 with
  neither, when there's nothing to judge).

## The demo benchmark

`benchmarks/scenarios.py` defines four synthetic tasks for an invented
"order support" agent, each with sample outputs that either pass cleanly
or fail/partially fail so the scorecard has something to show:

- `extract_order_summary` -- pure schema check (missing field, wrong type)
- `classify_ticket_priority` -- exact-match fields
- `estimate_shipping_cost` -- numeric tolerance
- `explain_refund_decision` -- schema + exact fields + `KeywordJudge` over
  a free-text explanation

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python run.py
```

Sample output:

```
== extract_order_summary ==
   Extract order_id, item_count, and total from a support ticket.
  [PASS] well_formed  score=1.00
  [FAIL] missing_item_count  score=0.00
        failing checks: schema
  [FAIL] wrong_type_for_total  score=0.00
        failing checks: schema

...

== explain_refund_decision ==
   Explain why a refund was approved for a damaged-item claim.
  [PASS] clear_explanation  score=1.00
        judge OK: found keywords ['damaged', 'refund']
  [FAIL] vague_and_dismissive  score=0.50
        judge FAILED: found no required keywords; missing keywords ['damaged', 'refund']; forbidden phrases present: ['not our policy']

Summary: 4/9 outputs passed, mean score 0.63
```

## Tests

```bash
pytest
```

45 tests across:
- `tests/test_spec.py` -- `TaskSpec`/`FieldSpec`/`NumericToleranceSpec` contracts
- `tests/test_checks.py` -- schema, exact-match, and numeric-tolerance checkers
- `tests/test_result.py` -- `CheckResult`/`JudgeResult`/`ScoreResult` scoring semantics
- `tests/test_judge.py` -- the `Judge` protocol and the default `KeywordJudge`

## Layout

```
agent-eval-harness/
  src/agent_eval_harness/   spec, checks, judge, result types
  benchmarks/                the synthetic order-support scenarios
  tests/                     pytest suite
  run.py                     CLI entry point
```
