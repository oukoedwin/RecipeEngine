from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Recipe, RecipeLike
from .forms import RecipeForm, RecipeSearchForm # TODO
from .services import RecipeSearchService
from apps.recommendations.services import RecipeEmbeddingService
from django.core.cache import cache

@login_required
def recipe_list(request):
    form = RecipeSearchForm(request.GET)
    recipes = Recipe.objects.all()
    
    if form.is_valid():
        recipes = RecipeSearchService.search_recipes(
            ingredients=form.cleaned_data.get('ingredients'),
            max_time=form.cleaned_data.get('max_time'),
            cooking_technologies=form.cleaned_data.get('cooking_technologies')
        )
    
    return render(request, 'recipes/list.html', {
        'recipes': recipes,
        'form': form
    })

@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user
            recipe.embedding = RecipeEmbeddingService.create_embedding(recipe)
            recipe.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
    
    return render(request, 'recipes/create.html', {'form': form})

@require_http_methods(["POST"])
@login_required
def recipe_like(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    like, created = RecipeLike.objects.get_or_create(user=request.user, recipe=recipe)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({'liked': liked, 'like_count': recipe.recipelike_set.count()})


def popular_recipes(request):
    cache_key = 'popular_recipes'
    recipes = cache.get(cache_key)
    
    if recipes is None:
        recipes = Recipe.objects.annotate(
            like_count=Count('recipelike')
        ).order_by('-like_count')[:20]
        cache.set(cache_key, recipes, 3600)  # Cache for 1 hour
    
    return render(request, 'recipes/popular.html', {'recipes': recipes})