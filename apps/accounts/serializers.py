from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Friendship

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Minimal, read-only — used for nested display (creator, host, recipient, etc.)
    across every other app's serializers."""

    class Meta:
        model = User
        fields = ['id', 'username']


class FriendshipSerializer(serializers.ModelSerializer):
    friend = UserSerializer(source='user2', read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'friend', 'created_at']


# Schema-only serializers for the plain APIViews below (RegisterView, FriendAddView) —
# actual validation still goes through CustomUserCreationForm/FriendshipService; these
# exist purely so drf-spectacular can describe the request/response shape instead of
# silently dropping the endpoint from api/schema.yaml.
class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class FriendUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()
