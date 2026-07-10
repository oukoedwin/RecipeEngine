from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('recipes', api_views.RecipeViewSet, basename='api-recipe')
router.register('collections', api_views.RecipeCollectionViewSet, basename='api-collection')

urlpatterns = [
    path('vocabulary/', api_views.VocabularyView.as_view(), name='api-vocabulary'),
    path('', include(router.urls)),
]
