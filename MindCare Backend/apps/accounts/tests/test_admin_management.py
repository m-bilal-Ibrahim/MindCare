"""Phase 2 module 0: the super-admin workflow (create, promote, demote self,
deactivate/reactivate admins), the temporary-password gate, and
POST /accounts/password/change/ for every user."""

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts import services
from apps.accounts.models import Role, User
from core.exceptions import DomainValidationError
from core.testing import (
    PASSWORD,
    make_admin,
    make_patient,
    make_psychologist,
    make_super_admin,
)

ADMINS = "/api/v1/accounts/admin/admins/"
DEMOTE_SELF = "/api/v1/accounts/admin/admins/me/demote/"
PASSWORD_CHANGE = "/api/v1/accounts/password/change/"
LOGIN = "/api/v1/accounts/login/"
OVERVIEW = "/api/v1/accounts/admin/overview/"
NEW_PASSWORD = "a-much-better-passphrase-77"


def action_url(user_id, action):
    return f"{ADMINS}{user_id}/{action}/"


# --- Services -----------------------------------------------------------------


class CreateAdminServiceTests(TestCase):
    def setUp(self):
        self.root = make_super_admin()

    def test_creates_staff_admin_in_group_with_temporary_password(self):
        user, password = services.create_admin_account(
            actor=self.root, email="New.Admin@Example.com", full_name="Ayesha Khan"
        )
        user.refresh_from_db()
        self.assertEqual(user.email, "new.admin@example.com")
        self.assertEqual(user.role, Role.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_super_admin)
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password(password))
        self.assertGreaterEqual(len(password), 16)
        self.assertTrue(user.groups.filter(name=services.ADMIN_GROUP_NAME).exists())

    def test_admin_group_can_edit_content_and_only_view_users(self):
        group = services.ensure_admin_group()
        codenames = set(group.permissions.values_list("codename", flat=True))
        self.assertTrue(
            {"change_quote", "add_dua", "change_surah", "change_city"} <= codenames
        )
        self.assertIn("view_user", codenames)
        self.assertNotIn("change_user", codenames)
        self.assertNotIn("delete_user", codenames)
        self.assertNotIn("delete_city", codenames)

    def test_ensure_admin_group_is_idempotent(self):
        services.ensure_admin_group()
        services.ensure_admin_group()
        self.assertEqual(
            Group.objects.filter(name=services.ADMIN_GROUP_NAME).count(), 1
        )

    def test_ordinary_admin_cannot_create_admins(self):
        with self.assertRaises(services.NotSuperAdmin):
            services.create_admin_account(
                actor=make_admin(), email="x@example.com", full_name="Some One"
            )

    def test_duplicate_email(self):
        existing = make_patient().user
        with self.assertRaises(services.DuplicateEmailError):
            services.create_admin_account(
                actor=self.root, email=existing.email.upper(), full_name="Some One"
            )

    def test_name_rule_applies(self):
        with self.assertRaises(DomainValidationError):
            services.create_admin_account(
                actor=self.root, email="x@example.com", full_name="Admin 2"
            )


class PromoteDemoteServiceTests(TestCase):
    def setUp(self):
        self.root = make_super_admin()

    def test_promote_then_demote_self(self):
        admin = make_admin(is_staff=True)
        services.promote_admin(actor=self.root, user_id=admin.pk)
        admin.refresh_from_db()
        self.assertTrue(admin.is_super_admin)
        self.assertTrue(admin.is_superuser)

        services.demote_self(actor=self.root)
        self.root.refresh_from_db()
        self.assertFalse(self.root.is_super_admin)
        self.assertFalse(self.root.is_superuser)
        self.assertTrue(self.root.is_staff)
        self.assertTrue(
            self.root.groups.filter(name=services.ADMIN_GROUP_NAME).exists()
        )

    def test_last_super_admin_cannot_demote(self):
        with self.assertRaises(DomainValidationError) as ctx:
            services.demote_self(actor=self.root)
        self.assertIn("only super-admin", ctx.exception.errors["is_super_admin"][0])
        self.root.refresh_from_db()
        self.assertTrue(self.root.is_super_admin)

    def test_a_deactivated_super_admin_does_not_count(self):
        make_super_admin(is_active=False)
        with self.assertRaises(DomainValidationError):
            services.demote_self(actor=self.root)

    def test_promote_refuses_super_admin_inactive_and_non_admin(self):
        other_root = make_super_admin()
        inactive = make_admin(is_active=False)
        with self.assertRaises(DomainValidationError):
            services.promote_admin(actor=self.root, user_id=other_root.pk)
        with self.assertRaises(DomainValidationError):
            services.promote_admin(actor=self.root, user_id=inactive.pk)
        with self.assertRaises(services.AccountNotFound):
            services.promote_admin(actor=self.root, user_id=make_patient().user.pk)

    def test_ordinary_admin_cannot_promote(self):
        with self.assertRaises(services.NotSuperAdmin):
            services.promote_admin(actor=make_admin(), user_id=make_admin().pk)


