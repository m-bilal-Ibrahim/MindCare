"""DRF serializers for the accounts API."""

from rest_framework import serializers

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


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "approval_status"]
