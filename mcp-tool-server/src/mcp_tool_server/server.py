"""MCP protocol adapter: registers the recipe-box handlers as MCP tools.

This module contains no business logic of its own -- every tool body is a
one-line call into ``mcp_tool_server.tools``, which is tested directly and
independently of this file. Keeping the split this way means the protocol
plumbing (this file) never needs its own behavioral tests; it's exercised
implicitly by running the server.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_tool_server import tools

mcp = FastMCP(
    name="recipe-box",
    instructions=(
        "Search, fetch, and scale recipes from a small synthetic recipe "
        "catalog. Use search_recipes to find candidates by free-text "
        "query, tag, or prep time; get_recipe to fetch full ingredients "
        "and steps; scale_recipe to adjust ingredient quantities to a "
        "different serving count."
    ),
)


@mcp.tool()
def search_recipes(
    query: str = "",
    tag: str | None = None,
    max_prep_minutes: int | None = None,
) -> list[dict]:
    """Search the recipe catalog by free-text query, tag, and/or a prep-time ceiling."""
    return tools.search_recipes(query=query, tag=tag, max_prep_minutes=max_prep_minutes)


@mcp.tool()
def get_recipe(recipe_id: str) -> dict:
    """Fetch a single recipe by id, including its ingredients and steps."""
    return tools.get_recipe(recipe_id)


@mcp.tool()
def scale_recipe(recipe_id: str, servings: int) -> dict:
    """Return a recipe with ingredient quantities scaled to a target serving count."""
    return tools.scale_recipe(recipe_id, servings)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
