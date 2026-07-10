import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import Friendship, User


@pytest.mark.django_db
class TestRegisterApi:
    def test_creates_user_and_returns_token(self):
        response = APIClient().post(reverse('api-register'), {
            'username': 'apinewuser', 'password1': 'a-strong-password-1', 'password2': 'a-strong-password-1',
        })

        assert response.status_code == 201
        assert 'token' in response.data
        assert User.objects.filter(username='apinewuser').exists()


@pytest.mark.django_db
class TestTokenAuth:
    def test_obtain_token_with_valid_credentials(self, user):
        response = APIClient().post(reverse('api-token-auth'), {
            'username': user.username, 'password': 'testpass12345',
        })

        assert response.status_code == 200
        assert 'token' in response.data


@pytest.mark.django_db
class TestFriendApi:
    def test_add_happy_path(self, api_client_as, user_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')

        response = api_client_as(owner).post(reverse('api-friend-add'), {'username': 'buddy'})

        assert response.status_code == 201
        assert Friendship.objects.filter(user1=owner, user2=buddy).exists()

    def test_add_unknown_username_returns_400(self, api_client_as, user_factory):
        owner = user_factory(username='owner')

        response = api_client_as(owner).post(reverse('api-friend-add'), {'username': 'ghost'})

        assert response.status_code == 400
        assert not Friendship.objects.exists()

    def test_list_scoped_to_owner(self, api_client_as, user_factory):
        owner = user_factory(username='owner')
        other_owner = user_factory(username='other_owner')
        buddy = user_factory(username='buddy')
        stranger_buddy = user_factory(username='stranger_buddy')
        Friendship.objects.create(user1=owner, user2=buddy)
        Friendship.objects.create(user1=other_owner, user2=stranger_buddy)

        response = api_client_as(owner).get(reverse('api-friend-list'))

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['friend']['username'] == 'buddy'

    def test_remove(self, api_client_as, user_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        friendship = Friendship.objects.create(user1=owner, user2=buddy)

        response = api_client_as(owner).delete(
            reverse('api-friend-remove', args=[friendship.pk])
        )

        assert response.status_code == 204
        assert not Friendship.objects.filter(pk=friendship.pk).exists()

    def test_requires_auth(self):
        response = APIClient().get(reverse('api-friend-list'))
        assert response.status_code == 401
