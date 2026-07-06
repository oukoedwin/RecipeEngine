import pytest
from django.urls import reverse

from apps.accounts.models import Friendship, User


@pytest.mark.django_db
class TestRegister:
    def test_get_renders_form(self, client):
        response = client.get(reverse('register'))
        assert response.status_code == 200

    def test_post_creates_user_and_logs_in(self, client):
        response = client.post(reverse('register'), {
            'username': 'newperson',
            'password1': 'a-strong-password-1',
            'password2': 'a-strong-password-1',
        })

        assert response.status_code == 302
        assert response.url == reverse('recipe_list')
        assert User.objects.filter(username='newperson').exists()
        assert '_auth_user_id' in client.session


@pytest.mark.django_db
class TestFriendList:
    def test_only_shows_own_friendships(self, client, user_factory):
        owner = user_factory(username='owner')
        other_owner = user_factory(username='other_owner')
        buddy = user_factory(username='buddy')
        stranger_buddy = user_factory(username='stranger_buddy')

        Friendship.objects.create(user1=owner, user2=buddy)
        Friendship.objects.create(user1=other_owner, user2=stranger_buddy)

        client.force_login(owner)
        response = client.get(reverse('friend_list'))

        friendships = list(response.context['friendships'])
        assert len(friendships) == 1
        assert friendships[0].user2 == buddy

    def test_requires_login(self, client):
        response = client.get(reverse('friend_list'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestFriendAdd:
    def test_happy_path_creates_friendship(self, client, user_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        client.force_login(owner)

        response = client.post(reverse('friend_add'), {'username': 'buddy'}, follow=True)

        assert Friendship.objects.filter(user1=owner, user2=buddy).exists()
        messages = [str(m) for m in response.context['messages']]
        assert any('Added buddy as a friend' in m for m in messages)

    def test_unknown_username_shows_error_and_creates_nothing(self, client, user_factory):
        owner = user_factory(username='owner')
        client.force_login(owner)

        response = client.post(reverse('friend_add'), {'username': 'ghost'}, follow=True)

        assert not Friendship.objects.exists()
        messages = [str(m) for m in response.context['messages']]
        assert any('No user found' in m for m in messages)

    def test_self_add_rejected(self, client, user_factory):
        owner = user_factory(username='owner')
        client.force_login(owner)

        response = client.post(reverse('friend_add'), {'username': 'owner'}, follow=True)

        assert not Friendship.objects.exists()
        messages = [str(m) for m in response.context['messages']]
        assert any("can't add yourself" in m for m in messages)

    def test_duplicate_add_shows_info_and_does_not_duplicate(self, client, user_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        Friendship.objects.create(user1=owner, user2=buddy)
        client.force_login(owner)

        response = client.post(reverse('friend_add'), {'username': 'buddy'}, follow=True)

        assert Friendship.objects.filter(user1=owner, user2=buddy).count() == 1
        messages = [str(m) for m in response.context['messages']]
        assert any('already a friend' in m for m in messages)

    def test_requires_login(self, client):
        response = client.post(reverse('friend_add'), {'username': 'someone'})
        assert response.status_code == 302

    def test_get_not_allowed(self, client, user_factory):
        owner = user_factory(username='owner')
        client.force_login(owner)

        response = client.get(reverse('friend_add'))

        assert response.status_code == 405


@pytest.mark.django_db
class TestFriendRemove:
    def test_removes_own_friendship(self, client, user_factory):
        owner = user_factory(username='owner')
        buddy = user_factory(username='buddy')
        friendship = Friendship.objects.create(user1=owner, user2=buddy)
        client.force_login(owner)

        response = client.post(reverse('friend_remove', args=[friendship.pk]))

        assert response.status_code == 302
        assert not Friendship.objects.filter(pk=friendship.pk).exists()

    def test_cannot_remove_another_users_friendship(self, client, user_factory):
        owner = user_factory(username='owner')
        other = user_factory(username='other')
        buddy = user_factory(username='buddy')
        friendship = Friendship.objects.create(user1=other, user2=buddy)
        client.force_login(owner)

        response = client.post(reverse('friend_remove', args=[friendship.pk]))

        assert response.status_code == 404
        assert Friendship.objects.filter(pk=friendship.pk).exists()
