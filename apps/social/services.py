from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.recipes.models import Recipe
from .models import DinnerEvent, EventDish, EventInvite

User = get_user_model()


class EventService:
    """Business logic shared by the template views (apps/social/views.py) and the
    API views (apps/social/api_views.py)."""

    @classmethod
    def is_host_or_guest(cls, event, user):
        return event.host_id == user.pk or EventInvite.objects.filter(event=event, recipient=user).exists()

    @classmethod
    def create_event(cls, host, title, date, time, location, recipe_ids, recipient_ids):
        event = DinnerEvent.objects.create(
            host=host, title=title, date=date, time=time, location=location or '',
        )
        for recipe in Recipe.objects.filter(pk__in=recipe_ids):
            EventDish.objects.create(event=event, recipe=recipe)
        for recipient in User.objects.filter(pk__in=recipient_ids):
            EventInvite.objects.get_or_create(event=event, recipient=recipient)
        return event

    @classmethod
    def respond_to_invite(cls, invite, action):
        if action == 'accept':
            invite.status = EventInvite.Status.ACCEPTED
        elif action == 'decline':
            invite.status = EventInvite.Status.DECLINED
        invite.responded_at = timezone.now()
        invite.save()
        return invite

    @classmethod
    def toggle_dish_claim(cls, dish, user):
        """Claim an unclaimed dish, or unclaim one already claimed by `user`.
        Returns True if `dish` is now claimed by `user`, False otherwise (including
        the no-op case where it's already claimed by someone else)."""
        if dish.claimed_by_id == user.pk:
            dish.claimed_by = None
            dish.save()
            return False
        if dish.claimed_by_id is None:
            dish.claimed_by = user
            dish.save()
            return True
        return False

    @classmethod
    def generate_ics(cls, event):
        start = datetime.combine(event.date, event.time)
        end = start + timedelta(hours=2)
        fmt = '%Y%m%dT%H%M%S'
        return "\r\n".join([
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//RecipeEngine//DinnerEvent//EN",
            "BEGIN:VEVENT",
            f"UID:dinnerevent-{event.pk}@recipeengine",
            f"DTSTART:{start.strftime(fmt)}",
            f"DTEND:{end.strftime(fmt)}",
            f"SUMMARY:{event.title}",
            f"LOCATION:{event.location}",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ])
