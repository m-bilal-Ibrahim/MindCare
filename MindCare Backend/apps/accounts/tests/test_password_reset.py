"""Phase 2 module 1: password reset by emailed 6-digit code, the
password-changed notice, approval/rejection emails, and the Django admin gate
for temporary passwords."""

import re
from datetime import timedelta
from unittest import mock

from django.contrib.auth.hashers import check_password
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts import services
from apps.accounts.models import ApprovalStatus, PasswordResetCode, Role
from core.exceptions import DomainValidationError
from core.testing import (
    PASSWORD,
    make_admin,
    make_patient,
    make_psychologist,
    make_super_admin,
    make_user,
)

REQUEST = "/api/v1/accounts/password/reset/"
CONFIRM = "/api/v1/accounts/password/reset/confirm/"
NEW_PASSWORD = "a-much-better-passphrase-77"


def sent_code():
    """The code in the newest email in the outbox."""
    return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)


class RequestResetServiceTests(TestCase):
    def setUp(self):
        self.user = make_patient().user

    def request(self, email=None):
        with self.captureOnCommitCallbacks(execute=True):
            services.request_password_reset(email=email or self.user.email)

    def test_emails_a_hashed_six_digit_code(self):
        self.request(self.user.email.upper())
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.user.email])
        self.assertIn("password reset code", message.subject)
        code = sent_code()
        reset = PasswordResetCode.objects.get(user=self.user)
        self.assertNotEqual(reset.code_hash, code)
        self.assertTrue(check_password(code, reset.code_hash))
        self.assertAlmostEqual(
            (reset.expires_at - reset.created_at).total_seconds(), 15 * 60, delta=5
        )
        self.assertIn(code, message.alternatives[0][0])  # html part too

    def test_a_new_request_supersedes_the_old_code(self):
        self.request()
        first = sent_code()
        self.request()
        second = sent_code()
        codes = PasswordResetCode.objects.filter(user=self.user)
        self.assertEqual(codes.filter(closed_at__isnull=True).count(), 1)
        with self.assertRaises(services.InvalidResetCode):
            if first != second:
                services.confirm_password_reset(
                    email=self.user.email, code=first, new_password=NEW_PASSWORD
                )
            else:  # same digits by chance: still only one open code
                raise services.InvalidResetCode()

    def test_three_codes_an_hour_per_account(self):
        for _ in range(4):
            self.request()
        self.assertEqual(len(mail.outbox), 3)

    def test_unknown_deactivated_and_rejected_get_nothing(self):
        deactivated = make_patient(is_active=False).user
        rejected = make_psychologist(approval_status=ApprovalStatus.REJECTED).user
        for email in ("nobody@example.com", deactivated.email, rejected.email):
            self.request(email)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(PasswordResetCode.objects.exists())

    def test_pending_accounts_can_reset(self):
        pending = make_psychologist(approval_status=ApprovalStatus.PENDING).user
        self.request(pending.email)
        self.assertEqual(mail.outbox[0].to, [pending.email])

    def test_old_rows_are_cleaned_up(self):
        self.request()
        PasswordResetCode.objects.update(created_at=timezone.now() - timedelta(days=2))
        self.request()
        self.assertEqual(PasswordResetCode.objects.count(), 1)

    def test_nothing_is_sent_if_the_transaction_rolls_back(self):
        from django.db import transaction

        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    services.request_password_reset(email=self.user.email)
                    raise RuntimeError
            except RuntimeError:
                pass
        self.assertEqual(mail.outbox, [])


