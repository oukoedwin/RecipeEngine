import pytest

from apps.recipes.constants import DIETARY_TAG_CHOICES, INGREDIENT_CHOICES
from apps.recipes.forms import RecipeForm


@pytest.mark.django_db
def test_rejects_ingredient_outside_fixed_vocabulary():
    form = RecipeForm(data={
        'ingredients': ['Not A Real Ingredient'],
        'time_minutes': 30,
        'cooking_technologies': [],
    })

    assert not form.is_valid()
    assert 'ingredients' in form.errors


@pytest.mark.django_db
def test_accepts_ingredients_from_fixed_vocabulary():
    form = RecipeForm(data={
        'title': 'Test Recipe',
        'instructions': 'Mix everything together and cook.',
        'servings': 4,
        'ingredients': [INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[1]],
        'time_minutes': 30,
        'cooking_technologies': [],
    })

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_requires_title_and_instructions():
    form = RecipeForm(data={
        'servings': 4,
        'ingredients': [INGREDIENT_CHOICES[0]],
        'time_minutes': 30,
        'cooking_technologies': [],
    })

    assert not form.is_valid()
    assert 'title' in form.errors
    assert 'instructions' in form.errors


@pytest.mark.django_db
def test_accepts_dietary_tags_from_fixed_vocabulary():
    form = RecipeForm(data={
        'title': 'Test Recipe',
        'instructions': 'Mix everything together and cook.',
        'servings': 4,
        'ingredients': [INGREDIENT_CHOICES[0]],
        'time_minutes': 30,
        'cooking_technologies': [],
        'dietary_tags': [DIETARY_TAG_CHOICES[0]],
    })

    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_edit_repopulates_ingredients_from_instance(user, recipe_factory):
    recipe = recipe_factory(
        creator=user,
        ingredients=[INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[1]],
    )

    form = RecipeForm(instance=recipe)

    assert set(form.initial['ingredients']) == {INGREDIENT_CHOICES[0], INGREDIENT_CHOICES[1]}
