from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DinnerEvent, EventDish, EventInvite
from .serializers import (
    DinnerEventSerializer, DishClaimResponseSerializer, EventInviteSerializer,
    EventInviteWithEventSerializer,
)
from .services import EventService


class DinnerEventViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """List/create/retrieve only — the web app has no event edit/delete view either."""
    # Static queryset (for schema introspection/basename) alongside the dynamic
    # get_queryset() below (for actual per-request scoping) — DRF supports both.
    queryset = DinnerEvent.objects.all()
    serializer_class = DinnerEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'retrieve':
            return DinnerEvent.objects.all()
        # 'list' = events the requesting user is hosting (mirrors event_list's
        # "Hosting" section); see the `invited` action for the other half.
        return DinnerEvent.objects.filter(host=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if not EventService.is_host_or_guest(obj, self.request.user):
            raise Http404
        return obj

    def perform_create(self, serializer):
        event = EventService.create_event(
            host=self.request.user,
            title=serializer.validated_data.get('title'),
            date=serializer.validated_data.get('date'),
            time=serializer.validated_data.get('time'),
            location=serializer.validated_data.get('location', ''),
            recipe_ids=serializer.validated_data.get('recipe_ids', []),
            recipient_ids=serializer.validated_data.get('recipient_ids', []),
        )
        serializer.instance = event

    @action(detail=False)
    def invited(self, request):
        invites = EventInvite.objects.filter(
            recipient=request.user
        ).select_related('event', 'event__host')
        serializer = EventInviteWithEventSerializer(invites, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        invite = get_object_or_404(EventInvite, event_id=pk, recipient=request.user)
        EventService.respond_to_invite(invite, request.data.get('action'))
        return Response(EventInviteSerializer(invite).data)

    @action(detail=True, methods=['get'])
    def ics(self, request, pk=None):
        event = self.get_object()
        response = HttpResponse(EventService.generate_ics(event), content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="event-{event.pk}.ics"'
        return response


class EventDishClaimView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=DishClaimResponseSerializer)
    def post(self, request, pk):
        dish = get_object_or_404(EventDish, pk=pk)
        if not EventService.is_host_or_guest(dish.event, request.user):
            raise Http404
        now_claimed = EventService.toggle_dish_claim(dish, request.user)
        return Response({'claimed': now_claimed})
