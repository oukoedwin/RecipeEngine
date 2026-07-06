# Controlled vocabulary shared by RecipeForm/RecipeSearchForm (apps/recipes/forms.py)
# and RecipeEmbeddingService (apps/recommendations/services.py), so the embedding
# always lines up with what a recipe can actually be tagged with.
# See notes.md: "Initially account for 20 ingredients, further ingredients may
# require more substantial change in schema."
INGREDIENT_CHOICES = [
    "Chicken", "Beef", "Pork", "Fish", "Shrimp",
    "Rice", "Pasta", "Potato", "Bread", "Tortilla",
    "Egg", "Cheese", "Milk", "Butter", "Olive Oil",
    "Tomato", "Onion", "Garlic", "Bell Pepper", "Spinach",
]

COOKING_TECHNOLOGY_CHOICES = ["Oven", "Grill", "Microwave"]

# Fixed vocabulary, same reasoning as INGREDIENT_CHOICES above: lets guests' dietary
# needs be filtered on directly instead of relying on free-text description.
DIETARY_TAG_CHOICES = [
    "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free", "Halal", "Kosher",
]
