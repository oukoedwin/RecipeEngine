from django.contrib.auth import get_user_model
from .models import Friendship

User = get_user_model()


class UserNotFound(Exception):
    """No user exists with the given username."""


class CannotAddSelf(Exception):
    """A user can't add themselves as a friend."""


class FriendshipService:
    """Business logic shared by the template views (apps/accounts/views.py) and the
    API views (apps/accounts/api_views.py).

    Raises typed exceptions instead of calling django.contrib.messages directly,
    since messages are web-only — the web view catches these and calls
    messages.error(...); an API view catches the same exceptions and returns a 400
    with a JSON error body.
    """

    @classmethod
    def add_friend(cls, owner, username):
        try:
            friend = User.objects.get(username=username)
        except User.DoesNotExist:
            raise UserNotFound(username)

        if friend == owner:
            raise CannotAddSelf()

        friendship, created = Friendship.objects.get_or_create(user1=owner, user2=friend)
        return friendship, created
