"""DRF views for the accounts API.

Views stay thin: parse the request, delegate to services.py (writes) or
selectors.py (reads), then serialize the result. No business logic here.
"""

from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.accounts import services
from apps.accounts.api.serializers import (
    MindCareTokenObtainPairSerializer,
    RegisterSerializer,
    UserPublicSerializer,
)
from apps.accounts.models import User


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_user(**serializer.validated_data)
        return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class LoginView(TokenObtainPairView):
    serializer_class = MindCareTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]
    permission_classes = [AllowAny]
    authentication_classes = []


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        user = None
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                user = User.objects.filter(pk=token["user_id"]).first()
            except TokenError:
                user = None

        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK and user is not None:
            services.record_token_refresh(user=user, ip=request.META.get("REMOTE_ADDR"))
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise ParseError("refresh token is required")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            raise ParseError("invalid or already-blacklisted token") from exc

        services.record_logout(user=request.user, ip=request.META.get("REMOTE_ADDR"))
        return Response(status=status.HTTP_205_RESET_CONTENT)
