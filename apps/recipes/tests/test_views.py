import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.accounts.models import Friendship
from apps.recipes.constants import COOKING_TECHNOLOGY_CHOICES, INGREDIENT_CHOICES
from apps.recipes.models import Recipe, RecipeCollection, RecipeComment, RecipeLike, RecipeMade


@pytest.mark.django_db
class TestRecipeList:
    def test_requires_login(self, client):
        response = client.get(reverse('recipe_list'))
        assert response.status_code == 302

    def test_filters_by_ingredient(self, client, user, recipe_factory):
        client.force_login(user)
        matching = recipe_factory(creator=user, ingredients=['Chicken'])
        other = recipe_factory(creator=user, ingredients=['Spinach'])

        response = client.get(reverse('recipe_list'), {'ingredients': ['Chicken']})

        recipes = list(response.context['recipes'])
        assert matching in recipes
        assert other not in recipes

    def test_filters_by_max_time(self, client, user, recipe_factory):
        client.force_login(user)
        quick = recipe_factory(creator=user, time_minutes=10)
        slow = recipe_factory(creator=user, time_minutes=200)

        response = client.get(reverse('recipe_list'), {'max_time': 30})

        recipes = list(response.context['recipes'])
        assert quick in recipes
        assert slow not in recipes

    def test_friend_recommended_in_context(self, client, user_factory, recipe_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        recipe = recipe_factory(creator=buddy)
        RecipeLike.objects.create(user=buddy, recipe=recipe)
        Friendship.objects.create(user1=owner, user2=buddy)

        client.force_login(owner)
        response = client.get(reverse('recipe_list'))

        assert recipe in list(response.context['friend_recommended'])


@pytest.mark.django_db
class TestRecipeCreate:
    def test_requires_login(self, client):
        response = client.get(reverse('recipe_create'))
        assert response.status_code == 302

    def test_post_creates_recipe_with_embedding(self, client, user):
        client.force_login(user)

        response = client.post(reverse('recipe_create'), {
            'title': 'Test Recipe',
            'instructions': 'Mix everything together and cook.',
            'servings': 4,
            'ingredients': [INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[1]],
            'time_minutes': 45,
            'cooking_technologies': [COOKING_TECHNOLOGY_CHOICES[0]],
        })

        recipe = Recipe.objects.get(creator=user)
        assert response.status_code == 302
        assert response.url == reverse('recipe_detail', args=[recipe.pk])
        assert set(recipe.ingredients) == {INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[1]}
        assert len(recipe.embedding) == len(INGREDIENT_CHOICES) + len(COOKING_TECHNOLOGY_CHOICES) + 1
        assert any(v != 0 for v in recipe.embedding)


@pytest.mark.django_db
class TestRecipeDetail:
    def test_anonymous_access_allowed(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)

        response = client.get(reverse('recipe_detail', args=[recipe.pk]))

        assert response.status_code == 200
        assert response.context['user_has_liked'] is False

    def test_user_has_liked_reflects_actual_like(self, client, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        liker = user_factory(username='liker')
        recipe = recipe_factory(creator=creator)
        RecipeLike.objects.create(user=liker, recipe=recipe)

        client.force_login(liker)
        response = client.get(reverse('recipe_detail', args=[recipe.pk]))

        assert response.context['user_has_liked'] is True
        assert b'Unlike' in response.content

    def test_similar_recipes_present_in_context(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user, ingredients=['Chicken'])
        recipe_factory(creator=user, ingredients=['Chicken'])

        response = client.get(reverse('recipe_detail', args=[recipe.pk]))

        assert 'similar_recipes' in response.context


@pytest.mark.django_db
class TestRecipeEditDelete:
    def test_edit_requires_creator(self, client, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        other = user_factory(username='other')
        recipe = recipe_factory(creator=creator)

        client.force_login(other)
        response = client.get(reverse('recipe_edit', args=[recipe.pk]))

        assert response.status_code == 404

    def test_creator_can_edit(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user, time_minutes=20)
        client.force_login(user)

        response = client.post(reverse('recipe_edit', args=[recipe.pk]), {
            'title': recipe.title,
            'instructions': recipe.instructions,
            'servings': recipe.servings,
            'ingredients': [INGREDIENT_CHOICES[2]],
            'time_minutes': 99,
            'cooking_technologies': [],
        })

        recipe.refresh_from_db()
        assert response.status_code == 302
        assert recipe.time_minutes == 99
        assert recipe.ingredients == [INGREDIENT_CHOICES[2]]

    def test_delete_requires_creator(self, client, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        other = user_factory(username='other')
        recipe = recipe_factory(creator=creator)

        client.force_login(other)
        response = client.post(reverse('recipe_delete', args=[recipe.pk]))

        assert response.status_code == 404
        assert Recipe.objects.filter(pk=recipe.pk).exists()

    def test_creator_can_delete(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)
        client.force_login(user)

        response = client.post(reverse('recipe_delete', args=[recipe.pk]))

        assert response.status_code == 302
        assert not Recipe.objects.filter(pk=recipe.pk).exists()


@pytest.mark.django_db
class TestRecipeLike:
    def test_toggle_like_and_unlike(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)
        client.force_login(user)

        response = client.post(reverse('recipe_like', args=[recipe.pk]))
        assert response.json() == {'liked': True, 'like_count': 1}

        response = client.post(reverse('recipe_like', args=[recipe.pk]))
        assert response.json() == {'liked': False, 'like_count': 0}


@pytest.mark.django_db
class TestRecipeComment:
    def test_requires_login(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)
        response = client.post(reverse('recipe_comment_add', args=[recipe.pk]), {'body': 'Nice!'})
        assert response.status_code == 302
        assert not RecipeComment.objects.exists()

    def test_creates_comment_and_shows_on_detail(self, client, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        commenter = user_factory(username='commenter')
        recipe = recipe_factory(creator=creator)
        client.force_login(commenter)

        response = client.post(
            reverse('recipe_comment_add', args=[recipe.pk]), {'body': 'Loved it!'}, follow=True
        )

        assert RecipeComment.objects.filter(recipe=recipe, user=commenter, body='Loved it!').exists()
        assert b'Loved it!' in response.content

    def test_get_not_allowed(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)
        client.force_login(user)

        response = client.get(reverse('recipe_comment_add', args=[recipe.pk]))

        assert response.status_code == 405


@pytest.mark.django_db
class TestRecipeMade:
    def test_requires_login(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)
        response = client.get(reverse('recipe_made_add', args=[recipe.pk]))
        assert response.status_code == 302

    def test_creates_made_post_and_shows_on_detail(self, client, user_factory, recipe_factory):
        creator = user_factory(username='creator')
        cook = user_factory(username='cook')
        recipe = recipe_factory(creator=creator)
        client.force_login(cook)

        response = client.post(
            reverse('recipe_made_add', args=[recipe.pk]), {'note': 'Turned out great'}
        )

        assert response.status_code == 302
        assert RecipeMade.objects.filter(recipe=recipe, user=cook, note='Turned out great').exists()

        detail_response = client.get(reverse('recipe_detail', args=[recipe.pk]))
        assert b'Turned out great' in detail_response.content


@pytest.mark.django_db
class TestCollections:
    def test_list_only_shows_own_collections(self, client, user_factory):
        owner = user_factory(username='owner')
        other = user_factory(username='other')
        mine = RecipeCollection.objects.create(owner=owner, name='Mine')
        RecipeCollection.objects.create(owner=other, name='Theirs')

        client.force_login(owner)
        response = client.get(reverse('collection_list'))

        assert list(response.context['collections']) == [mine]

    def test_create_sets_owner(self, client, user):
        client.force_login(user)

        response = client.post(reverse('collection_create'), {'name': 'Friendsgiving'})

        collection = RecipeCollection.objects.get(name='Friendsgiving')
        assert response.status_code == 302
        assert collection.owner == user

    def test_detail_requires_owner(self, client, user_factory):
        owner = user_factory(username='owner')
        other = user_factory(username='other')
        collection = RecipeCollection.objects.create(owner=owner, name='Mine')

        client.force_login(other)
        response = client.get(reverse('collection_detail', args=[collection.pk]))

        assert response.status_code == 404

    def test_toggle_adds_then_removes_recipe(self, client, user, recipe_factory):
        recipe = recipe_factory(creator=user)
        collection = RecipeCollection.objects.create(owner=user, name='Mine')
        client.force_login(user)

        client.post(reverse('collection_toggle_recipe', args=[collection.pk]), {'recipe_id': recipe.pk})
        assert recipe in collection.recipes.all()

        client.post(reverse('collection_toggle_recipe', args=[collection.pk]), {'recipe_id': recipe.pk})
        assert recipe not in collection.recipes.all()


@pytest.mark.django_db
class TestPopularRecipes:
    def test_ordered_by_like_count(self, client, user_factory, recipe_factory):
        cache.clear()
        creator = user_factory(username='creator')
        liker1 = user_factory(username='liker1')
        liker2 = user_factory(username='liker2')

        popular = recipe_factory(creator=creator)
        unpopular = recipe_factory(creator=creator)
        RecipeLike.objects.create(user=liker1, recipe=popular)
        RecipeLike.objects.create(user=liker2, recipe=popular)

        response = client.get(reverse('popular_recipes'))

        recipes = list(response.context['recipes'])
        assert recipes.index(popular) < recipes.index(unpopular)
