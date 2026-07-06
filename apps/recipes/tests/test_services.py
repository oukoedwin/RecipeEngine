import pytest

from apps.recipes.services import RecipeSearchService


@pytest.mark.django_db
class TestRecipeSearchService:
    def test_matches_any_specified_ingredient_or_semantics(self, user, recipe_factory):
        """RecipeSearchService currently matches ANY ingredient (OR), not all/subset
        (there is a `# TODO` for that in services.py, tracked separately in PLAN.md).
        This test locks in the current behavior so it doesn't regress by accident."""
        has_first = recipe_factory(creator=user, ingredients=['Chicken'])
        has_second = recipe_factory(creator=user, ingredients=['Rice'])
        has_neither = recipe_factory(creator=user, ingredients=['Spinach'])

        results = RecipeSearchService.search_recipes(ingredients=['Chicken', 'Rice'])

        assert has_first in results
        assert has_second in results
        assert has_neither not in results

    def test_filters_by_max_time(self, user, recipe_factory):
        quick = recipe_factory(creator=user, time_minutes=10)
        slow = recipe_factory(creator=user, time_minutes=100)

        results = RecipeSearchService.search_recipes(max_time=30)

        assert quick in results
        assert slow not in results

    def test_filters_by_cooking_technologies(self, user, recipe_factory):
        oven = recipe_factory(creator=user, cooking_technologies=['Oven'])
        grill = recipe_factory(creator=user, cooking_technologies=['Grill'])

        results = RecipeSearchService.search_recipes(cooking_technologies=['Oven'])

        assert oven in results
        assert grill not in results

    def test_combined_filters(self, user, recipe_factory):
        match = recipe_factory(
            creator=user, ingredients=['Chicken'], time_minutes=15, cooking_technologies=['Oven']
        )
        wrong_time = recipe_factory(
            creator=user, ingredients=['Chicken'], time_minutes=150, cooking_technologies=['Oven']
        )

        results = RecipeSearchService.search_recipes(
            ingredients=['Chicken'], max_time=30, cooking_technologies=['Oven']
        )

        assert match in results
        assert wrong_time not in results

    def test_no_filters_returns_all(self, user, recipe_factory):
        a = recipe_factory(creator=user)
        b = recipe_factory(creator=user)

        results = RecipeSearchService.search_recipes()

        assert set(results) == {a, b}

    def test_no_matches_returns_empty(self, user, recipe_factory):
        recipe_factory(creator=user, ingredients=['Chicken'])

        results = RecipeSearchService.search_recipes(ingredients=['Spinach'])

        assert list(results) == []

    def test_match_mode_all_requires_every_ingredient(self, user, recipe_factory):
        has_both = recipe_factory(creator=user, ingredients=['Chicken', 'Rice'])
        has_only_one = recipe_factory(creator=user, ingredients=['Chicken'])

        results = RecipeSearchService.search_recipes(
            ingredients=['Chicken', 'Rice'], match_mode='all'
        )

        assert has_both in results
        assert has_only_one not in results

    def test_dietary_tag_filter_matches_any_tag(self, user, recipe_factory):
        vegetarian = recipe_factory(creator=user, dietary_tags=['Vegetarian'])
        vegan = recipe_factory(creator=user, dietary_tags=['Vegan'])
        neither = recipe_factory(creator=user, dietary_tags=[])

        results = RecipeSearchService.search_recipes(dietary_tags=['Vegetarian', 'Vegan'])

        assert vegetarian in results
        assert vegan in results
        assert neither not in results

    def test_fuzzy_title_search_tolerates_typo(self, user, recipe_factory):
        target = recipe_factory(creator=user, title='Spaghetti Carbonara')
        unrelated = recipe_factory(creator=user, title='Blueberry Pancakes')

        results = RecipeSearchService.search_recipes(query='Spagetti Carbonara')

        assert target in results
        assert unrelated not in results

    def test_sort_newest_orders_by_created_at_desc(self, user, recipe_factory):
        older = recipe_factory(creator=user)
        newer = recipe_factory(creator=user)

        results = list(RecipeSearchService.search_recipes(sort='newest'))

        assert results.index(newer) < results.index(older)

    def test_sort_quickest_orders_by_time_ascending(self, user, recipe_factory):
        slow = recipe_factory(creator=user, time_minutes=100)
        quick = recipe_factory(creator=user, time_minutes=10)

        results = list(RecipeSearchService.search_recipes(sort='quickest'))

        assert results.index(quick) < results.index(slow)


@pytest.mark.django_db
class TestRankByMissingIngredients:
    def test_orders_by_fewest_missing_ingredients(self, user, recipe_factory):
        exact = recipe_factory(creator=user, ingredients=['Chicken', 'Rice'])
        one_missing = recipe_factory(creator=user, ingredients=['Chicken', 'Rice', 'Onion'])
        two_missing = recipe_factory(creator=user, ingredients=['Chicken', 'Rice', 'Onion', 'Garlic'])

        results = RecipeSearchService.rank_by_missing_ingredients(['Chicken', 'Rice'])

        assert results.index(exact) < results.index(one_missing) < results.index(two_missing)
        # rank_by_missing_ingredients returns freshly-fetched instances (mutating them
        # in place), not the same Python objects the factory handed back — fetch by
        # position rather than asserting on the factory-returned references.
        assert results[results.index(exact)].missing_ingredients == []
        assert results[results.index(one_missing)].missing_ingredients == ['Onion']

    def test_closest_match_sort_wires_into_search_recipes(self, user, recipe_factory):
        exact = recipe_factory(creator=user, ingredients=['Chicken'])
        one_missing = recipe_factory(creator=user, ingredients=['Chicken', 'Onion'])

        results = RecipeSearchService.search_recipes(
            ingredients=['Chicken'], sort='closest_match'
        )

        assert results.index(exact) < results.index(one_missing)
