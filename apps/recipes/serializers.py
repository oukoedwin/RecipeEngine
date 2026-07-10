from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .constants import COOKING_TECHNOLOGY_CHOICES, DIETARY_TAG_CHOICES, INGREDIENT_CHOICES
from .models import Recipe, RecipeCollection, RecipeComment, RecipeMade
from .services import RecipeService


def _choice_list_field(choices, **kwargs):
    return serializers.ListField(child=serializers.ChoiceField(choices=choices), **kwargs)


class RecipeCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RecipeComment
        fields = ['id', 'user', 'body', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class RecipeMadeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RecipeMade
        fields = ['id', 'user', 'photo', 'note', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class RecipeListSerializer(serializers.ModelSerializer):
    """Lightweight shape used for list/search results and nested "similar recipes"."""

    creator = UserSerializer(read_only=True)
    ingredients = _choice_list_field(INGREDIENT_CHOICES)
    cooking_technologies = _choice_list_field(COOKING_TECHNOLOGY_CHOICES, required=False)
    dietary_tags = _choice_list_field(DIETARY_TAG_CHOICES, required=False)
    like_count = serializers.SerializerMethodField()
    # Only present when the list was ranked by RecipeSearchService.rank_by_missing_ingredients.
    missing_ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'creator', 'servings', 'time_minutes',
            'ingredients', 'cooking_technologies', 'dietary_tags',
            'picture', 'like_count', 'missing_ingredients', 'created_at',
        ]
        read_only_fields = ['id', 'creator', 'like_count', 'missing_ingredients', 'created_at']

    def get_like_count(self, recipe) -> int:
        return recipe.recipelike_set.count()

    @extend_schema_field(serializers.ListField(child=serializers.CharField(), allow_null=True))
    def get_missing_ingredients(self, recipe):
        return getattr(recipe, 'missing_ingredients', None)


class RecipeDetailSerializer(RecipeListSerializer):
    user_has_liked = serializers.SerializerMethodField()
    similar_recipes = serializers.SerializerMethodField()
    comments = RecipeCommentSerializer(source='recipecomment_set', many=True, read_only=True)
    made_posts = RecipeMadeSerializer(source='recipemade_set', many=True, read_only=True)

    class Meta(RecipeListSerializer.Meta):
        fields = RecipeListSerializer.Meta.fields + [
            'instructions', 'user_has_liked', 'similar_recipes', 'comments', 'made_posts', 'updated_at',
        ]

    def get_user_has_liked(self, recipe) -> bool:
        request = self.context.get('request')
        return bool(request) and RecipeService.user_has_liked(recipe, request.user)

    @extend_schema_field(RecipeListSerializer(many=True))
    def get_similar_recipes(self, recipe):
        from apps.recommendations.services import RecipeEmbeddingService

        similar = RecipeEmbeddingService.find_similar_recipes(recipe, limit=5)
        return RecipeListSerializer(similar, many=True, context=self.context).data


class RecipeCollectionSerializer(serializers.ModelSerializer):
    recipes = RecipeListSerializer(many=True, read_only=True)

    class Meta:
        model = RecipeCollection
        fields = ['id', 'name', 'recipes', 'created_at']
        read_only_fields = ['id', 'recipes', 'created_at']


class VocabularySerializer(serializers.Serializer):
    """Schema-only — describes VocabularyView's static response shape."""
    ingredients = serializers.ListField(child=serializers.CharField())
    cooking_technologies = serializers.ListField(child=serializers.CharField())
    dietary_tags = serializers.ListField(child=serializers.CharField())
