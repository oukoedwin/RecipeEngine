from django.db import models

class Invite(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    invite_date = models.DateField()
    invite_time = models.TimeField()
    status = models.CharField(max_choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
