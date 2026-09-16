"""Service-layer tests for accounts.

Per project convention, every new piece of business logic in services.py
gets a test here before the feature is considered done.
"""

from django.test import TestCase

from apps.accounts.models import ApprovalStatus, Role, User


class UserManagerTests(TestCase):
    def test_create_user_sets_given_fields(self):
        user = User.objects.create_user(
            email="patient@example.com",
            password="strongpass123",
            full_name="Pat Ient",
            role=Role.PATIENT,
        )
        self.assertEqual(user.email, "patient@example.com")
        self.assertEqual(user.full_name, "Pat Ient")
        self.assertEqual(user.role, Role.PATIENT)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_super_admin)
        self.assertTrue(user.check_password("strongpass123"))

    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(
            email="patient@EXAMPLE.com",
            password="strongpass123",
            full_name="Pat Ient",
            role=Role.PATIENT,
        )
        self.assertEqual(user.email, "patient@example.com")

    def test_create_superuser_is_admin_and_super_admin(self):
        user = User.objects.create_superuser(
            email="root@example.com", password="strongpass123"
        )
        self.assertEqual(user.role, Role.ADMIN)
        self.assertEqual(user.approval_status, ApprovalStatus.APPROVED)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_super_admin)

    def test_create_superuser_forces_admin_role_even_if_overridden(self):
        user = User.objects.create_superuser(
            email="root2@example.com", password="strongpass123", role=Role.PATIENT
        )
        self.assertEqual(user.role, Role.ADMIN)
