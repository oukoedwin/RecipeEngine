from django.urls import path
from . import api_views

urlpatterns = [
    path('register/', api_views.RegisterView.as_view(), name='api-register'),
    path('friends/', api_views.FriendListView.as_view(), name='api-friend-list'),
    path('friends/add/', api_views.FriendAddView.as_view(), name='api-friend-add'),
    path('friends/<int:pk>/remove/', api_views.FriendRemoveView.as_view(), name='api-friend-remove'),
]