class ConfirmResetServiceTests(TestCase):
    def setUp(self):
        self.user = make_admin(must_change_password=True)
        with self.captureOnCommitCallbacks(execute=True):
            services.request_password_reset(email=self.user.email)
        self.code = sent_code()
        mail.outbox.clear()

    def confirm(self, code=None, password=NEW_PASSWORD, email=None):
        with self.captureOnCommitCallbacks(execute=True):
            return services.confirm_password_reset(
                email=email or self.user.email,
                code=code or self.code,
                new_password=password,
            )

    def wrong_code(self):
        return "000000" if self.code != "000000" else "111111"

    def test_success_sets_password_signs_out_and_sends_notice(self):
        token = RefreshToken.for_user(self.user)
        self.confirm()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertFalse(self.user.must_change_password)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=token["jti"]).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("password was changed", mail.outbox[0].subject)
        self.assertNotIn(NEW_PASSWORD, mail.outbox[0].body)
        with self.assertRaises(services.InvalidResetCode):  # used once only
            self.confirm()

    def test_five_wrong_tries_kill_the_code(self):
        for _ in range(5):
            with self.assertRaises(services.InvalidResetCode):
                self.confirm(code=self.wrong_code())
        with self.assertRaises(services.InvalidResetCode):
            self.confirm()  # even the right code is dead now
        self.assertEqual(PasswordResetCode.objects.get().failed_attempts, 5)

    def test_wrong_tries_are_counted_even_though_the_call_fails(self):
        with self.assertRaises(services.InvalidResetCode):
            self.confirm(code=self.wrong_code())
        self.assertEqual(PasswordResetCode.objects.get().failed_attempts, 1)
        self.confirm()

    def test_expired_code(self):
        PasswordResetCode.objects.update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        with self.assertRaises(services.InvalidResetCode):
            self.confirm()

    def test_weak_password_keeps_the_code_usable(self):
        with self.assertRaises(DomainValidationError) as ctx:
            self.confirm(password="12345678")
        self.assertIn("new_password", ctx.exception.errors)
        self.confirm()

    def test_password_similar_to_email_refused(self):
        with self.assertRaises(DomainValidationError):
            self.confirm(password=self.user.email)

    def test_unknown_email(self):
        with self.assertRaises(services.InvalidResetCode):
            self.confirm(email="nobody@example.com")

    def test_deactivated_after_request(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        with self.assertRaises(services.InvalidResetCode):
            self.confirm()


class PasswordResetAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_patient().user

    def tearDown(self):
        cache.clear()

    def test_same_answer_for_known_and_unknown_emails(self):
        with self.captureOnCommitCallbacks(execute=True):
            known = self.client.post(REQUEST, {"email": self.user.email})
            unknown = self.client.post(REQUEST, {"email": "nobody@example.com"})
        self.assertEqual(known.status_code, 200)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_full_flow(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(REQUEST, {"email": self.user.email})
        code = sent_code()
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(
                CONFIRM,
                {"email": self.user.email, "code": code, "new_password": NEW_PASSWORD},
            )
        self.assertEqual(r.status_code, 200, r.json())
        login = self.client.post(
            "/api/v1/accounts/login/",
            {"email": self.user.email, "password": NEW_PASSWORD},
        )
        self.assertEqual(login.status_code, 200)

    def test_request_validation(self):
        for body in ({}, {"email": "not-an-email"}, {"email": "a@b.co", "x": 1}):
            with self.subTest(body=body):
                self.assertEqual(
                    self.client.post(REQUEST, body, format="json").status_code, 400
                )

    def test_confirm_validation(self):
        base = {
            "email": self.user.email,
            "code": "123456",
            "new_password": NEW_PASSWORD,
        }
        cases = [
            ({**base, "code": "12345"}, "code"),
            ({**base, "code": "12345a"}, "code"),
            ({**base, "code": ""}, "code"),
            ({k: v for k, v in base.items() if k != "code"}, "code"),
            ({**base, "email": "bad"}, "email"),
            ({k: v for k, v in base.items() if k != "new_password"}, "new_password"),
            ({**base, "extra": 1}, "extra"),
        ]
        for body, field in cases:
            with self.subTest(body=body):
                r = self.client.post(CONFIRM, body, format="json")
                self.assertEqual(r.status_code, 400)
                self.assertIn(field, r.json())
        r = self.client.post(CONFIRM, {**base, "code": "12345"}, format="json")
        self.assertEqual(r.json(), {"code": ["Enter the 6-digit code from the email."]})

    def test_wrong_code_message_is_generic(self):
        r = self.client.post(
            CONFIRM,
            {
                "email": "nobody@example.com",
                "code": "123456",
                "new_password": NEW_PASSWORD,
            },
        )
        self.assertEqual(
            r.json(),
            {"code": ["That code is wrong or has expired. Request a new one."]},
        )

    def test_request_is_throttled_per_address(self):
        for _ in range(5):
            self.client.post(REQUEST, {"email": "nobody@example.com"})
        r = self.client.post(REQUEST, {"email": "nobody@example.com"})
        self.assertEqual(r.status_code, 429)

    def test_password_change_also_sends_the_notice(self):
        self.client.force_authenticate(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(
                "/api/v1/accounts/password/change/",
                {"current_password": PASSWORD, "new_password": NEW_PASSWORD},
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(mail.outbox[-1].to, [self.user.email])
        self.assertIn("password was changed", mail.outbox[-1].subject)


class ReviewEmailTests(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def review(self, user, decision, reason=None):
        with self.captureOnCommitCallbacks(execute=True):
            services.review_pending_account(
                admin=self.admin, user_id=user.pk, decision=decision, reason=reason
            )

    def test_approval_email(self):
        applicant = make_psychologist(approval_status=ApprovalStatus.PENDING).user
        self.review(applicant, ApprovalStatus.APPROVED)
        [message] = mail.outbox
        self.assertEqual(message.to, [applicant.email])
        self.assertIn("approved", message.subject)

    def test_rejection_email_has_reason_label_and_support_contact(self):
        ngo = make_user(role=Role.NGO, approval_status=ApprovalStatus.PENDING)
        self.review(
            ngo, ApprovalStatus.REJECTED, reason=services.RejectReason.NOT_ELIGIBLE
        )
        [message] = mail.outbox
        self.assertIn("Reason: Not eligible.", message.body)
        self.assertIn("support@mindcare.test", message.body)
        self.assertIn("NGO", message.body)

    def test_rejection_without_reason(self):
        applicant = make_psychologist(approval_status=ApprovalStatus.PENDING).user
        self.review(applicant, ApprovalStatus.REJECTED)
        self.assertNotIn("Reason:", mail.outbox[0].body)

    def test_names_are_escaped_in_html(self):
        from apps.notifications import emails

        _, _, html = emails.account_approved(full_name="<b>Eve</b>", role="ngo")
        self.assertIn("&lt;b&gt;Eve&lt;/b&gt;", html)
        self.assertNotIn("<b>Eve</b>", html)


class DjangoAdminTemporaryPasswordTests(TestCase):
    def setUp(self):
        root = make_super_admin()
        self.user, self.password = services.create_admin_account(
            actor=root, email="fresh@example.com", full_name="Fresh Admin"
        )

    def test_login_refused_until_password_changed(self):
        r = self.client.post(
            "/admin/login/?next=/admin/",
            {"username": "fresh@example.com", "password": self.password},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Change your temporary password")
        self.assertNotIn("_auth_user_id", self.client.session)

        services.change_password(
            user=self.user, current_password=self.password, new_password=NEW_PASSWORD
        )
        r = self.client.post(
            "/admin/login/?next=/admin/",
            {"username": "fresh@example.com", "password": NEW_PASSWORD},
        )
        self.assertEqual(r.status_code, 302)

    def test_existing_session_loses_access_when_flag_is_set(self):
        self.user.must_change_password = False
        self.user.save(update_fields=["must_change_password"])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])
        self.assertEqual(self.client.get("/admin/").status_code, 302)


class EmailFailureNeverBreaksTheRequestTests(TestCase):
    def test_provider_failure_is_logged_without_details(self):
        from integrations.email_client.client import EmailNotSent

        user = make_patient().user
        with mock.patch(
            "apps.notifications.services.send_email",
            side_effect=EmailNotSent("http_401"),
        ), self.assertLogs("mindcare.email", level="WARNING") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                services.request_password_reset(email=user.email)
        line = logs.output[0]
        self.assertIn("password_reset_code", line)
        self.assertIn("http_401", line)
        self.assertNotIn(user.email, line)
        self.assertTrue(PasswordResetCode.objects.filter(user=user).exists())
