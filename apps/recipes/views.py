from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Recipe, RecipeCollection
from .forms import (
    RecipeForm, RecipeSearchForm, RecipeCommentForm, RecipeMadeForm, RecipeCollectionForm,
)
from .services import RecipeSearchService, RecipeService, CollectionService
from apps.recommendations.services import RecipeEmbeddingService, FriendRecommendationService

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
            RecipeService.finalize_and_save(recipe, creator=request.user)
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()

    return render(request, 'recipes/create.html', {'form': form})

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    user_has_liked = RecipeService.user_has_liked(recipe, request.user)
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
        RecipeService.add_comment(recipe, request.user, form.cleaned_data['body'])
    return redirect('recipe_detail', pk=recipe.pk)

@login_required
def recipe_made_add(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = RecipeMadeForm(request.POST, request.FILES)
        if form.is_valid():
            RecipeService.add_made_post(
                recipe, request.user,
                photo=form.cleaned_data.get('photo'),
                note=form.cleaned_data.get('note', ''),
            )
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
            RecipeService.finalize_and_save(recipe)
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
    liked, like_count = RecipeService.toggle_like(request.user, recipe)
    return JsonResponse({'liked': liked, 'like_count': like_count})


def popular_recipes(request):
    recipes = RecipeService.get_popular_recipes()
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
    CollectionService.toggle_recipe(collection, recipe)
    return redirect('recipe_detail', pk=recipe.pk)
