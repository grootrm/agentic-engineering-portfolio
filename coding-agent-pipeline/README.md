# Coding Agent Pipeline

A deterministic Planner -> Executor -> Validator -> Critic loop, built test-first from scratch. This is a
portfolio piece demonstrating the general shape of an autonomous coding-agent workflow: given a typed
`GoalSpec` (objective, acceptance criteria, constraints, attempt budget), a rule-based planner ranks candidate
strategies, an executor applies each one in turn, a validator scores the result against the spec, and a critic
decides whether to retry the next strategy, escalate with a diagnostic, or declare the goal done -- all without
any real LLM call, so the whole pipeline is deterministic and reproducible in CI.

There is no proprietary logic, schema, or data here. Everything -- including the demo target -- is invented for
this project.

## What it demonstrates

- **Capability-aware planning** -- `planStrategies` filters a strategy catalog down to the ones relevant to a
  goal's declared acceptance criteria, then orders the survivors cheapest-first, so the pipeline always tries
  the simplest plausible fix before reaching for a more complex rewrite. See `tests/planner.test.ts`.
- **Isolated, non-throwing execution** -- `executeStrategy` runs a candidate strategy against the goal's
  scenario and always returns a structured `ExecutionResult`, capturing a thrown error's name (and a
  before/after mutation check on the input) instead of letting a bad candidate crash the run. See
  `tests/executor.test.ts`.
- **Data-driven validation** -- `validate` scores an execution against both `acceptanceCriteria` and
  `constraints` using a small, domain-agnostic set of path-based check kinds (`path-equals`, `path-absent`,
  `path-type`, `throws`/`no-throws`), so the same validator works for any JSON-shaped target. See
  `tests/validator.test.ts`.
- **Branching critic logic** -- `decide` chooses `retry` (with the planner's next-ranked strategy), `escalate`
  (with a distinct cause -- attempt budget exhausted vs. no candidate strategies left -- and a diagnostic of
  what's still failing), or `done`. See `tests/critic.test.ts` and `tests/integration.test.ts`.
- **Strict, generic TypeScript core** -- the pipeline (`GoalSpec<TInput>`, `StrategyFn<TInput, TOutput>`, ...)
  is generic over the domain payload and instantiated concretely only in `demo/`, under `strict` mode with
  `noUncheckedIndexedAccess`.

## The demo target: `mergeConfig`

`demo/mergeConfigStrategies.ts` defines four candidate implementations of a layered JSON config merger
(`mergeConfig(layers, policy)`), strictly increasing in capability:

1. `recursive-merge` -- merges nested objects, but replaces arrays wholesale, overwrites instead of deleting on
   `null`, and corrupts an object-vs-array type collision (`typeof [] === "object"` is a classic trap) instead
   of replacing it.
2. `recursive-merge-with-arrays` -- adds `policy.arrays` (`replace`/`concat`/`concat-dedupe`) support.
3. `recursive-merge-with-null-delete` -- adds `policy.nullMeansDelete` support.
4. `full-featured-merge` -- adds correct object/array type-conflict handling (wholesale replace under
   `"override"`, a `TypeConflictError` under `"error"`).

```
        GoalSpec
           |
           v
      +----------+   cost-ranked strategies   +----------+
      | Planner  | -------------------------> | Executor |
      +----------+                            +----------+
                                                    |
                                                    v ExecutionResult
      +----------+   pass/fail per check     +-----------+
      |  Critic  | <------------------------ | Validator |
      +----------+                           +-----------+
        |     |
  retry |     | done / escalate
        +-----+--> next attempt, or stop
```

The bundled `happy-path` demo goal requires all four capabilities, so the planner tries the four strategies in
cost order and the critic retries three times before the fourth strategy satisfies every check -- watch it with
`npm run demo -- --goal happy-path`.

## Running it

```bash
npm install
npm run typecheck
npm test

npm run demo -- --goal minimal        # done on attempt 1
npm run demo -- --goal happy-path     # retries through all 4 strategies, done on attempt 4
npm run demo -- --goal escalate       # exhausts a 2-attempt budget, escalates
npm run demo -- --goal impossible     # no strategy matches -> escalates immediately
npm run demo -- --goal escalate --max-attempts 4   # same scenario, now succeeds
npm run demo -- --goal happy-path --json           # print the full RunReport as JSON
```

## Tests

Built test-first throughout: for every capability, a failing test was written and confirmed to fail for the
right reason before any implementation code was added.

```bash
npm test
```

59 tests across:
- `tests/jsonUtils.test.ts` -- JSON clone/equal/path/type/depth helpers
- `tests/validateGoalSpec.test.ts` -- GoalSpec validation
- `tests/planner.test.ts` -- capability-filtered, cost-ranked planning
- `tests/executor.test.ts` -- isolated strategy execution and mutation detection
- `tests/validator.test.ts` -- every acceptance-check and constraint kind
- `tests/critic.test.ts` -- retry/escalate/done branching, both escalate causes
- `tests/orchestrator.test.ts` -- the full loop against synthetic fixture strategies
- `tests/mergeConfigStrategies.test.ts` -- the four real merge strategies
- `tests/goals.test.ts` -- CLI goal selection
- `tests/integration.test.ts` -- the full pipeline end to end, including a retry-then-succeed run and an
  escalate-after-exhausting-attempts run

## Layout

```
coding-agent-pipeline/
  src/coding-agent-pipeline/   core engine: goal spec, planner, executor, validator, critic, orchestrator
  src/cli.ts                   CLI entry point
  demo/                        the synthetic mergeConfig target, strategies, and demo goals
  tests/                       vitest suite (unit + integration)
```
