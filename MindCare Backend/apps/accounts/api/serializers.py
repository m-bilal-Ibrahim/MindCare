"""DRF serializers for the accounts API."""

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts import services
from apps.accounts.models import Role, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)
    role = serializers.ChoiceField(choices=[Role.PATIENT, Role.PSYCHOLOGIST, Role.NGO])

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        from django.contrib.auth.password_validation import (
            validate_password as django_validate_password,
        )
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            django_validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "approval_status"]


class MindCareTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        request = self.context.get("request")
        ip = request.META.get("REMOTE_ADDR") if request is not None else None

        try:
            user = services.authenticate_and_check_approval(
                email=attrs[self.username_field], password=attrs["password"], ip=ip
            )
        except services.InvalidCredentialsError as exc:
            raise AuthenticationFailed(str(exc), code="no_active_account") from exc
        except services.AccountPendingApprovalError as exc:
            raise AuthenticationFailed(
                str(exc), code="account_pending_approval"
            ) from exc
        except services.AccountRejectedError as exc:
            raise AuthenticationFailed(str(exc), code="account_rejected") from exc

        refresh = self.get_token(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
