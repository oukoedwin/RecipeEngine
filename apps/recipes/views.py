from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from .models import Recipe, RecipeLike, RecipeComment, RecipeMade, RecipeCollection
from .forms import (
    RecipeForm, RecipeSearchForm, RecipeCommentForm, RecipeMadeForm, RecipeCollectionForm,
)
from .services import RecipeSearchService
from apps.recommendations.services import RecipeEmbeddingService, FriendRecommendationService
from django.core.cache import cache

@login_required
def recipe_list(request):
    form = RecipeSearchForm(request.GET)
    recipes = Recipe.objects.all()

    if form.is_valid():
        recipes = RecipeSearchService.search_recipes(
            query=form.cleaned_data.get('query'),
            ingredients=form.cleaned_data.get('ingredients'),
            match_mode=form.cleaned_data.get('match_mode') or 'any',
            max_time=form.cleaned_data.get('max_time'),
            cooking_technologies=form.cleaned_data.get('cooking_technologies'),
            dietary_tags=form.cleaned_data.get('dietary_tags'),
            sort=form.cleaned_data.get('sort') or 'relevance',
        )

    friend_recommended = FriendRecommendationService.recommend_for_user(request.user, limit=5)

    return render(request, 'recipes/list.html', {
        'recipes': recipes,
        'form': form,
        'friend_recommended': friend_recommended,
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

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    user_has_liked = (
        request.user.is_authenticated
        and recipe.recipelike_set.filter(user=request.user).exists()
    )
    similar_recipes = RecipeEmbeddingService.find_similar_recipes(recipe, limit=5)
    user_collections = (
        RecipeCollection.objects.filter(owner=request.user)
        if request.user.is_authenticated else RecipeCollection.objects.none()
    )
    return render(request, 'recipes/detail.html', {
        'recipe': recipe,
        'user_has_liked': user_has_liked,
        'similar_recipes': similar_recipes,
        'comments': recipe.recipecomment_set.select_related('user'),
        'comment_form': RecipeCommentForm(),
        'made_posts': recipe.recipemade_set.select_related('user'),
        'made_form': RecipeMadeForm(),
        'user_collections': user_collections,
    })

@login_required
@require_http_methods(["POST"])
def recipe_comment_add(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    form = RecipeCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.recipe = recipe
        comment.user = request.user
        comment.save()
    return redirect('recipe_detail', pk=recipe.pk)

@login_required
def recipe_made_add(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = RecipeMadeForm(request.POST, request.FILES)
        if form.is_valid():
            made = form.save(commit=False)
            made.recipe = recipe
            made.user = request.user
            made.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeMadeForm()

    return render(request, 'recipes/made_add.html', {'form': form, 'recipe': recipe})

@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, creator=request.user)
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.embedding = RecipeEmbeddingService.create_embedding(recipe)
            recipe.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'recipes/edit.html', {'form': form, 'recipe': recipe})

@require_http_methods(["POST"])
@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, creator=request.user)
    recipe.delete()
    return redirect('recipe_list')

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


@login_required
def collection_list(request):
    collections = RecipeCollection.objects.filter(owner=request.user)
    return render(request, 'recipes/collection_list.html', {'collections': collections})

@login_required
def collection_create(request):
    if request.method == 'POST':
        form = RecipeCollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.owner = request.user
            collection.save()
            return redirect('collection_detail', pk=collection.pk)
    else:
        form = RecipeCollectionForm()

    return render(request, 'recipes/collection_create.html', {'form': form})

@login_required
def collection_detail(request, pk):
    collection = get_object_or_404(RecipeCollection, pk=pk, owner=request.user)
    return render(request, 'recipes/collection_detail.html', {'collection': collection})

@login_required
@require_http_methods(["POST"])
def collection_toggle_recipe(request, pk):
    """Add/remove the recipe named by POST['recipe_id'] from collection `pk`."""
    collection = get_object_or_404(RecipeCollection, pk=pk, owner=request.user)
    recipe = get_object_or_404(Recipe, pk=request.POST.get('recipe_id'))
    if collection.recipes.filter(pk=recipe.pk).exists():
        collection.recipes.remove(recipe)
    else:
        collection.recipes.add(recipe)
    return redirect('recipe_detail', pk=recipe.pk)