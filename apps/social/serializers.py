from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.recipes.serializers import RecipeListSerializer
from .models import DinnerEvent, EventDish, EventInvite


class EventDishSerializer(serializers.ModelSerializer):
    recipe = RecipeListSerializer(read_only=True)
    claimed_by = UserSerializer(read_only=True)

    class Meta:
        model = EventDish
        fields = ['id', 'recipe', 'claimed_by']
        read_only_fields = fields


class EventInviteSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = EventInvite
        fields = ['id', 'recipient', 'status', 'created_at', 'responded_at']
        read_only_fields = fields


class DinnerEventSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    dishes = EventDishSerializer(many=True, read_only=True)
    accepted_guests = serializers.SerializerMethodField()
    user_invite = serializers.SerializerMethodField()
    # Not real model fields — consumed in DinnerEventViewSet.perform_create to build
    # the EventDish/EventInvite rows via EventService.create_event.
    recipe_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    recipient_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = DinnerEvent
        fields = [
            'id', 'host', 'title', 'date', 'time', 'location',
            'dishes', 'accepted_guests', 'user_invite',
            'recipe_ids', 'recipient_ids', 'created_at',
        ]
        read_only_fields = ['id', 'host', 'dishes', 'accepted_guests', 'user_invite', 'created_at']

    @extend_schema_field(UserSerializer(many=True))
    def get_accepted_guests(self, event):
        accepted = EventInvite.objects.filter(
            event=event, status=EventInvite.Status.ACCEPTED
        ).select_related('recipient')
        return UserSerializer([invite.recipient for invite in accepted], many=True).data

    @extend_schema_field(EventInviteSerializer(allow_null=True))
    def get_user_invite(self, event):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        invite = EventInvite.objects.filter(event=event, recipient=request.user).first()
        return EventInviteSerializer(invite).data if invite else None


class EventInviteWithEventSerializer(EventInviteSerializer):
    """Used for the "invited" listing, where the event is the point of interest —
    mirrors event_list's "Invited" section in the web app."""
    event = DinnerEventSerializer(read_only=True)

    class Meta(EventInviteSerializer.Meta):
        fields = EventInviteSerializer.Meta.fields + ['event']
        read_only_fields = fields


class DishClaimResponseSerializer(serializers.Serializer):
    """Schema-only — describes EventDishClaimView's response shape."""
    claimed = serializers.BooleanField()
