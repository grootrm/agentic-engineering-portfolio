#!/usr/bin/env python
"""Entry point for the recipe-box MCP server.

    python run.py            # start the real MCP server over stdio
    python run.py --demo      # call the tool handlers directly and print
                               # sample output, without speaking MCP at all

The stdio mode is what a real MCP client (Claude Desktop, Claude Code,
any other MCP host) would launch as a subprocess and talk to over
stdin/stdout. --demo exists because that mode blocks waiting for a client
and produces no readable output on its own -- it's here so you can see
the tools work without wiring up a client first.
"""

from __future__ import annotations

import argparse
import json
import sys

from mcp_tool_server import tools
from mcp_tool_server.server import main as run_server


def run_demo() -> int:
    print("== search_recipes(tag='quick', max_prep_minutes=20) ==")
    results = tools.search_recipes(tag="quick", max_prep_minutes=20)
    print(json.dumps(results, indent=2))

    if not results:
        print("no results -- catalog may have changed", file=sys.stderr)
        return 1

    recipe_id = results[0]["id"]

    print(f"\n== get_recipe({recipe_id!r}) ==")
    recipe = tools.get_recipe(recipe_id)
    print(json.dumps(recipe, indent=2))

    scaled_servings = recipe["servings"] * 3
    print(f"\n== scale_recipe({recipe_id!r}, servings={scaled_servings}) ==")
    scaled = tools.scale_recipe(recipe_id, scaled_servings)
    print(json.dumps(scaled["ingredients"], indent=2))

    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="call the tool handlers directly and print sample output, instead of starting the MCP server",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.demo:
        return run_demo()

    run_server()
    return 0


if __name__ == "__main__":
    sys.exit(main())
