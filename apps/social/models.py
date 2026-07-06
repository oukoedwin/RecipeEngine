from django.db import models
from django.conf import settings
from apps.recipes.models import Recipe


class DinnerEvent(models.Model):
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_events')
    title = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class EventDish(models.Model):
    event = models.ForeignKey(DinnerEvent, on_delete=models.CASCADE, related_name='dishes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    # null = up for grabs (potluck-style); set once someone claims it.
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )


class EventInvite(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'

    event = models.ForeignKey(DinnerEvent, on_delete=models.CASCADE, related_name='invites')
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_invites'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('event', 'recipient')
