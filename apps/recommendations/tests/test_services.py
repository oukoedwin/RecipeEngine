import pytest
from django.conf import settings

from apps.accounts.models import Friendship
from apps.recipes.constants import COOKING_TECHNOLOGY_CHOICES, INGREDIENT_CHOICES
from apps.recipes.models import Recipe, RecipeLike
from apps.recommendations.services import FriendRecommendationService, RecipeEmbeddingService


@pytest.mark.django_db
class TestCreateEmbedding:
    def test_one_hot_positions_match_ingredients_and_tech(self, user, recipe_factory):
        recipe = recipe_factory(
            creator=user,
            ingredients=[INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[3]],
            cooking_technologies=[COOKING_TECHNOLOGY_CHOICES[1]],
            time_minutes=60,
        )

        embedding = recipe.embedding
        assert embedding[0] == 1
        assert embedding[3] == 1
        assert embedding[1] == 0

        tech_offset = len(INGREDIENT_CHOICES)
        assert embedding[tech_offset + 1] == 1
        assert embedding[tech_offset] == 0
        assert embedding[tech_offset + 2] == 0

        expected_time = min(60 / settings.MAX_COOK_TIME, 1.0)
        assert embedding[-1] == pytest.approx(expected_time)

    def test_time_normalization_clamps_at_max_cook_time(self, user, recipe_factory):
        recipe = recipe_factory(creator=user, time_minutes=int(settings.MAX_COOK_TIME) * 10)

        assert recipe.embedding[-1] == 1.0


@pytest.mark.django_db
class TestFindSimilarRecipes:
    def test_excludes_target_recipe(self, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        results = RecipeEmbeddingService.find_similar_recipes(recipe)

        assert recipe not in results

    def test_ties_broken_by_like_count_then_recency(self, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        liker = user_factory(username='liker')
        target = recipe_factory(creator=creator, ingredients=['Chicken'])
        # identical ingredients => identical embedding => cosine similarity tie
        less_liked = recipe_factory(creator=creator, ingredients=['Chicken'])
        more_liked = recipe_factory(creator=creator, ingredients=['Chicken'])
        RecipeLike.objects.create(user=liker, recipe=more_liked)

        results = RecipeEmbeddingService.find_similar_recipes(target)

        assert results.index(more_liked) < results.index(less_liked)

    def test_skips_recipes_with_mismatched_embedding_length(self, user, recipe_factory):
        target = recipe_factory(creator=user)
        # Simulates a recipe created outside the normal form flow (e.g. via /admin/),
        # which defaults to an empty embedding instead of a computed one.
        broken = Recipe.objects.create(
            creator=user, ingredients=['Chicken'], time_minutes=30, cooking_technologies=[],
        )
        assert broken.embedding == []

        results = RecipeEmbeddingService.find_similar_recipes(target)

        assert broken not in results


@pytest.mark.django_db
class TestFriendRecommendationService:
    def test_no_friends_returns_empty(self, user):
        results = FriendRecommendationService.recommend_for_user(user)

        assert list(results) == []

    def test_excludes_own_recipes_and_already_liked(self, user_factory, recipe_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        Friendship.objects.create(user1=owner, user2=buddy)

        own_recipe = recipe_factory(creator=owner)
        RecipeLike.objects.create(user=buddy, recipe=own_recipe)

        already_liked = recipe_factory(creator=buddy)
        RecipeLike.objects.create(user=buddy, recipe=already_liked)
        RecipeLike.objects.create(user=owner, recipe=already_liked)

        recommended = recipe_factory(creator=buddy)
        RecipeLike.objects.create(user=buddy, recipe=recommended)

        results = list(FriendRecommendationService.recommend_for_user(owner))

        assert own_recipe not in results
        assert already_liked not in results
        assert recommended in results

    def test_ranks_by_number_of_friends_who_liked(self, user_factory, recipe_factory):
        owner = user_factory(username='owner')
        buddy1 = user_factory(username='buddy1')
        buddy2 = user_factory(username='buddy2')
        Friendship.objects.create(user1=owner, user2=buddy1)
        Friendship.objects.create(user1=owner, user2=buddy2)

        popular = recipe_factory(creator=buddy1)
        unpopular = recipe_factory(creator=buddy1)
        RecipeLike.objects.create(user=buddy1, recipe=popular)
        RecipeLike.objects.create(user=buddy2, recipe=popular)
        RecipeLike.objects.create(user=buddy1, recipe=unpopular)

        results = list(FriendRecommendationService.recommend_for_user(owner))

        assert results.index(popular) < results.index(unpopular)