class DeactivateAdminServiceTests(TestCase):
    def setUp(self):
        self.root = make_super_admin()
        self.admin = make_admin(is_staff=True)

    def test_deactivate_revokes_sessions_and_reactivate(self):
        token = RefreshToken.for_user(self.admin)
        services.deactivate_admin(actor=self.root, user_id=self.admin.pk)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)
        self.assertIsNotNone(self.admin.deactivated_at)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=token["jti"]).exists()
        )

        services.reactivate_admin(actor=self.root, user_id=self.admin.pk)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertIsNone(self.admin.deactivated_at)

    def test_cannot_deactivate_self(self):
        with self.assertRaises(DomainValidationError) as ctx:
            services.deactivate_admin(actor=self.root, user_id=self.root.pk)
        self.assertIn("your own account", ctx.exception.errors["is_active"][0])

    def test_super_admin_must_be_demoted_first(self):
        other_root = make_super_admin()
        with self.assertRaises(DomainValidationError) as ctx:
            services.deactivate_admin(actor=self.root, user_id=other_root.pk)
        self.assertIn("demote themselves", ctx.exception.errors["is_active"][0])

    def test_double_deactivate_and_reactivate_active(self):
        services.deactivate_admin(actor=self.root, user_id=self.admin.pk)
        with self.assertRaises(DomainValidationError):
            services.deactivate_admin(actor=self.root, user_id=self.admin.pk)
        services.reactivate_admin(actor=self.root, user_id=self.admin.pk)
        with self.assertRaises(DomainValidationError):
            services.reactivate_admin(actor=self.root, user_id=self.admin.pk)

    def test_non_admin_targets_are_not_found(self):
        with self.assertRaises(services.AccountNotFound):
            services.deactivate_admin(actor=self.root, user_id=make_patient().user.pk)


class ChangePasswordServiceTests(TestCase):
    def test_changes_password_clears_flag_and_signs_out_everywhere(self):
        user = make_admin(must_change_password=True)
        old = RefreshToken.for_user(user)
        services.change_password(
            user=user, current_password=PASSWORD, new_password=NEW_PASSWORD
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertFalse(user.must_change_password)
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old["jti"]).exists())

    def test_wrong_current_password(self):
        user = make_patient().user
        with self.assertRaises(services.WrongCurrentPassword):
            services.change_password(
                user=user, current_password="nope", new_password=NEW_PASSWORD
            )

    def test_same_password_refused(self):
        user = make_patient().user
        with self.assertRaises(DomainValidationError):
            services.change_password(
                user=user, current_password=PASSWORD, new_password=PASSWORD
            )

    def test_deactivating_a_patient_also_revokes_sessions(self):
        patient = make_patient().user
        token = RefreshToken.for_user(patient)
        services.deactivate_account(admin=make_admin(), user_id=patient.pk)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=token["jti"]).exists()
        )


# --- API ----------------------------------------------------------------------


class AdminManagementAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.root = make_super_admin()
        self.client.force_authenticate(self.root)

    def test_super_admin_creates_admin_and_sees_password_once(self):
        r = self.client.post(
            ADMINS, {"email": "Second@Example.com", "full_name": "Bilal Ahmed"}
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.json())
        body = r.json()
        self.assertEqual(body["email"], "second@example.com")
        self.assertTrue(body["must_change_password"])
        self.assertFalse(body["is_super_admin"])
        password = body["temporary_password"]
        self.assertTrue(User.objects.get(pk=body["id"]).check_password(password))

        listing = self.client.get(ADMINS).json()
        self.assertEqual([row["id"] for row in listing], [self.root.pk, body["id"]])
        self.assertNotIn("temporary_password", listing[1])

    def test_create_validation(self):
        make_patient(email="taken@example.com")
        cases = [
            ({"email": "taken@example.com", "full_name": "Bilal Ahmed"}, "email"),
            ({"email": "not-an-email", "full_name": "Bilal Ahmed"}, "email"),
            ({"email": "a@example.com", "full_name": "Bilal 2"}, "full_name"),
            ({"email": "a@example.com", "full_name": "   "}, "full_name"),
            ({"email": "a@example.com", "full_name": "<b>X</b>"}, "full_name"),
            ({"email": "a@example.com"}, "full_name"),
            (
                {"email": "a@example.com", "full_name": "Bilal Ahmed", "role": "x"},
                "role",
            ),
        ]
        for payload, field in cases:
            with self.subTest(payload=payload):
                r = self.client.post(ADMINS, payload, format="json")
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.json())

    def test_ordinary_admin_gets_403_on_every_admin_management_endpoint(self):
        admin = make_admin()
        self.client.force_authenticate(admin)
        calls = [
            ("get", ADMINS),
            ("post", ADMINS),
            ("post", DEMOTE_SELF),
            ("post", action_url(self.root.pk, "promote")),
            ("post", action_url(self.root.pk, "deactivate")),
            ("post", action_url(self.root.pk, "reactivate")),
        ]
        for method, url in calls:
            with self.subTest(url=url):
                r = getattr(self.client, method)(url, {}, format="json")
                self.assertEqual(r.status_code, 403)

    def test_patient_gets_403(self):
        self.client.force_authenticate(make_patient().user)
        self.assertEqual(self.client.get(ADMINS).status_code, 403)

    def test_promote_demote_deactivate_flow(self):
        admin = make_admin(is_staff=True)
        r = self.client.post(action_url(admin.pk, "promote"))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["is_super_admin"])

        r = self.client.post(DEMOTE_SELF)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["is_super_admin"])

        # The former root is now an ordinary admin: 403 on admin management.
        self.root.refresh_from_db()
        self.client.force_authenticate(self.root)
        self.assertEqual(self.client.get(ADMINS).status_code, 403)

        admin.refresh_from_db()
        self.client.force_authenticate(admin)
        r = self.client.post(DEMOTE_SELF)
        self.assertEqual(r.status_code, 400)
        self.assertIn("is_super_admin", r.json())

        r = self.client.post(action_url(self.root.pk, "deactivate"))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["is_active"])
        r = self.client.post(action_url(self.root.pk, "reactivate"))
        self.assertEqual(r.status_code, 200)

    def test_unknown_admin_404_and_self_deactivate_400(self):
        self.assertEqual(
            self.client.post(action_url(99999, "promote")).status_code, 404
        )
        patient = make_patient().user
        self.assertEqual(
            self.client.post(action_url(patient.pk, "deactivate")).status_code, 404
        )
        r = self.client.post(action_url(self.root.pk, "deactivate"))
        self.assertEqual(r.status_code, 400)


