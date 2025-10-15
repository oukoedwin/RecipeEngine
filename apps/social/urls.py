from django.urls import path
from . import views

urlpatterns = [
    path('invites/', views.invite_list, name='invite_list'),
    path('invite/create/<int:recipe_pk>/', views.invite_create, name='invite_create'),
    path('invite/<int:pk>/respond/', views.invite_respond, name='invite_respond'),
]