from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Invite
from apps.recipes.models import Recipe
from django.contrib.auth.models import User

@login_required
def invite_create(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        invite_date = request.POST.get('invite_date')
        invite_time = request.POST.get('invite_time')
        
        recipient = get_object_or_404(User, pk=recipient_id)
        Invite.objects.create(
            sender=request.user,
            recipient=recipient,
            recipe=recipe,
            invite_date=invite_date,
            invite_time=invite_time
        )
        return redirect('invite_list')
    
    users = User.objects.exclude(pk=request.user.pk)
    return render(request, 'social/invite_create.html', {
        'recipe': recipe,
        'users': users
    })

@login_required
def invite_list(request):
    received = request.user.received_invites.filter(status='pending')
    sent = request.user.sent_invites.all()
    return render(request, 'social/invite_list.html', {
        'received_invites': received,
        'sent_invites': sent
    })

@login_required
def invite_respond(request, pk):
    invite = get_object_or_404(Invite, pk=pk, recipient=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            invite.status = 'accepted'
        elif action == 'decline':
            invite.status = 'declined'
        invite.save()
    return redirect('invite_list')

