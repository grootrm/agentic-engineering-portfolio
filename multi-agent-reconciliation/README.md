# Multi-Agent Reconciliation

Three cooperating agents -- an Extractor, a Validator, and a Reconciler --
built test-first to reconcile two independently captured inventory
snapshots. This is a portfolio piece demonstrating a pattern common to any
system stitching together data from systems that were never designed to
agree with each other: normalize each source into one canonical shape,
validate business rules independently, and only then compare across
sources so a "shape" problem is never confused with a genuine discrepancy.

There is no proprietary logic, schema, or data here. Everything --
including the demo domain -- is invented for this project.

## What it demonstrates

- **A three-agent pipeline with typed message contracts** -- each agent
  (`ExtractorAgent`, `ValidatorAgent`, `ReconcilerAgent`) has a single
  responsibility and speaks a fixed input/output contract
  (`RawRecordBatch -> ExtractedBatch -> ValidatedBatch -> DiscrepancyReport`,
  see `src/reconciliation_agents/messages.py`). No agent ever sees another
  agent's internals, only the message type it promised to produce.
- **Shape failures vs. business-rule failures, kept separate** -- a row
  that can't even be identified (no tag) or type-coerced (a quantity
  that isn't a number) is an `ExtractionError`, the Extractor's concern.
  A well-formed record that violates a business rule (unknown category,
  non-positive quantity, malformed tag format) is an `InvalidRecord`, the
  Validator's concern. Neither agent silently drops a row -- every input
  ends up in exactly one output bucket.
- **Dialect normalization** -- the two source systems describe the same
  tool with different field names and different condition encodings; the
  Extractor absorbs that difference so nothing downstream has to know
  which system a record came from.
- **Duplicate-tag exclusion from matching** -- a tag_id that appears more
  than once within a single source makes that source's claim about the
  tag unreliable. Duplicates are excluded from cross-source matching and
  reported separately (`DiscrepancyReport.duplicate_tags`) rather than
  silently picking one and guessing.

## The demo domain

Millbrook Tool Library is an invented community tool-lending library with
two systems that each take their own snapshot of the same inventory:

- `checkout_ledger` -- the front-desk checkout ledger, in an abbreviated
  dialect (`tag`, `cond` as `g`/`f`/`r`, `qty`, `bin`).
- `shelf_sweep` -- a periodic shelf-audit sweep, in a fully spelled-out
  dialect (`tag_id`, `condition`, `quantity`, `location_bin`).

`pipeline/dataset_generator.py` generates both sources from one seed,
deterministically routing each synthetic tool through one of five
reconciliation scenarios (matched, quantity mismatch, condition mismatch,
missing from the ledger, missing from the sweep), plus a duplicated ledger
tag and a handful of malformed rows per source -- so every branch of the
Extractor, Validator, and Reconciler is exercised on every run.

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python run.py                                  # 40 synthetic tools, seed 42
python run.py --record-count 100 --seed 7      # bigger, different run
```

## Tests

Built test-first throughout: for every capability, a failing test was
written and confirmed to fail for the right reason before any
implementation code was added.

```bash
pytest
```

27 tests across:
- `tests/test_extractor.py` -- dialect normalization and shape-failure handling
- `tests/test_validator.py` -- business-rule checks
- `tests/test_reconciler.py` -- matching, mismatches, and duplicate-tag handling
- `tests/test_pipeline_integration.py` -- the full synthetic pipeline end
  to end, including deterministic generation and a fixed-seed scenario
  check pinned to specific tag ids

## Layout

```
multi-agent-reconciliation/
  src/reconciliation_agents/   core agents: extractor, validator, reconciler, messages, records
  pipeline/                    the synthetic Millbrook Tool Library demo data + wiring
  tests/                       pytest suite (unit + integration)
  run.py                       CLI entry point
```
