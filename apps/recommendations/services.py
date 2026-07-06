import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.db.models import Count
from apps.recipes.models import Recipe, RecipeLike
from apps.recipes.constants import INGREDIENT_CHOICES, COOKING_TECHNOLOGY_CHOICES
from apps.accounts.models import Friendship

MAX_COOK_TIME = settings.MAX_COOK_TIME

class RecipeEmbeddingService:
    INGREDIENTS_LIST = INGREDIENT_CHOICES
    COOKING_TECH = COOKING_TECHNOLOGY_CHOICES
    
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
        """Find similar recipes using cosine similarity.

        The embedding is a small, mostly-binary vector (20 ingredient flags + 3 tech
        flags + normalized time), so exact cosine ties are common once there are more
        than a handful of recipes. Ties are broken by like count, then recency, so the
        result order is deterministic instead of falling back to whatever order the
        DB happens to return rows in.
        """
        target_vector = np.array(target_recipe.embedding).reshape(1, -1)
        target_dim = target_vector.shape[1]

        recipes = Recipe.objects.exclude(id=target_recipe.id).annotate(
            like_count=Count('recipelike')
        )

        similarities = []
        for recipe in recipes:
            # Recipes created outside the normal form flow (e.g. via /admin/) default
            # to an empty embedding; skip rather than crash cosine_similarity on a
            # shape mismatch.
            if len(recipe.embedding) != target_dim:
                continue
            recipe_vector = np.array(recipe.embedding).reshape(1, -1)
            similarity = cosine_similarity(target_vector, recipe_vector)[0][0]
            similarities.append((recipe, similarity))

        similarities.sort(key=lambda x: (x[1], x[0].like_count, x[0].created_at), reverse=True)
        return [recipe for recipe, _ in similarities[:limit]]


class FriendRecommendationService:
    """Recommends recipes liked by the user's friends.

    Deliberately simple: a direct aggregate over `Friendship` + `RecipeLike` rather
    than general user-user/item-item collaborative filtering. With a small friend
    graph, CF similarity scores are noisy and cold-start-prone; "what my friends
    liked" is a more honest use of the signal actually available. Revisit true CF
    once there's enough like volume for it to outperform this baseline.
    """

    @classmethod
    def recommend_for_user(cls, user, limit=10):
        friend_ids = list(
            Friendship.objects.filter(user1=user).values_list('user2_id', flat=True)
        )
        if not friend_ids:
            return Recipe.objects.none()

        already_liked_ids = RecipeLike.objects.filter(user=user).values_list('recipe_id', flat=True)

        return (
            Recipe.objects.filter(recipelike__user_id__in=friend_ids)
            .exclude(creator=user)
            .exclude(id__in=already_liked_ids)
            .annotate(friend_like_count=Count('recipelike', distinct=True))
            .order_by('-friend_like_count', '-created_at')[:limit]
        )
