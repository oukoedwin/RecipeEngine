# apps/accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('friends/', views.friend_list, name='friend_list'),
    path('friends/add/', views.friend_add, name='friend_add'),
    path('friends/<int:pk>/remove/', views.friend_remove, name='friend_remove'),
]