class TemporaryPasswordGateTests(APITestCase):
    def setUp(self):
        cache.clear()
        root = make_super_admin()
        self.user, self.password = services.create_admin_account(
            actor=root, email="fresh@example.com", full_name="Fresh Admin"
        )

    def test_login_reports_the_flag_and_admin_endpoints_refuse_until_changed(self):
        r = self.client.post(
            LOGIN, {"email": "fresh@example.com", "password": self.password}
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["must_change_password"])
        access = r.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        r = self.client.get(OVERVIEW)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(
            r.json()["detail"], "Change your temporary password before continuing."
        )

        r = self.client.post(
            PASSWORD_CHANGE,
            {"current_password": self.password, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(r.status_code, 200, r.json())
        self.assertFalse(r.json()["must_change_password"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['access']}")
        self.assertEqual(self.client.get(OVERVIEW).status_code, 200)

    def test_login_flag_is_false_for_ordinary_users(self):
        patient = make_patient().user
        r = self.client.post(LOGIN, {"email": patient.email, "password": PASSWORD})
        self.assertFalse(r.json()["must_change_password"])


class PasswordChangeAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_psychologist().user
        self.client.force_authenticate(self.user)

    def test_success_returns_new_pair_and_revokes_old_tokens(self):
        old = RefreshToken.for_user(self.user)
        r = self.client.post(
            PASSWORD_CHANGE,
            {"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()), {"refresh", "access", "must_change_password"})
        self.assertTrue(BlacklistedToken.objects.filter(token__jti=old["jti"]).exists())
        new_jti = RefreshToken(r.json()["refresh"])["jti"]
        self.assertFalse(BlacklistedToken.objects.filter(token__jti=new_jti).exists())
        self.assertTrue(OutstandingToken.objects.filter(jti=new_jti).exists())

    def test_validation(self):
        cases = [
            (
                {"current_password": "wrong", "new_password": NEW_PASSWORD},
                "current_password",
            ),
            ({"current_password": PASSWORD, "new_password": "short"}, "new_password"),
            (
                {"current_password": PASSWORD, "new_password": "12345678901"},
                "new_password",
            ),
            (
                {"current_password": PASSWORD, "new_password": "password123"},
                "new_password",
            ),
            (
                {"current_password": PASSWORD, "new_password": self.user.email},
                "new_password",
            ),
            ({"current_password": PASSWORD, "new_password": PASSWORD}, "new_password"),
            ({"current_password": PASSWORD}, "new_password"),
            ({"new_password": NEW_PASSWORD}, "current_password"),
            (
                {"current_password": PASSWORD, "new_password": NEW_PASSWORD, "x": 1},
                "x",
            ),
        ]
        for payload, field in cases:
            with self.subTest(payload=payload):
                r = self.client.post(PASSWORD_CHANGE, payload, format="json")
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.json())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_wrong_current_password_message(self):
        r = self.client.post(
            PASSWORD_CHANGE, {"current_password": "wrong", "new_password": NEW_PASSWORD}
        )
        self.assertEqual(
            r.json(), {"current_password": ["Your current password is incorrect."]}
        )

    def test_requires_login(self):
        self.client.force_authenticate(None)
        r = self.client.post(
            PASSWORD_CHANGE,
            {"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(r.status_code, 401)
