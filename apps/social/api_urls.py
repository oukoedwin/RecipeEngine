from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register('events', api_views.DinnerEventViewSet, basename='api-event')

urlpatterns = [
    path('dishes/<int:pk>/claim/', api_views.EventDishClaimView.as_view(), name='api-dish-claim'),
    path('', include(router.urls)),
]
