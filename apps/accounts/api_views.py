from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CustomUserCreationForm
from .models import Friendship
from .serializers import FriendshipSerializer, FriendUsernameSerializer, RegisterRequestSerializer, TokenSerializer
from .services import FriendshipService, UserNotFound, CannotAddSelf


class RegisterView(APIView):
    """POST username/password -> creates the user and returns an auth token.
    (The web `register` view calls `login()` for a session instead — see
    apps/accounts/services.py for why that isn't a shared service method.)"""
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterRequestSerializer, responses=TokenSerializer)
    def post(self, request):
        form = CustomUserCreationForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        user = form.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)


class FriendListView(ListAPIView):
    serializer_class = FriendshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Friendship.objects.filter(user1=self.request.user).select_related('user2')


class FriendAddView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=FriendUsernameSerializer, responses=FriendshipSerializer)
    def post(self, request):
        username = request.data.get('username', '').strip()
        try:
            friendship, created = FriendshipService.add_friend(request.user, username)
        except UserNotFound:
            return Response(
                {'detail': f"No user found with username '{username}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CannotAddSelf:
            return Response(
                {'detail': "You can't add yourself as a friend."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = FriendshipSerializer(friendship)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class FriendRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=None)
    def delete(self, request, pk):
        friendship = get_object_or_404(Friendship, pk=pk, user1=request.user)
        friendship.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
