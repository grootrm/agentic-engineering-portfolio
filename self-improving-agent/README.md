# Self-Improving Agent

A small propose -> test -> keep loop, built test-first from scratch. This
is a portfolio piece demonstrating the general engineering pattern behind
evolutionary/self-improving coding agents (in the spirit of AlphaEvolve
and similar systems): a rule-based proposer mutates a candidate
implementation, each mutation is scored against a fixed acceptance
suite in an isolated subprocess, and only variants that are a genuine
improvement over their parent survive into a lineage-tracked archive.

There is no proprietary logic, schema, or data here. Everything --
including the demo problem -- is invented for this project.

## What it demonstrates

- **AST-level mutation** -- `mutator.replace_function_body` splices a new
  function body into a candidate's source via the `ast` module (not
  string-splicing), so the result is always re-parsed and re-generated as
  syntactically valid Python before it's ever handed to the evaluator. A
  malformed mutation rule fails fast with a `SyntaxError` at proposal
  time, not as a mysterious downstream failure.
- **Subprocess-isolated evaluation** -- `Evaluator.evaluate` writes a
  candidate's source into a fresh temporary directory next to a copy of
  the problem's frozen test file, then runs `pytest` as a real
  subprocess against that isolated directory. A broken candidate (bad
  syntax, an infinite loop, whatever) can never contaminate a later
  candidate's evaluation.
- **Strict-improvement archive with lineage tracking** -- `Archive.try_add`
  keeps the initial seed unconditionally, but keeps a later candidate
  only if it passes a *strict superset* of the tests its parent passed.
  Regressions and no-op mutations are evaluated but never enter the
  archive, so `Archive.lineage(...)` always reads as a monotonic
  improvement history back to the seed.

## The demo problem: `text_parsing`

`problems/text_parsing/` defines `split_csv_line(line: str) -> list[str]`,
a small CSV-line splitter with graduated failure modes:

1. **Seed** (`line.split(",")`) -- correct only for plain, unquoted
   fields.
2. **`strip_whitespace`** -- also strips leading/trailing whitespace
   around each field.
3. **`handle_quoted_fields`** -- also tracks quote state so commas
   *inside* a quoted field aren't treated as separators.
4. **`handle_escaped_quotes`** -- also treats a doubled quote inside a
   quoted field (`""`) as an escaped literal quote, the standard CSV
   escaping convention.

Each rule's body is a complete, standalone reimplementation -- strictly
more capable than the one before it -- against
`problems/text_parsing/test_text_parsing.py`'s 11 cases, grouped by
which rule is required to pass them (4 pass at the seed, 6 after rule 1,
9 after rule 2, all 11 after rule 3).

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python run.py                       # runs the text_parsing problem
python run.py --problem text_parsing
```

Sample output:

```
Running propose -> test -> keep loop on problem 'text_parsing' (3 candidate generations)...

  [KEPT  ] seed                     4/11 tests passed
  [KEPT  ] strip_whitespace         6/11 tests passed
  [KEPT  ] handle_quoted_fields     9/11 tests passed
  [KEPT  ] handle_escaped_quotes    11/11 tests passed

Lineage of the best kept candidate:
  gen 0: seed                     4 passed -- initial seed -- passes 4/11 tests
  gen 1: strip_whitespace         6 passed -- gained [...] beyond its predecessor (via 'strip_whitespace')
  gen 2: handle_quoted_fields     9 passed -- gained [...] beyond its predecessor (via 'handle_quoted_fields')
  gen 3: handle_escaped_quotes    11 passed -- gained [...] beyond its predecessor (via 'handle_escaped_quotes')

Final candidate ('handle_escaped_quotes') passes all tests.
```

Exits 0 if the final kept candidate passes every test, 1 otherwise.

## Tests

Built test-first throughout: for every capability, a failing test was
written and confirmed to fail for the right reason before any
implementation code was added.

```bash
pytest
```

20 tests across:
- `tests/test_mutator.py` -- AST-level function-body replacement
- `tests/test_evaluator.py` -- isolated subprocess evaluation, using tiny
  fixture problems independent of the real demo domain
- `tests/test_archive.py` -- strict-superset keep/reject logic, lineage
  chains, and best-candidate selection

`problems/text_parsing/test_text_parsing.py` (11 further cases) is a
separate, frozen acceptance suite -- it's not collected by the project's
own `pytest` run (`testpaths = ["tests"]`); it only runs inside the
Evaluator's isolated temp directory, against whichever candidate is
under test.

## Layout

```
self-improving-agent/
  src/self_improving_agent/   core engine: candidate, mutator, evaluator, archive, problem
  problems/text_parsing/      the synthetic text_parsing demo problem + its frozen suite
  tests/                      pytest suite for the core engine
  run.py                      CLI entry point
```
