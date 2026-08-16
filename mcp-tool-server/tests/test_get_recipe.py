"""get_recipe / scale_recipe: fetch a single recipe by id, optionally scaled
to a target serving count. Handler logic is tested directly (no MCP
transport)."""

import pytest

from mcp_tool_server.errors import RecipeNotFoundError
from mcp_tool_server.tools import get_recipe, scale_recipe


def test_get_recipe_returns_full_recipe():
    recipe = get_recipe("tomato-lentil-soup")
    assert recipe["id"] == "tomato-lentil-soup"
    assert "ingredients" in recipe
    assert "steps" in recipe


def test_get_recipe_unknown_id_raises_recipe_not_found_error():
    with pytest.raises(RecipeNotFoundError):
        get_recipe("not-a-real-recipe")


def test_scale_recipe_doubles_quantities_when_servings_doubled():
    original = get_recipe("tomato-lentil-soup")
    scaled = scale_recipe("tomato-lentil-soup", original["servings"] * 2)

    assert scaled["servings"] == original["servings"] * 2
    for before, after in zip(original["ingredients"], scaled["ingredients"]):
        assert after["quantity"] == pytest.approx(before["quantity"] * 2)
        assert after["name"] == before["name"]
        assert after["unit"] == before["unit"]


def test_scale_recipe_to_same_servings_is_a_no_op():
    original = get_recipe("citrus-quinoa-salad")
    scaled = scale_recipe("citrus-quinoa-salad", original["servings"])
    assert scaled["ingredients"] == original["ingredients"]


def test_scale_recipe_does_not_mutate_the_catalog():
    before = get_recipe("banana-oat-pancakes")["ingredients"][0]["quantity"]
    scale_recipe("banana-oat-pancakes", 100)
    after = get_recipe("banana-oat-pancakes")["ingredients"][0]["quantity"]
    assert before == after


def test_scale_recipe_rejects_non_positive_servings():
    with pytest.raises(ValueError):
        scale_recipe("tomato-lentil-soup", 0)


def test_scale_recipe_unknown_id_raises_recipe_not_found_error():
    with pytest.raises(RecipeNotFoundError):
        scale_recipe("not-a-real-recipe", 4)
