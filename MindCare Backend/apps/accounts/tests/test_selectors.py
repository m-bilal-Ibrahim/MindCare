"""Read-path query logic tests for accounts."""

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ApprovalStatus, Role, User
from apps.accounts.selectors import get_user_from_refresh_token


class GetUserFromRefreshTokenTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="selector@example.com",
            password="strongpass123",
            full_name="Selector User",
            role=Role.PATIENT,
            approval_status=ApprovalStatus.APPROVED,
        )

    def test_valid_token_returns_correct_user(self):
        token = RefreshToken.for_user(self.user)
        result = get_user_from_refresh_token(str(token))
        self.assertEqual(result, self.user)

    def test_invalid_token_returns_none(self):
        result = get_user_from_refresh_token("invalid.token.here")
        self.assertIsNone(result)

    def test_malformed_token_returns_none(self):
        result = get_user_from_refresh_token("not-a-token")
        self.assertIsNone(result)
