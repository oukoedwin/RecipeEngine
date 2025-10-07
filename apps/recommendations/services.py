import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings

class RecipeEmbeddingService:
    INGREDIENTS_LIST = [f"Ing_{i}" for i in range(20)]  # Your predefined ingredients
    COOKING_TECH = ["Oven", "Grill", "Microwave"]
    
    @classmethod
    def create_embedding(cls, recipe):
        """Convert recipe to vector embedding"""
        vector = np.zeros(len(cls.INGREDIENTS_LIST) + len(cls.COOKING_TECH) + 1)  # +1 for time
        
        # Ingredient encoding (binary or TF-IDF)
        for i, ingredient in enumerate(cls.INGREDIENTS_LIST):
            if ingredient.lower() in [ing.lower() for ing in recipe.ingredients]:
                vector[i] = 1
        
        # Cooking technology encoding
        tech_offset = len(cls.INGREDIENTS_LIST)
        for i, tech in enumerate(cls.COOKING_TECH):
            if tech in recipe.cooking_technologies:
                vector[tech_offset + i] = 1
        
        # Time normalization (0-1 scale, assuming max 240 minutes)
        vector[-1] = min(recipe.time_minutes / 240.0, 1.0)
        
        return vector.tolist()
    
    @classmethod
    def find_similar_recipes(cls, target_recipe, limit=10):
        """Find similar recipes using cosine similarity"""
        target_vector = np.array(target_recipe.embedding).reshape(1, -1)
        
        # Get all recipes with embeddings
        recipes = Recipe.objects.exclude(id=target_recipe.id).exclude(embedding__exact=[])
        
        similarities = []
        for recipe in recipes:
            recipe_vector = np.array(recipe.embedding).reshape(1, -1)
            similarity = cosine_similarity(target_vector, recipe_vector)[0][0]
            similarities.append((recipe, similarity))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [recipe for recipe, _ in similarities[:limit]]
