from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.models import Friendship
from apps.recipes.models import Recipe
from .models import DinnerEvent, EventDish, EventInvite
from .services import EventService

User = get_user_model()


@login_required
def event_create(request):
    if request.method == 'POST':
        event = EventService.create_event(
            host=request.user,
            title=request.POST.get('title'),
            date=request.POST.get('date'),
            time=request.POST.get('time'),
            location=request.POST.get('location', ''),
            recipe_ids=request.POST.getlist('recipes'),
            recipient_ids=request.POST.getlist('recipients'),
        )
        return redirect('event_detail', pk=event.pk)

    users = User.objects.exclude(pk=request.user.pk)
    friend_ids = set(
        Friendship.objects.filter(user1=request.user).values_list('user2_id', flat=True)
    )
    recipes = Recipe.objects.filter(
        Q(creator=request.user) | Q(recipelike__user=request.user)
    ).distinct()
    return render(request, 'social/event_create.html', {
        'users': users,
        'friend_ids': friend_ids,
        'recipes': recipes,
    })

@login_required
def event_list(request):
    hosting = DinnerEvent.objects.filter(host=request.user)
    invited = EventInvite.objects.filter(recipient=request.user).select_related('event')
    return render(request, 'social/event_list.html', {
        'hosting': hosting,
        'invited': invited,
    })

@login_required
def event_detail(request, pk):
    event = get_object_or_404(DinnerEvent, pk=pk)
    if not EventService.is_host_or_guest(event, request.user):
        raise Http404

    dishes = event.dishes.select_related('recipe', 'claimed_by')
    accepted_guests = EventInvite.objects.filter(
        event=event, status=EventInvite.Status.ACCEPTED
    ).select_related('recipient')
    user_invite = EventInvite.objects.filter(event=event, recipient=request.user).first()
    return render(request, 'social/event_detail.html', {
        'event': event,
        'dishes': dishes,
        'accepted_guests': accepted_guests,
        'is_host': event.host_id == request.user.pk,
        'user_invite': user_invite,
    })

@login_required
@require_http_methods(["POST"])
def event_respond(request, pk):
    invite = get_object_or_404(EventInvite, event_id=pk, recipient=request.user)
    EventService.respond_to_invite(invite, request.POST.get('action'))
    return redirect('event_detail', pk=pk)

@login_required
@require_http_methods(["POST"])
def event_dish_claim(request, pk):
    dish = get_object_or_404(EventDish, pk=pk)
    if not EventService.is_host_or_guest(dish.event, request.user):
        raise Http404

    EventService.toggle_dish_claim(dish, request.user)
    return redirect('event_detail', pk=dish.event_id)

@login_required
def event_ics(request, pk):
    event = get_object_or_404(DinnerEvent, pk=pk)
    if not EventService.is_host_or_guest(event, request.user):
        raise Http404

    response = HttpResponse(EventService.generate_ics(event), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="event-{event.pk}.ics"'
    return response
