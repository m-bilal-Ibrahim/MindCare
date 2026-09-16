"""API-layer tests for accounts."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role, User

REGISTER_URL = "/api/v1/accounts/register/"
LOGIN_URL = "/api/v1/accounts/login/"


class RegisterAPITests(APITestCase):
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
