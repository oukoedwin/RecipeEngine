import pytest
from django.urls import reverse

from apps.social.models import DinnerEvent, EventDish, EventInvite


@pytest.mark.django_db
class TestEventCreateApi:
    def test_creates_event_with_dishes_and_invites(
        self, api_client, user, user_factory, recipe_factory
    ):
        buddy = user_factory(username='buddy')
        recipe = recipe_factory(creator=user)

        response = api_client.post(reverse('api-event-list'), {
            'title': 'API Dinner',
            'date': '2026-08-01',
            'time': '18:30',
            'location': 'My place',
            'recipe_ids': [recipe.pk],
            'recipient_ids': [buddy.pk],
        }, format='json')

        assert response.status_code == 201
        event = DinnerEvent.objects.get(host=user, title='API Dinner')
        assert EventDish.objects.filter(event=event, recipe=recipe).exists()
        assert EventInvite.objects.filter(event=event, recipient=buddy).exists()
        assert len(response.data['dishes']) == 1

    def test_recipe_ids_and_recipient_ids_are_optional(self, api_client, user):
        response = api_client.post(reverse('api-event-list'), {
            'title': 'Dinner', 'date': '2026-08-01', 'time': '18:00',
        }, format='json')

        assert response.status_code == 201
        event = DinnerEvent.objects.get(host=user, title='Dinner')
        assert not EventDish.objects.filter(event=event).exists()
        assert not EventInvite.objects.filter(event=event).exists()


@pytest.mark.django_db
class TestEventDetailApi:
    def test_host_can_retrieve(self, api_client, user):
        event = DinnerEvent.objects.create(host=user, title='Dinner', date='2026-08-01', time='18:00')

        response = api_client.get(reverse('api-event-detail', args=[event.pk]))

        assert response.status_code == 200

    def test_uninvited_stranger_gets_404(self, api_client_as, user_factory):
        host = user_factory(username='host')
        stranger = user_factory(username='stranger')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')

        response = api_client_as(stranger).get(reverse('api-event-detail', args=[event.pk]))

        assert response.status_code == 404


@pytest.mark.django_db
class TestEventInvitedApi:
    def test_lists_events_user_is_invited_to(self, api_client_as, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        EventInvite.objects.create(event=event, recipient=guest)

        response = api_client_as(guest).get(reverse('api-event-invited'))

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['event']['title'] == 'Dinner'


@pytest.mark.django_db
class TestEventRespondApi:
    def test_recipient_can_accept(self, api_client_as, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        invite = EventInvite.objects.create(event=event, recipient=guest)

        response = api_client_as(guest).post(
            reverse('api-event-respond', args=[event.pk]), {'action': 'accept'}
        )

        invite.refresh_from_db()
        assert response.status_code == 200
        assert invite.status == EventInvite.Status.ACCEPTED

    def test_non_recipient_gets_404(self, api_client_as, user_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        stranger = user_factory(username='stranger')
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        EventInvite.objects.create(event=event, recipient=guest)

        response = api_client_as(stranger).post(
            reverse('api-event-respond', args=[event.pk]), {'action': 'accept'}
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestEventDishClaimApi:
    def test_guest_can_claim_unclaimed_dish(self, api_client_as, user_factory, recipe_factory):
        host = user_factory(username='host')
        guest = user_factory(username='guest')
        recipe = recipe_factory(creator=host)
        event = DinnerEvent.objects.create(host=host, title='Dinner', date='2026-08-01', time='18:00')
        dish = EventDish.objects.create(event=event, recipe=recipe)
        EventInvite.objects.create(event=event, recipient=guest)

        response = api_client_as(guest).post(reverse('api-dish-claim', args=[dish.pk]))

        dish.refresh_from_db()
        assert response.status_code == 200
        assert response.data == {'claimed': True}
        assert dish.claimed_by == guest


@pytest.mark.django_db
class TestEventIcsApi:
    def test_returns_calendar_for_host(self, api_client, user):
        event = DinnerEvent.objects.create(
            host=user, title='Dinner Party', date='2026-08-01', time='18:00', location='Home'
        )

        response = api_client.get(reverse('api-event-ics', args=[event.pk]))

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/calendar'
        assert b'BEGIN:VEVENT' in response.content
