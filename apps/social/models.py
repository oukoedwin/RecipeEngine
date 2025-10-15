from django.db import models
from django.contrib.auth.models import User
from apps.recipes.models import Recipe
from django.conf import settings

class Invite(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invites')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    invite_date = models.DateField()
    invite_time = models.TimeField()
    status = models.CharField(max_length=20, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
