import pytest
from django.db import IntegrityError

from apps.recipes.models import RecipeLike


@pytest.mark.django_db
def test_recipelike_unique_together(user, recipe_factory):
    recipe = recipe_factory(creator=user)
    RecipeLike.objects.create(user=user, recipe=recipe)

    with pytest.raises(IntegrityError):
        RecipeLike.objects.create(user=user, recipe=recipe)
