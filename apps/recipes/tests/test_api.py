import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.recipes.constants import INGREDIENT_CHOICES
from apps.recipes.models import Recipe, RecipeCollection


@pytest.mark.django_db
class TestVocabularyApi:
    def test_returns_fixed_vocabularies(self):
        response = APIClient().get(reverse('api-vocabulary'))

        assert response.status_code == 200
        assert response.data['ingredients'] == INGREDIENT_CHOICES


@pytest.mark.django_db
class TestRecipeListApi:
    def test_requires_auth(self):
        response = APIClient().get(reverse('api-recipe-list'))
        assert response.status_code == 401

    def test_filters_by_ingredient(self, api_client, user, recipe_factory):
        matching = recipe_factory(creator=user, ingredients=['Chicken'])
        other = recipe_factory(creator=user, ingredients=['Spinach'])

        response = api_client.get(reverse('api-recipe-list'), {'ingredients': ['Chicken']})

        ids = [r['id'] for r in response.data]
        assert matching.pk in ids
        assert other.pk not in ids


@pytest.mark.django_db
class TestRecipeCreateApi:
    def test_creates_recipe_with_embedding(self, api_client, user):
        response = api_client.post(reverse('api-recipe-list'), {
            'title': 'API Test Recipe',
            'instructions': 'Mix and cook.',
            'servings': 4,
            'ingredients': [INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[1]],
            'time_minutes': 30,
            'cooking_technologies': [],
        }, format='json')

        assert response.status_code == 201
        recipe = Recipe.objects.get(pk=response.data['id'])
        assert recipe.creator == user
        assert any(v != 0 for v in recipe.embedding)


@pytest.mark.django_db
class TestRecipeDetailApi:
    def test_includes_instructions_and_user_has_liked(self, api_client, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        response = api_client.get(reverse('api-recipe-detail', args=[recipe.pk]))

        assert response.status_code == 200
        assert response.data['instructions'] == recipe.instructions
        assert response.data['user_has_liked'] is False

    def test_anonymous_can_retrieve(self, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        response = APIClient().get(reverse('api-recipe-detail', args=[recipe.pk]))

        assert response.status_code == 200


@pytest.mark.django_db
class TestRecipeEditApi:
    def test_non_creator_gets_404(self, api_client_as, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        other = user_factory(username='other')
        recipe = recipe_factory(creator=creator)

        response = api_client_as(other).patch(
            reverse('api-recipe-detail', args=[recipe.pk]), {'time_minutes': 99}, format='json'
        )

        assert response.status_code == 404

    def test_creator_can_update(self, api_client, user, recipe_factory):
        recipe = recipe_factory(creator=user, time_minutes=20)

        response = api_client.patch(
            reverse('api-recipe-detail', args=[recipe.pk]), {'time_minutes': 99}, format='json'
        )

        recipe.refresh_from_db()
        assert response.status_code == 200
        assert recipe.time_minutes == 99


@pytest.mark.django_db
class TestRecipeLikeApi:
    def test_toggle(self, api_client, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        response = api_client.post(reverse('api-recipe-like', args=[recipe.pk]))
        assert response.data == {'liked': True, 'like_count': 1}

        response = api_client.post(reverse('api-recipe-like', args=[recipe.pk]))
        assert response.data == {'liked': False, 'like_count': 0}


@pytest.mark.django_db
class TestRecipeCommentApi:
    def test_create_and_list(self, api_client, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        create_response = api_client.post(
            reverse('api-recipe-comments', args=[recipe.pk]), {'body': 'Delicious!'}
        )
        assert create_response.status_code == 201

        list_response = api_client.get(reverse('api-recipe-comments', args=[recipe.pk]))
        assert list_response.status_code == 200
        assert list_response.data[0]['body'] == 'Delicious!'


@pytest.mark.django_db
class TestCollectionApi:
    def test_create_and_toggle_recipe(self, api_client, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        create_response = api_client.post(reverse('api-collection-list'), {'name': 'Mine'})
        assert create_response.status_code == 201
        collection_id = create_response.data['id']

        toggle_response = api_client.post(
            reverse('api-collection-toggle-recipe', args=[collection_id]), {'recipe_id': recipe.pk}
        )
        assert toggle_response.status_code == 200
        assert toggle_response.data['included'] is True
        assert RecipeCollection.objects.get(pk=collection_id).recipes.filter(pk=recipe.pk).exists()

    def test_scoped_to_owner(self, api_client_as, user_factory):
        owner = user_factory(username='owner')
        other = user_factory(username='other')
        RecipeCollection.objects.create(owner=other, name='Not mine')

        response = api_client_as(owner).get(reverse('api-collection-list'))

        assert response.status_code == 200
        assert response.data == []
