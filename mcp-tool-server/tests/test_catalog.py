"""The catalog is the synthetic dataset every tool operates over. Before any
tool logic exists, the data itself has to be well-formed: unique ids, sane
types, and every ingredient carrying a name/quantity/unit a scaler can do
arithmetic on."""

from mcp_tool_server.catalog import RECIPES


def test_catalog_is_nonempty():
    assert len(RECIPES) >= 10


def test_recipe_ids_are_unique():
    ids = [r["id"] for r in RECIPES]
    assert len(ids) == len(set(ids))


def test_every_recipe_has_required_fields():
    required = {"id", "title", "tags", "prep_minutes", "servings", "ingredients", "steps"}
    for recipe in RECIPES:
        missing = required - recipe.keys()
        assert not missing, f"{recipe.get('id')} missing fields: {missing}"


def test_every_recipe_has_positive_servings_and_prep_time():
    for recipe in RECIPES:
        assert recipe["servings"] > 0, recipe["id"]
        assert recipe["prep_minutes"] > 0, recipe["id"]


def test_every_ingredient_has_name_quantity_and_unit():
    for recipe in RECIPES:
        assert recipe["ingredients"], f"{recipe['id']} has no ingredients"
        for ingredient in recipe["ingredients"]:
            assert set(ingredient.keys()) == {"name", "quantity", "unit"}
            assert isinstance(ingredient["quantity"], (int, float))
            assert ingredient["quantity"] > 0


def test_every_recipe_has_at_least_one_tag_and_one_step():
    for recipe in RECIPES:
        assert recipe["tags"], recipe["id"]
        assert recipe["steps"], recipe["id"]
