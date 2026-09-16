"""API-layer tests for accounts."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role, User

REGISTER_URL = "/api/v1/accounts/register/"
LOGIN_URL = "/api/v1/accounts/login/"


class RegisterAPITests(APITestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_patient_can_register_and_is_approved(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "newpatient@example.com",
                "password": "strongpass123",
                "full_name": "New Patient",
                "role": "patient",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newpatient@example.com")
        self.assertEqual(user.approval_status, ApprovalStatus.APPROVED)

    def test_psychologist_registration_is_pending(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "newdoc@example.com",
                "password": "strongpass123",
                "full_name": "New Doc",
                "role": "psychologist",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newdoc@example.com")
        self.assertEqual(user.approval_status, ApprovalStatus.PENDING)

    def test_admin_role_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "wannabeadmin@example.com",
                "password": "strongpass123",
                "full_name": "Wannabe Admin",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="wannabeadmin@example.com").exists())

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email="dup@example.com",
            password="strongpass123",
            full_name="Existing",
            role=Role.PATIENT,
        )
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "dup@example.com",
                "password": "strongpass123",
                "full_name": "Dup Attempt",
                "role": "patient",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "weakpass@example.com",
                "password": "password",
                "full_name": "Weak Password",
                "role": "patient",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email="weakpass@example.com").exists())

    def test_purely_numeric_weak_password_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "numericpass@example.com",
                "password": "12345678",
                "full_name": "Numeric Password",
                "role": "patient",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_endpoint_is_throttled_after_repeated_requests(self):
        for i in range(10):
            response = self.client.post(
                REGISTER_URL,
                {
                    "email": f"throttleuser{i}@example.com",
                    "password": "strongpass123",
                    "full_name": "Throttle User",
                    "role": "patient",
                },
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "throttleuser-over-limit@example.com",
                "password": "strongpass123",
                "full_name": "Throttle User",
                "role": "patient",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class LoginAPITests(APITestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.password = "strongpass123"
        self.patient = User.objects.create_user(
            email="loginpatient@example.com",
            password=self.password,
            full_name="Pat Ient",
            role=Role.PATIENT,
            approval_status=ApprovalStatus.APPROVED,
        )
        self.pending_psych = User.objects.create_user(
            email="loginpending@example.com",
            password=self.password,
            full_name="Pending Doc",
            role=Role.PSYCHOLOGIST,
            approval_status=ApprovalStatus.PENDING,
        )

    def test_successful_login_returns_tokens_with_role_claim(self):
        response = self.client.post(
            LOGIN_URL, {"email": "loginpatient@example.com", "password": self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken(response.data["access"])
        self.assertEqual(token["role"], "patient")

    def test_pending_account_login_is_rejected_with_clear_message(self):
        response = self.client.post(
            LOGIN_URL, {"email": "loginpending@example.com", "password": self.password}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("pending admin approval", str(response.data))

    def test_wrong_password_rejected(self):
        response = self.client.post(
            LOGIN_URL, {"email": "loginpatient@example.com", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_endpoint_is_throttled_after_repeated_failures(self):
        for _ in range(5):
            self.client.post(
                LOGIN_URL,
                {"email": "loginpatient@example.com", "password": "wrongpass"},
            )
        response = self.client.post(
            LOGIN_URL, {"email": "loginpatient@example.com", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


REFRESH_URL = "/api/v1/accounts/refresh/"
LOGOUT_URL = "/api/v1/accounts/logout/"


class RefreshAndLogoutAPITests(APITestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.password = "strongpass123"
        self.user = User.objects.create_user(
            email="refreshuser@example.com",
            password=self.password,
            full_name="Refresh User",
            role=Role.PATIENT,
            approval_status=ApprovalStatus.APPROVED,
        )
        login = self.client.post(
            LOGIN_URL, {"email": "refreshuser@example.com", "password": self.password}
        )
        self.access = login.data["access"]
        self.refresh = login.data["refresh"]

    def test_refresh_rotates_token_and_blacklists_old_one(self):
        response = self.client.post(REFRESH_URL, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_refresh = response.data["refresh"]
        self.assertNotEqual(new_refresh, self.refresh)

        reuse_response = self.client.post(REFRESH_URL, {"refresh": self.refresh})
        self.assertEqual(reuse_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_is_rejected_after_approval_status_changes_to_pending(self):
        self.user.approval_status = ApprovalStatus.PENDING
        self.user.save(update_fields=["approval_status"])

        response = self.client.post(REFRESH_URL, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_is_rejected_after_account_is_rejected(self):
        self.user.approval_status = ApprovalStatus.REJECTED
        self.user.save(update_fields=["approval_status"])

        response = self.client.post(REFRESH_URL, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(LOGOUT_URL, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        response = self.client.post(LOGOUT_URL, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_after_logout = self.client.post(REFRESH_URL, {"refresh": self.refresh})
        self.assertEqual(refresh_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_rejects_token_from_different_user(self):
        # Create another user and get their tokens
        User.objects.create_user(
            email="otheruser@example.com",
            password=self.password,
            full_name="Other User",
            role=Role.PATIENT,
            approval_status=ApprovalStatus.APPROVED,
        )
        other_login = self.client.post(
            LOGIN_URL, {"email": "otheruser@example.com", "password": self.password}
        )
        other_refresh = other_login.data["refresh"]

        # First user tries to logout with other user's refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        response = self.client.post(LOGOUT_URL, {"refresh": other_refresh})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not belong", str(response.data))

        # Verify other user's token is still valid (not blacklisted)
        refresh_result = self.client.post(REFRESH_URL, {"refresh": other_refresh})
        self.assertEqual(refresh_result.status_code, status.HTTP_200_OK)
