"""Exceptions raised by the recipe-box tool handlers."""


class RecipeNotFoundError(ValueError):
    """Raised when a recipe id doesn't exist in the catalog."""

    def __init__(self, recipe_id: str):
        self.recipe_id = recipe_id
        super().__init__(f"no recipe with id {recipe_id!r}")


class UnknownTagError(ValueError):
    """Raised when a tag filter doesn't match any tag in the catalog."""

    def __init__(self, tag: str):
        self.tag = tag
        super().__init__(f"unknown tag {tag!r}")
