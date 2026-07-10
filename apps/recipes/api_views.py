from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import COOKING_TECHNOLOGY_CHOICES, DIETARY_TAG_CHOICES, INGREDIENT_CHOICES
from .models import Recipe, RecipeCollection
from .serializers import (
    RecipeCollectionSerializer, RecipeCommentSerializer, RecipeDetailSerializer,
    RecipeListSerializer, RecipeMadeSerializer, VocabularySerializer,
)
from .services import CollectionService, RecipeService, RecipeSearchService


class VocabularyView(APIView):
    """The fixed ingredient/cooking-tech/dietary-tag vocabularies, so a client builds
    its pickers from the server's list instead of hardcoding a copy that can drift."""
    permission_classes = [AllowAny]

    @extend_schema(responses=VocabularySerializer)
    def get(self, request):
        return Response({
            'ingredients': INGREDIENT_CHOICES,
            'cooking_technologies': COOKING_TECHNOLOGY_CHOICES,
            'dietary_tags': DIETARY_TAG_CHOICES,
        })


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'popular':
            return RecipeListSerializer
        return RecipeDetailSerializer

    def get_permissions(self):
        # Mirrors the web views: recipe_detail is public, everything else needs login.
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            # Creator-only, and 404 (not 403) for everyone else — mirrors
            # get_object_or_404(Recipe, pk=pk, creator=request.user) in views.py.
            user = self.request.user
            return Recipe.objects.filter(creator=user) if user.is_authenticated else Recipe.objects.none()
        if self.action == 'list':
            params = self.request.query_params
            return RecipeSearchService.search_recipes(
                query=params.get('query'),
                ingredients=params.getlist('ingredients') or None,
                match_mode=params.get('match_mode') or 'any',
                max_time=params.get('max_time'),
                cooking_technologies=params.getlist('cooking_technologies') or None,
                dietary_tags=params.getlist('dietary_tags') or None,
                sort=params.get('sort') or 'relevance',
            )
        return Recipe.objects.all()

    def perform_create(self, serializer):
        recipe = Recipe(**serializer.validated_data)
        RecipeService.finalize_and_save(recipe, creator=self.request.user)
        serializer.instance = recipe

    def perform_update(self, serializer):
        recipe = serializer.instance
        for attr, value in serializer.validated_data.items():
            setattr(recipe, attr, value)
        RecipeService.finalize_and_save(recipe)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        recipe = self.get_object()
        liked, like_count = RecipeService.toggle_like(request.user, recipe)
        return Response({'liked': liked, 'like_count': like_count})

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = RecipeCommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comment = RecipeService.add_comment(recipe, request.user, serializer.validated_data['body'])
            return Response(RecipeCommentSerializer(comment).data, status=201)
        comments = recipe.recipecomment_set.select_related('user')
        return Response(RecipeCommentSerializer(comments, many=True).data)

    @action(detail=True, methods=['get', 'post'])
    def made(self, request, pk=None):
        recipe = self.get_object()
        if request.method == 'POST':
            serializer = RecipeMadeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            made = RecipeService.add_made_post(
                recipe, request.user,
                photo=serializer.validated_data.get('photo'),
                note=serializer.validated_data.get('note', ''),
            )
            return Response(RecipeMadeSerializer(made).data, status=201)
        made_posts = recipe.recipemade_set.select_related('user')
        return Response(RecipeMadeSerializer(made_posts, many=True).data)

    @action(detail=False)
    def popular(self, request):
        recipes = RecipeService.get_popular_recipes()
        serializer = RecipeListSerializer(recipes, many=True, context={'request': request})
        return Response(serializer.data)


class RecipeCollectionViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """List/create/retrieve only — the web app has no collection rename/delete view,
    so the API doesn't expose one either (see collection_toggle_recipe for the one
    mutation collections do support)."""
    # Static queryset (for schema introspection/basename) alongside the dynamic
    # get_queryset() below (for actual per-request scoping) — DRF supports both.
    queryset = RecipeCollection.objects.all()
    serializer_class = RecipeCollectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecipeCollection.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_recipe(self, request, pk=None):
        collection = self.get_object()
        recipe = get_object_or_404(Recipe, pk=request.data.get('recipe_id'))
        included = CollectionService.toggle_recipe(collection, recipe)
        return Response({'recipe_id': recipe.pk, 'included': included})
