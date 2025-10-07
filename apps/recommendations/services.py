import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from apps.recipes.models import Recipe

MAX_COOK_TIME = settings.MAX_COOK_TIME

class RecipeEmbeddingService:
    INGREDIENTS_LIST = [f"Ing_{i}" for i in range(20)]  # Your predefined ingredients
    COOKING_TECH = ["Oven", "Grill", "Microwave"]
    
    @classmethod
    def create_embedding(cls, recipe):
        """Convert recipe to vector embedding"""
        vector = np.zeros(len(cls.INGREDIENTS_LIST) + len(cls.COOKING_TECH) + 1)  # +1 for time
        
        # Ingredient encoding (binary or TF-IDF)
        recipe_ingredients = set([ing.lower() for ing in recipe.ingredients])
        for i, ingredient in enumerate(cls.INGREDIENTS_LIST):
            if ingredient.lower() in recipe_ingredients:
                vector[i] = 1
        
        # Cooking technology encoding
        tech_offset = len(cls.INGREDIENTS_LIST)
        for i, tech in enumerate(cls.COOKING_TECH):
            if tech in recipe.cooking_technologies:
                vector[tech_offset + i] = 1
        
        # Time normalization (0-1 scale, assuming max MAX_COOK_TIME minutes)
        vector[-1] = min(recipe.time_minutes / MAX_COOK_TIME, 1.0)
        
        return vector.tolist()
    
    @classmethod
    def find_similar_recipes(cls, target_recipe, limit=10):
        """Find similar recipes using cosine similarity"""
        target_vector = np.array(target_recipe.embedding).reshape(1, -1)
        
        # Get all recipes with embeddings
        recipes = Recipe.objects.exclude(id=target_recipe.id)
        
        similarities = []
        for recipe in recipes:
            recipe_vector = np.array(recipe.embedding).reshape(1, -1)
            similarity = cosine_similarity(target_vector, recipe_vector)[0][0]
            similarities.append((recipe, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [recipe for recipe, _ in similarities[:limit]]
