# apps/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Friendship
from .forms import CustomUserCreationForm
from .services import FriendshipService, UserNotFound, CannotAddSelf

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('recipe_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def friend_list(request):
    friendships = Friendship.objects.filter(user1=request.user).select_related('user2')
    return render(request, 'accounts/friend_list.html', {
        'friendships': friendships,
    })

@login_required
@require_http_methods(["POST"])
def friend_add(request):
    username = request.POST.get('username', '').strip()
    try:
        friendship, created = FriendshipService.add_friend(request.user, username)
    except UserNotFound:
        messages.error(request, f"No user found with username '{username}'.")
        return redirect('friend_list')
    except CannotAddSelf:
        messages.error(request, "You can't add yourself as a friend.")
        return redirect('friend_list')

    if created:
        messages.success(request, f"Added {friendship.user2.username} as a friend.")
    else:
        messages.info(request, f"{friendship.user2.username} is already a friend.")
    return redirect('friend_list')

@login_required
@require_http_methods(["POST"])
def friend_remove(request, pk):
    friendship = get_object_or_404(Friendship, pk=pk, user1=request.user)
    friendship.delete()
    return redirect('friend_list')