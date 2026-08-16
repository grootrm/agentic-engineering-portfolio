"""Synthetic recipe catalog.

Everything here -- recipe names, quantities, tags, and steps -- is invented
for this project. It is not derived from any real cookbook, business, or
proprietary dataset. It exists purely to give the MCP tools in
``mcp_tool_server.tools`` a small, deterministic, human-readable dataset to
operate over.

Each recipe is a plain dict (not a dataclass) so it serializes trivially to
JSON for MCP tool responses:

    {
        "id": str,                 unique slug
        "title": str,
        "tags": list[str],         lowercase, e.g. ["vegetarian", "quick"]
        "prep_minutes": int,       > 0
        "servings": int,           base yield the ingredient list is for
        "ingredients": [
            {"name": str, "quantity": float, "unit": str}, ...
        ],
        "steps": list[str],
    }
"""

from __future__ import annotations

RECIPES: list[dict] = [
    {
        "id": "tomato-lentil-soup",
        "title": "Tomato Lentil Soup",
        "tags": ["soup", "vegetarian", "vegan", "gluten-free"],
        "prep_minutes": 40,
        "servings": 4,
        "ingredients": [
            {"name": "red lentils", "quantity": 1.0, "unit": "cup"},
            {"name": "diced tomatoes", "quantity": 2.0, "unit": "cup"},
            {"name": "onion", "quantity": 1.0, "unit": "each"},
            {"name": "garlic", "quantity": 2.0, "unit": "clove"},
            {"name": "vegetable broth", "quantity": 4.0, "unit": "cup"},
            {"name": "cumin", "quantity": 1.0, "unit": "tsp"},
        ],
        "steps": [
            "Saute diced onion and garlic until soft.",
            "Add cumin and toast for 30 seconds.",
            "Add lentils, tomatoes, and broth; bring to a boil.",
            "Simmer 25 minutes until lentils are tender.",
        ],
    },
    {
        "id": "citrus-quinoa-salad",
        "title": "Citrus Quinoa Salad",
        "tags": ["salad", "vegetarian", "gluten-free", "quick"],
        "prep_minutes": 20,
        "servings": 4,
        "ingredients": [
            {"name": "quinoa", "quantity": 1.0, "unit": "cup"},
            {"name": "orange", "quantity": 2.0, "unit": "each"},
            {"name": "spinach", "quantity": 2.0, "unit": "cup"},
            {"name": "feta cheese", "quantity": 0.5, "unit": "cup"},
            {"name": "olive oil", "quantity": 2.0, "unit": "tbsp"},
        ],
        "steps": [
            "Cook quinoa according to package directions; cool slightly.",
            "Segment the oranges over a bowl to catch the juice.",
            "Toss quinoa, orange segments, spinach, and feta with olive oil and reserved juice.",
        ],
    },
    {
        "id": "weeknight-veggie-stirfry",
        "title": "Weeknight Veggie Stir-Fry",
        "tags": ["stir-fry", "vegetarian", "quick", "dinner"],
        "prep_minutes": 15,
        "servings": 2,
        "ingredients": [
            {"name": "broccoli", "quantity": 2.0, "unit": "cup"},
            {"name": "carrot", "quantity": 1.0, "unit": "each"},
            {"name": "bell pepper", "quantity": 1.0, "unit": "each"},
            {"name": "soy sauce", "quantity": 2.0, "unit": "tbsp"},
            {"name": "garlic", "quantity": 1.0, "unit": "clove"},
            {"name": "rice", "quantity": 1.0, "unit": "cup"},
        ],
        "steps": [
            "Cook rice separately.",
            "Stir-fry garlic, carrot, and bell pepper over high heat for 3 minutes.",
            "Add broccoli and soy sauce; cook 4 more minutes.",
            "Serve over rice.",
        ],
    },
    {
        "id": "banana-oat-pancakes",
        "title": "Banana Oat Pancakes",
        "tags": ["breakfast", "vegetarian", "quick"],
        "prep_minutes": 15,
        "servings": 2,
        "ingredients": [
            {"name": "rolled oats", "quantity": 1.0, "unit": "cup"},
            {"name": "banana", "quantity": 1.0, "unit": "each"},
            {"name": "egg", "quantity": 2.0, "unit": "each"},
            {"name": "milk", "quantity": 0.5, "unit": "cup"},
            {"name": "cinnamon", "quantity": 0.5, "unit": "tsp"},
        ],
        "steps": [
            "Blend oats to a coarse flour.",
            "Mash banana and whisk in egg, milk, and cinnamon.",
            "Stir in oat flour and cook spoonfuls on a hot griddle, 2 minutes per side.",
        ],
    },
    {
        "id": "roasted-vegetable-tray-bake",
        "title": "Roasted Vegetable Tray Bake",
        "tags": ["dinner", "vegetarian", "vegan", "gluten-free"],
        "prep_minutes": 45,
        "servings": 4,
        "ingredients": [
            {"name": "potato", "quantity": 4.0, "unit": "each"},
            {"name": "carrot", "quantity": 3.0, "unit": "each"},
            {"name": "red onion", "quantity": 1.0, "unit": "each"},
            {"name": "olive oil", "quantity": 3.0, "unit": "tbsp"},
            {"name": "rosemary", "quantity": 1.0, "unit": "tbsp"},
        ],
        "steps": [
            "Chop all vegetables into even chunks.",
            "Toss with olive oil and rosemary on a sheet pan.",
            "Roast at 425F for 35-40 minutes, stirring once.",
        ],
    },
    {
        "id": "chocolate-chip-cookies",
        "title": "Chocolate Chip Cookies",
        "tags": ["dessert", "vegetarian", "baking"],
        "prep_minutes": 30,
        "servings": 24,
        "ingredients": [
            {"name": "flour", "quantity": 2.25, "unit": "cup"},
            {"name": "butter", "quantity": 1.0, "unit": "cup"},
            {"name": "brown sugar", "quantity": 0.75, "unit": "cup"},
            {"name": "white sugar", "quantity": 0.75, "unit": "cup"},
            {"name": "egg", "quantity": 2.0, "unit": "each"},
            {"name": "chocolate chips", "quantity": 2.0, "unit": "cup"},
            {"name": "baking soda", "quantity": 1.0, "unit": "tsp"},
        ],
        "steps": [
            "Cream butter with both sugars.",
            "Beat in eggs, then mix in flour and baking soda.",
            "Fold in chocolate chips.",
            "Bake at 375F for 9-11 minutes per batch.",
        ],
    },
    {
        "id": "spicy-black-bean-tacos",
        "title": "Spicy Black Bean Tacos",
        "tags": ["dinner", "vegetarian", "vegan", "quick"],
        "prep_minutes": 20,
        "servings": 3,
        "ingredients": [
            {"name": "black beans", "quantity": 2.0, "unit": "cup"},
            {"name": "corn tortillas", "quantity": 6.0, "unit": "each"},
            {"name": "lime", "quantity": 1.0, "unit": "each"},
            {"name": "chili powder", "quantity": 1.0, "unit": "tsp"},
            {"name": "cilantro", "quantity": 0.25, "unit": "cup"},
            {"name": "red onion", "quantity": 0.5, "unit": "each"},
        ],
        "steps": [
            "Warm black beans with chili powder.",
            "Char tortillas briefly over a flame or dry skillet.",
            "Fill tortillas with beans, diced onion, cilantro, and a squeeze of lime.",
        ],
    },
    {
        "id": "creamy-mushroom-risotto",
        "title": "Creamy Mushroom Risotto",
        "tags": ["dinner", "vegetarian", "gluten-free"],
        "prep_minutes": 50,
        "servings": 4,
        "ingredients": [
            {"name": "arborio rice", "quantity": 1.5, "unit": "cup"},
            {"name": "mushroom", "quantity": 3.0, "unit": "cup"},
            {"name": "vegetable broth", "quantity": 5.0, "unit": "cup"},
            {"name": "parmesan cheese", "quantity": 0.75, "unit": "cup"},
            {"name": "onion", "quantity": 1.0, "unit": "each"},
            {"name": "butter", "quantity": 2.0, "unit": "tbsp"},
        ],
        "steps": [
            "Saute onion and mushrooms in butter until browned.",
            "Add rice and toast 1 minute.",
            "Add warm broth one ladle at a time, stirring until absorbed, about 25 minutes.",
            "Stir in parmesan off heat.",
        ],
    },
    {
        "id": "greek-yogurt-berry-parfait",
        "title": "Greek Yogurt Berry Parfait",
        "tags": ["breakfast", "vegetarian", "gluten-free", "quick"],
        "prep_minutes": 5,
        "servings": 1,
        "ingredients": [
            {"name": "greek yogurt", "quantity": 1.0, "unit": "cup"},
            {"name": "mixed berries", "quantity": 0.5, "unit": "cup"},
            {"name": "granola", "quantity": 0.25, "unit": "cup"},
            {"name": "honey", "quantity": 1.0, "unit": "tbsp"},
        ],
        "steps": [
            "Layer yogurt, berries, and granola in a glass.",
            "Drizzle with honey.",
        ],
    },
    {
        "id": "classic-margherita-pizza",
        "title": "Classic Margherita Pizza",
        "tags": ["dinner", "vegetarian", "baking"],
        "prep_minutes": 35,
        "servings": 4,
        "ingredients": [
            {"name": "pizza dough", "quantity": 1.0, "unit": "each"},
            {"name": "crushed tomatoes", "quantity": 0.75, "unit": "cup"},
            {"name": "mozzarella cheese", "quantity": 1.5, "unit": "cup"},
            {"name": "basil", "quantity": 0.25, "unit": "cup"},
            {"name": "olive oil", "quantity": 1.0, "unit": "tbsp"},
        ],
        "steps": [
            "Stretch dough onto a floured surface.",
            "Spread crushed tomatoes, leaving a border for the crust.",
            "Top with mozzarella and bake at 475F for 12-15 minutes.",
            "Finish with fresh basil and a drizzle of olive oil.",
        ],
    },
    {
        "id": "lemon-garlic-roasted-chickpeas",
        "title": "Lemon Garlic Roasted Chickpeas",
        "tags": ["snack", "vegetarian", "vegan", "gluten-free", "quick"],
        "prep_minutes": 30,
        "servings": 4,
        "ingredients": [
            {"name": "chickpeas", "quantity": 2.0, "unit": "cup"},
            {"name": "olive oil", "quantity": 2.0, "unit": "tbsp"},
            {"name": "lemon", "quantity": 1.0, "unit": "each"},
            {"name": "garlic", "quantity": 2.0, "unit": "clove"},
            {"name": "cumin", "quantity": 0.5, "unit": "tsp"},
        ],
        "steps": [
            "Toss dried chickpeas with olive oil, minced garlic, lemon zest, and cumin.",
            "Roast at 400F for 25 minutes, shaking the pan halfway through.",
        ],
    },
    {
        "id": "coconut-curry-vegetables",
        "title": "Coconut Curry Vegetables",
        "tags": ["dinner", "vegetarian", "vegan", "gluten-free"],
        "prep_minutes": 35,
        "servings": 4,
        "ingredients": [
            {"name": "coconut milk", "quantity": 1.0, "unit": "can"},
            {"name": "cauliflower", "quantity": 2.0, "unit": "cup"},
            {"name": "chickpeas", "quantity": 1.0, "unit": "cup"},
            {"name": "curry powder", "quantity": 2.0, "unit": "tbsp"},
            {"name": "onion", "quantity": 1.0, "unit": "each"},
            {"name": "rice", "quantity": 1.0, "unit": "cup"},
        ],
        "steps": [
            "Cook rice separately.",
            "Saute onion, then bloom curry powder for 1 minute.",
            "Add cauliflower, chickpeas, and coconut milk; simmer 20 minutes.",
            "Serve over rice.",
        ],
    },
]
