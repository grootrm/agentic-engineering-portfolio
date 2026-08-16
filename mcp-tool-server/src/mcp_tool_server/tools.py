"""Handler logic for the recipe-box MCP tools.

These are plain functions operating on the synthetic catalog in
``mcp_tool_server.catalog``. They contain no MCP-protocol code at all --
``server.py`` is a thin adapter that registers each of these as an MCP tool.
Keeping the logic here (rather than inline in decorated functions) is what
lets the test suite exercise it directly, without spinning up a server or
speaking the MCP transport.
"""

from __future__ import annotations

from mcp_tool_server.catalog import RECIPES
from mcp_tool_server.errors import UnknownTagError

_ALL_TAGS = {tag for recipe in RECIPES for tag in recipe["tags"]}

_SUMMARY_FIELDS = ("id", "title", "tags", "prep_minutes", "servings")


def _summary(recipe: dict) -> dict:
    return {field: recipe[field] for field in _SUMMARY_FIELDS}


def search_recipes(
    query: str = "",
    tag: str | None = None,
    max_prep_minutes: int | None = None,
) -> list[dict]:
    """Search the recipe catalog by free-text query, tag, and/or prep time.

    Args:
        query: Case-insensitive substring matched against the recipe title
            and its ingredient names. Empty string matches everything.
        tag: Exact tag to filter by (case-insensitive). Raises
            ``UnknownTagError`` if the tag doesn't exist in the catalog, so
            a caller gets a clear signal rather than a silent empty result.
        max_prep_minutes: If given, only recipes with ``prep_minutes`` at
            or below this ceiling are returned.

    Returns:
        A list of recipe summaries (id, title, tags, prep_minutes,
        servings -- no ingredients/steps), sorted by prep_minutes then
        title.
    """
    if tag is not None and tag.lower() not in _ALL_TAGS:
        raise UnknownTagError(tag)

    normalized_query = query.strip().lower()

    def matches(recipe: dict) -> bool:
        if normalized_query:
            title_hit = normalized_query in recipe["title"].lower()
            ingredient_hit = any(
                normalized_query in ing["name"].lower() for ing in recipe["ingredients"]
            )
            if not (title_hit or ingredient_hit):
                return False
        if tag is not None and tag.lower() not in recipe["tags"]:
            return False
        if max_prep_minutes is not None and recipe["prep_minutes"] > max_prep_minutes:
            return False
        return True

    results = [_summary(r) for r in RECIPES if matches(r)]
    results.sort(key=lambda r: (r["prep_minutes"], r["title"]))
    return results
