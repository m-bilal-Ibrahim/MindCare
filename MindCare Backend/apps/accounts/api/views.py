"""DRF views for the accounts API.

Views stay thin: parse the request, delegate to services.py (writes) or
selectors.py (reads), then serialize the result. No business logic here.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import services
from apps.accounts.api.serializers import RegisterSerializer, UserPublicSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_user(**serializer.validated_data)
        return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)
