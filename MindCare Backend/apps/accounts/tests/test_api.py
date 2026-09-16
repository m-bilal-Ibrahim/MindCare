"""API-layer tests for accounts."""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role, User

REGISTER_URL = "/api/v1/accounts/register/"


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
