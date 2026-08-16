"""search_recipes: find recipe summaries by free-text query, tag, and/or a
prep-time ceiling. Handler logic is tested directly (no MCP transport)."""

import pytest

from mcp_tool_server.tools import search_recipes


def test_no_filters_returns_every_recipe():
    results = search_recipes()
    assert len(results) >= 10
    # summaries, not full recipes -- no steps/ingredients leaking through
    for r in results:
        assert set(r.keys()) == {"id", "title", "tags", "prep_minutes", "servings"}


def test_query_matches_title_case_insensitively():
    results = search_recipes(query="PIZZA")
    assert any(r["id"] == "classic-margherita-pizza" for r in results)
    assert all("pizza" in r["title"].lower() for r in results)


def test_query_matches_ingredient_name():
    results = search_recipes(query="chickpeas")
    ids = {r["id"] for r in results}
    assert "lemon-garlic-roasted-chickpeas" in ids
    assert "coconut-curry-vegetables" in ids


def test_tag_filter_is_exact_and_case_insensitive():
    results = search_recipes(tag="VEGAN")
    assert results
    assert all("vegan" in r["tags"] for r in results)


def test_max_prep_minutes_filters_out_slower_recipes():
    results = search_recipes(max_prep_minutes=15)
    assert results
    assert all(r["prep_minutes"] <= 15 for r in results)


def test_combined_filters_are_ANDed():
    results = search_recipes(tag="vegetarian", max_prep_minutes=10)
    assert all(r["prep_minutes"] <= 10 and "vegetarian" in r["tags"] for r in results)


def test_no_matches_returns_empty_list():
    assert search_recipes(query="nonexistent-ingredient-xyz") == []


def test_results_sorted_by_prep_minutes_then_title():
    results = search_recipes()
    keys = [(r["prep_minutes"], r["title"]) for r in results]
    assert keys == sorted(keys)


def test_unknown_tag_raises_value_error():
    with pytest.raises(ValueError):
        search_recipes(tag="not-a-real-tag")
