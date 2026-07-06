from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),
    path('recipe/popular/', views.popular_recipes, name='popular_recipes'),
    path('recipe/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipe/create/', views.recipe_create, name='recipe_create'),
    path('recipe/<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipe/<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('recipe/<int:pk>/like/', views.recipe_like, name='recipe_like'),
    path('recipe/<int:pk>/comment/', views.recipe_comment_add, name='recipe_comment_add'),
    path('recipe/<int:pk>/made/', views.recipe_made_add, name='recipe_made_add'),
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/create/', views.collection_create, name='collection_create'),
    path('collections/<int:pk>/', views.collection_detail, name='collection_detail'),
    path('collections/<int:pk>/toggle/', views.collection_toggle_recipe, name='collection_toggle_recipe'),
]