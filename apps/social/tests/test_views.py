import pytest
from django.urls import reverse

from apps.accounts.models import Friendship
from apps.social.models import DinnerEvent, EventDish, EventInvite


@pytest.mark.django_db
class TestEventCreate:
    def test_get_context_includes_friend_ids_and_own_recipes(self, client, user_factory, recipe_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        stranger = user_factory(username='stranger')
        own_recipe = recipe_factory(creator=owner)
        Friendship.objects.create(user1=owner, user2=buddy)

        client.force_login(owner)
        response = client.get(reverse('event_create'))

        assert response.context['friend_ids'] == {buddy.pk}
        users = list(response.context['users'])
        assert buddy in users
        assert stranger in users
        assert owner not in users
        assert own_recipe in list(response.context['recipes'])

    def test_post_creates_event_with_dishes_and_invites(self, client, user_factory, recipe_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        stranger = user_factory(username='stranger')
        recipe = recipe_factory(creator=owner)

        client.force_login(owner)
        response = client.post(reverse('event_create'), {
            'title': 'Friendsgiving',
            'date': '2026-08-01',
            'time': '18:30',
            'location': "Owner's place",
            'recipes': [recipe.pk],
            'recipients': [buddy.pk, stranger.pk],
        })

        event = DinnerEvent.objects.get(host=owner, title='Friendsgiving')
        assert response.status_code == 302
        assert response.url == reverse('event_detail', args=[event.pk])
        assert event.location == "Owner's place"
        assert EventDish.objects.filter(event=event, recipe=recipe).exists()
        assert EventInvite.objects.filter(event=event, recipient=buddy).exists()
        assert EventInvite.objects.filter(event=event, recipient=stranger).exists()

    def test_duplicate_recipient_in_same_submission_does_not_duplicate_invite(
        self, client, user_factory
    ):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        client.force_login(owner)

        client.post(reverse('event_create'), {
            'title': 'Dinner',
            'date': '2026-08-01',
            'time': '18:30',
            # Duplicate value, e.g. from a malformed/replayed form submission.
            'recipients': [buddy.pk, buddy.pk],
        })

        event = DinnerEvent.objects.get(host=owner, title='Dinner')
        assert EventInvite.objects.filter(event=event, recipient=buddy).count() == 1


@pytest.mark.django_db
class TestEventList:
    def test_splits_hosting_and_invited(self, client, user_factory):
        owner = user_factory(username='owner')
        other = user_factory(username='other')
        hosted = DinnerEvent.objects.create(host=owner, title='Hosted', date='2026-08-01', time='18:00')
        invited_event = DinnerEvent.objects.create(host=other, title='Invited', date='2026-08-02', time='19:00')
        invite = EventInvite.objects.create(event=invited_event, recipient=owner)

        client.force_login(owner)
        response = client.get(reverse('event_list'))

        assert list(response.context['hosting']) == [hosted]
        assert list(response.context['invited']) == [invite]


@pytest.mark.django_db
class TestEventDetail:
    def test_host_can_view(self, client, user):
        event = DinnerEvent.objects.create(host=user, title='Dinner', date='2026-08-01', time='18:00')
        client.force_login(user)

        response = client.get(reverse('event_detail', args=[event.pk]))

        assert response.status_code == 200

    def test_invited_guest_can_view(self, client, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        EventInvite.objects.create(event=event, recipient=guest)

        client.force_login(guest)
        response = client.get(reverse('event_detail', args=[event.pk]))

        assert response.status_code == 200

    def test_uninvited_stranger_gets_404(self, client, user_factory):
        host = user_factory(username='host')
        stranger = user_factory(username='stranger')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')

        client.force_login(stranger)
        response = client.get(reverse('event_detail', args=[event.pk]))

        assert response.status_code == 404

    def test_shows_dishes_and_accepted_guests(self, client, user_factory, recipe_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        recipe = recipe_factory(creator=host, title='Chili')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        EventDish.objects.create(event=event, recipe=recipe)
        EventInvite.objects.create(event=event, recipient=guest, status=EventInvite.Status.ACCEPTED)

        client.force_login(host)
        response = client.get(reverse('event_detail', args=[event.pk]))

        assert recipe in [dish.recipe for dish in response.context['dishes']]
        assert guest in [invite.recipient for invite in response.context['accepted_guests']]


@pytest.mark.django_db
class TestEventDishClaim:
    def test_guest_can_claim_unclaimed_dish(self, client, user_factory, recipe_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        recipe = recipe_factory(creator=host)
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        dish = EventDish.objects.create(event=event, recipe=recipe)
        EventInvite.objects.create(event=event, recipient=guest)

        client.force_login(guest)
        response = client.post(reverse('event_dish_claim', args=[dish.pk]))

        dish.refresh_from_db()
        assert response.status_code == 302
        assert dish.claimed_by == guest

    def test_claiming_already_claimed_dish_is_a_noop(self, client, user_factory, recipe_factory):
        host = user_factory(username='host')
        guest1 = user_factory(username='guest1')
        guest2 = user_factory(username='guest2')
        recipe = recipe_factory(creator=host)
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        dish = EventDish.objects.create(event=event, recipe=recipe, claimed_by=guest1)
        EventInvite.objects.create(event=event, recipient=guest2)

        client.force_login(guest2)
        client.post(reverse('event_dish_claim', args=[dish.pk]))

        dish.refresh_from_db()
        assert dish.claimed_by == guest1

    def test_claimant_can_unclaim(self, client, user_factory, recipe_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        recipe = recipe_factory(creator=host)
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        dish = EventDish.objects.create(event=event, recipe=recipe, claimed_by=guest)
        EventInvite.objects.create(event=event, recipient=guest)

        client.force_login(guest)
        client.post(reverse('event_dish_claim', args=[dish.pk]))

        dish.refresh_from_db()
        assert dish.claimed_by is None


@pytest.mark.django_db
class TestEventRespond:
    def test_recipient_can_accept(self, client, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        invite = EventInvite.objects.create(event=event, recipient=guest)

        client.force_login(guest)
        response = client.post(reverse('event_respond', args=[event.pk]), {'action': 'accept'})

        invite.refresh_from_db()
        assert response.status_code == 302
        assert invite.status == EventInvite.Status.ACCEPTED
        assert invite.responded_at is not None

    def test_recipient_can_decline(self, client, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        invite = EventInvite.objects.create(event=event, recipient=guest)

        client.force_login(guest)
        client.post(reverse('event_respond', args=[event.pk]), {'action': 'decline'})

        invite.refresh_from_db()
        assert invite.status == EventInvite.Status.DECLINED

    def test_non_recipient_gets_404(self, client, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        stranger = user_factory(username='stranger')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        EventInvite.objects.create(event=event, recipient=guest)

        client.force_login(stranger)
        response = client.post(reverse('event_respond', args=[event.pk]), {'action': 'accept'})

        assert response.status_code == 404


@pytest.mark.django_db
class TestEventIcs:
    def test_returns_calendar_file_for_host(self, client, user):
        event = DinnerEvent.objects.create(
            host=user, title='Dinner Party', date='2026-08-01', time='18:00', location='Home'
        )
        client.force_login(user)

        response = client.get(reverse('event_ics', args=[event.pk]))

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/calendar'
        body = response.content.decode()
        assert 'BEGIN:VEVENT' in body
        assert 'SUMMARY:Dinner Party' in body
        assert 'DTSTART:20260801T180000' in body

    def test_uninvited_stranger_gets_404(self, client, user_factory):
        host = user_factory(username='host')
        stranger = user_factory(username='stranger')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')

        client.force_login(stranger)
        response = client.get(reverse('event_ics', args=[event.pk]))

        assert response.status_code == 404
