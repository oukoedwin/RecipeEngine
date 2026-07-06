from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, Count
from .models import Recipe

# Postgres' own default threshold for the pg_trgm `%` similarity operator.
TITLE_SIMILARITY_THRESHOLD = 0.3


class RecipeSearchService:
    @classmethod
    def search_recipes(cls, query=None, ingredients=None, match_mode='any', max_time=None,
                        cooking_technologies=None, dietary_tags=None, sort='relevance', user=None):
        queryset = Recipe.objects.all()

        if query:
            # Fuzzy title search via Postgres trigram similarity (pg_trgm), enabled by
            # migration 0003. Tolerates typos in a recipe title in a way that isn't
            # possible for ingredients/tech/dietary tags anymore now that those are
            # fixed-vocabulary checkboxes rather than free text.
            queryset = queryset.annotate(
                title_similarity=TrigramSimilarity('title', query)
            ).filter(title_similarity__gt=TITLE_SIMILARITY_THRESHOLD)

        if ingredients:
            if match_mode == 'all':
                # Postgres jsonb containment (`@>`) on a *list* value checks the whole
                # sublist in one query, giving "recipe must have every specified
                # ingredient" semantics without an OR-loop.
                queryset = queryset.filter(ingredients__contains=list(ingredients))
            else:
                # Default: match ANY of the specified ingredients.
                ingredient_q = Q()
                for ingredient in ingredients:
                    ingredient_q |= Q(ingredients__contains=ingredient)
                queryset = queryset.filter(ingredient_q)

        if max_time:
            queryset = queryset.filter(time_minutes__lte=max_time)

        if cooking_technologies:
            tech_q = Q()
            for tech in cooking_technologies:
                tech_q |= Q(cooking_technologies__contains=tech)
            queryset = queryset.filter(tech_q)

        if dietary_tags:
            dietary_q = Q()
            for tag in dietary_tags:
                dietary_q |= Q(dietary_tags__contains=tag)
            queryset = queryset.filter(dietary_q)

        queryset = queryset.annotate(like_count=Count('recipelike', distinct=True))

        if sort == 'closest_match' and ingredients:
            return cls.rank_by_missing_ingredients(ingredients, queryset=queryset)
        if sort == 'newest':
            return queryset.order_by('-created_at')
        if sort == 'quickest':
            return queryset.order_by('time_minutes', '-like_count')
        return queryset.order_by('-like_count', '-created_at')

    @classmethod
    def rank_by_missing_ingredients(cls, available_ingredients, queryset=None):
        """Pantry-style "closest match" ranking: recipes needing the fewest additional
        ingredients come first, each annotated with a `.missing_ingredients` list.

        Done in Python, not SQL — ingredient sets are small (the fixed vocabulary is
        20 words) and recipe counts are modest, the same trade-off already accepted for
        RecipeEmbeddingService's brute-force cosine similarity.
        """
        if queryset is None:
            queryset = Recipe.objects.annotate(like_count=Count('recipelike', distinct=True))

        available = set(available_ingredients)
        ranked = []
        for recipe in queryset:
            recipe.missing_ingredients = sorted(set(recipe.ingredients) - available)
            ranked.append(recipe)

        ranked.sort(key=lambda r: (len(r.missing_ingredients), -r.like_count))
        return ranked
