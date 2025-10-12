from django.db.models import Q, Count
from .models import Recipe

# TODO: Revise this to return only recipes that user all or a subset of the available recipes
class RecipeSearchService:
    @classmethod
    def search_recipes(cls, ingredients=None, max_time=None, cooking_technologies=None, user=None):
        queryset = Recipe.objects.all()
        
        if ingredients:
            # Filter recipes that contain ANY of the specified ingredients
            ingredient_q = Q()
            for ingredient in ingredients:
                ingredient_q |= Q(ingredients__icontains=ingredient)
            queryset = queryset.filter(ingredient_q)
        
        if max_time:
            queryset = queryset.filter(time_minutes__lte=max_time)
        
        if cooking_technologies:
            # Filter recipes that can be made with available technologies
            tech_q = Q()
            for tech in cooking_technologies:
                tech_q |= Q(cooking_technologies__contains=tech)
            queryset = queryset.filter(tech_q)
        
        return queryset.annotate(
            like_count=Count('recipelike')
        ).order_by('-like_count', '-created_at')