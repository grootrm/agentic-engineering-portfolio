# MCP Tool Server

A small Model Context Protocol (MCP) server exposing recipe-box tools over
a synthetic, invented recipe catalog. This is a portfolio piece
demonstrating how to build MCP tools with the protocol plumbing kept
completely separate from the tool logic itself.

There is no proprietary logic, schema, or data here. The recipe catalog
(`src/mcp_tool_server/catalog.py`) is invented for this project -- it is
not derived from any real cookbook, business, or proprietary dataset.

## What it demonstrates

- **Protocol/logic separation** -- `src/mcp_tool_server/tools.py` contains
  plain functions with no MCP-protocol code at all. `src/mcp_tool_server/server.py`
  is a thin adapter: every `@mcp.tool()` body is a one-line call into
  `tools.py`. This is what lets the test suite exercise every tool's
  behavior directly, in-process, without spinning up a server or speaking
  the MCP transport -- and it's why `server.py` itself carries no
  behavioral tests of its own.
- **Deterministic, well-formed data as a first-class concern** --
  `tests/test_catalog.py` validates the synthetic dataset itself (unique
  ids, positive quantities, every ingredient carrying a name/quantity/unit)
  before any tool logic is trusted to operate on it.
- **Explicit failure signaling** -- an unknown tag or recipe id raises a
  specific exception (`UnknownTagError`, `RecipeNotFoundError`) rather than
  returning a silently empty result, so a caller (or an LLM driving the
  tool) gets a clear signal to act on.
- **A tool with real computation, not just a lookup** -- `scale_recipe`
  proportionally rescales every ingredient's quantity to a target serving
  count, returning a new recipe without mutating the catalog.

## The tools

- `search_recipes(query="", tag=None, max_prep_minutes=None)` -- find
  recipe summaries by case-insensitive free-text query (title or
  ingredient name), an exact tag, and/or a prep-time ceiling.
- `get_recipe(recipe_id)` -- fetch one recipe's full ingredients and steps.
- `scale_recipe(recipe_id, servings)` -- fetch a recipe with every
  ingredient quantity scaled to a target serving count.

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate        # or: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python run.py --demo   # call the tools directly and print sample output
python run.py          # start the real MCP server over stdio
```

`--demo` exists because the real server mode blocks waiting for an MCP
client to connect over stdin/stdout and produces no readable output on its
own -- it's there so you can see the tools work without wiring up a client
first. Plain `python run.py` is what a real MCP host (Claude Desktop,
Claude Code, or any other MCP client) would launch as a subprocess and
talk to over stdio; point a client's MCP server config at this command to
use it for real.

## Tests

22 tests across:
- `tests/test_catalog.py` -- the synthetic dataset is well-formed
- `tests/test_search_recipes.py` -- `search_recipes` filtering, sorting,
  and error behavior
- `tests/test_get_recipe.py` -- `get_recipe` / `scale_recipe` lookup,
  scaling arithmetic, non-mutation of the catalog, and error behavior

```bash
pytest
```

## Layout

```
mcp-tool-server/
  src/mcp_tool_server/   catalog, tool handlers, errors, MCP server adapter
  tests/                 pytest suite (catalog + both tool handlers)
  run.py                 CLI entry point (--demo or real stdio server)
```
