import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.recipes.constants import COOKING_TECHNOLOGY_CHOICES, INGREDIENT_CHOICES
from apps.recipes.models import Recipe
from apps.recommendations.services import RecipeEmbeddingService

User = get_user_model()


@pytest.fixture
def user_factory(db):
    def make(username="testuser", password="testpass12345", **kwargs):
        return User.objects.create_user(username=username, password=password, **kwargs)

    return make


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def recipe_factory(db):
    def make(
        creator,
        title="Test Recipe",
        instructions="Mix everything together and cook.",
        servings=4,
        ingredients=None,
        time_minutes=30,
        cooking_technologies=None,
        dietary_tags=None,
        **kwargs,
    ):
        recipe = Recipe(
            creator=creator,
            title=title,
            instructions=instructions,
            servings=servings,
            ingredients=ingredients if ingredients is not None else list(INGREDIENT_CHOICES[:3]),
            time_minutes=time_minutes,
            cooking_technologies=(
                cooking_technologies if cooking_technologies is not None else [COOKING_TECHNOLOGY_CHOICES[0]]
            ),
            dietary_tags=dietary_tags if dietary_tags is not None else [],
            **kwargs,
        )
        recipe.embedding = RecipeEmbeddingService.create_embedding(recipe)
        recipe.save()
        return recipe

    return make


@pytest.fixture
def api_client_as(db):
    """Callable fixture: api_client_as(user) -> APIClient authenticated as that user
    via a DRF auth token (mirrors how a real client would authenticate)."""
    def make(user):
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    return make


@pytest.fixture
def api_client(user, api_client_as):
    return api_client_as(user)
