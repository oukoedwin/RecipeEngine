from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.models import Friendship
from apps.recipes.models import Recipe
from .models import DinnerEvent, EventDish, EventInvite

User = get_user_model()


def _is_host_or_guest(event, user):
    return event.host_id == user.pk or EventInvite.objects.filter(event=event, recipient=user).exists()


@login_required
def event_create(request):
    if request.method == 'POST':
        recipe_ids = request.POST.getlist('recipes')
        recipient_ids = request.POST.getlist('recipients')

        event = DinnerEvent.objects.create(
            host=request.user,
            title=request.POST.get('title'),
            date=request.POST.get('date'),
            time=request.POST.get('time'),
            location=request.POST.get('location', ''),
        )
        for recipe in Recipe.objects.filter(pk__in=recipe_ids):
            EventDish.objects.create(event=event, recipe=recipe)
        for recipient in User.objects.filter(pk__in=recipient_ids):
            EventInvite.objects.get_or_create(event=event, recipient=recipient)

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
    if not _is_host_or_guest(event, request.user):
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
    action = request.POST.get('action')
    if action == 'accept':
        invite.status = EventInvite.Status.ACCEPTED
    elif action == 'decline':
        invite.status = EventInvite.Status.DECLINED
    invite.responded_at = timezone.now()
    invite.save()
    return redirect('event_detail', pk=pk)

@login_required
@require_http_methods(["POST"])
def event_dish_claim(request, pk):
    dish = get_object_or_404(EventDish, pk=pk)
    if not _is_host_or_guest(dish.event, request.user):
        raise Http404

    if dish.claimed_by_id == request.user.pk:
        dish.claimed_by = None
        dish.save()
    elif dish.claimed_by_id is None:
        dish.claimed_by = request.user
        dish.save()
    # else: already claimed by someone else — no-op.

    return redirect('event_detail', pk=dish.event_id)

@login_required
def event_ics(request, pk):
    event = get_object_or_404(DinnerEvent, pk=pk)
    if not _is_host_or_guest(event, request.user):
        raise Http404

    start = datetime.combine(event.date, event.time)
    end = start + timedelta(hours=2)
    fmt = '%Y%m%dT%H%M%S'
    ics_body = "\r\n".join([
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
    response = HttpResponse(ics_body, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="event-{event.pk}.ics"'
    return response
