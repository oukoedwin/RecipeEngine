from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/respond/', views.event_respond, name='event_respond'),
    path('events/<int:pk>/ics/', views.event_ics, name='event_ics'),
    path('events/dish/<int:pk>/claim/', views.event_dish_claim, name='event_dish_claim'),
]
