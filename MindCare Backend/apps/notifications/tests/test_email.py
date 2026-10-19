"""Phase 2 module 1: the email layer. Brevo and Resend over HTTPS (urllib,
mocked here), Django's mailer for `console`, `disabled`, after-commit background
delivery, and the deploy checks."""

import json
from unittest import mock
from urllib.error import HTTPError, URLError

from django.core import mail
from django.test import TestCase, override_settings

from apps.notifications.services import send_email_after_commit
from core import checks
from integrations.email_client import client
from integrations.email_client.client import EmailNotSent, send_email

MESSAGE = ("Subject line", "Plain body", "<p>Html body</p>")


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return b"{}"


def sent_request(urlopen):
    request = urlopen.call_args.args[0]
    return request, json.loads(request.data)


@override_settings(
    EMAIL_PROVIDER_API_KEY="secret-key",
    DEFAULT_FROM_EMAIL="mindcare@example.org",
    DEFAULT_FROM_NAME="MindCare",
)
class ProviderTests(TestCase):
    @override_settings(EMAIL_PROVIDER="brevo")
    def test_brevo_payload(self):
        with mock.patch.object(client, "urlopen", return_value=_Response()) as urlopen:
            send_email(to="a@example.com", subject="S", text="T", html="<p>H</p>")
        request, body = sent_request(urlopen)
        self.assertEqual(request.full_url, client.BREVO_URL)
        self.assertEqual(request.get_header("Api-key"), "secret-key")
        self.assertEqual(
            body,
            {
                "sender": {"email": "mindcare@example.org", "name": "MindCare"},
                "to": [{"email": "a@example.com"}],
                "subject": "S",
                "textContent": "T",
                "htmlContent": "<p>H</p>",
            },
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 10)

    @override_settings(EMAIL_PROVIDER="resend")
    def test_resend_payload(self):
        with mock.patch.object(client, "urlopen", return_value=_Response()) as urlopen:
            send_email(to="a@example.com", subject="S", text="T")
        request, body = sent_request(urlopen)
        self.assertEqual(request.full_url, client.RESEND_URL)
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-key")
        self.assertEqual(
            body,
            {
                "from": "MindCare <mindcare@example.org>",
                "to": ["a@example.com"],
                "subject": "S",
                "text": "T",
            },
        )

    @override_settings(EMAIL_PROVIDER="brevo")
    def test_http_error_becomes_email_not_sent_with_status_only(self):
        error = HTTPError(client.BREVO_URL, 401, "Unauthorized", {}, None)
        with mock.patch.object(client, "urlopen", side_effect=error):
            with self.assertRaises(EmailNotSent) as ctx:
                send_email(to="a@example.com", subject="S", text="T")
        self.assertEqual(ctx.exception.reason, "http_401")

    @override_settings(EMAIL_PROVIDER="resend")
    def test_network_error(self):
        with mock.patch.object(client, "urlopen", side_effect=URLError("down")):
            with self.assertRaises(EmailNotSent) as ctx:
                send_email(to="a@example.com", subject="S", text="T")
        self.assertEqual(ctx.exception.reason, "URLError")

    @override_settings(EMAIL_PROVIDER="brevo", EMAIL_PROVIDER_API_KEY="")
    def test_missing_key(self):
        with self.assertRaises(EmailNotSent) as ctx:
            send_email(to="a@example.com", subject="S", text="T")
        self.assertEqual(ctx.exception.reason, "missing_api_key")

    @override_settings(EMAIL_PROVIDER="disabled")
    def test_disabled_sends_nothing(self):
        with mock.patch.object(client, "urlopen") as urlopen:
            send_email(to="a@example.com", subject="S", text="T")
        urlopen.assert_not_called()
        self.assertEqual(mail.outbox, [])

    @override_settings(EMAIL_PROVIDER="console")
    def test_console_uses_djangos_mailer(self):
        send_email(to="a@example.com", subject="S", text="T", html="<p>H</p>")
        [message] = mail.outbox
        self.assertEqual(message.to, ["a@example.com"])
        self.assertEqual(message.from_email, "MindCare <mindcare@example.org>")
        self.assertEqual(message.alternatives[0][0], "<p>H</p>")


class AfterCommitTests(TestCase):
    def test_sent_only_after_commit(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            send_email_after_commit(template="t", to="a@example.com", message=MESSAGE)
        self.assertEqual(mail.outbox, [])
        callbacks[0]()
        self.assertEqual(mail.outbox[0].subject, "Subject line")

    @override_settings(EMAIL_SEND_IN_BACKGROUND=True)
    def test_background_thread(self):
        with mock.patch("apps.notifications.services.threading.Thread") as thread:
            with self.captureOnCommitCallbacks(execute=True):
                send_email_after_commit(
                    template="t", to="a@example.com", message=MESSAGE
                )
        thread.assert_called_once()
        self.assertTrue(thread.call_args.kwargs["daemon"])
        thread.return_value.start.assert_called_once()

    def test_unexpected_errors_are_swallowed_and_logged_without_details(self):
        with mock.patch(
            "apps.notifications.services.send_email", side_effect=RuntimeError("x")
        ), self.assertLogs("mindcare.email", level="WARNING") as logs:
            with self.captureOnCommitCallbacks(execute=True):
                send_email_after_commit(
                    template="t", to="secret@example.com", message=MESSAGE
                )
        self.assertIn("RuntimeError", logs.output[0])
        self.assertNotIn("secret@example.com", logs.output[0])
        self.assertNotIn("Plain body", logs.output[0])


def _ids(results):
    return [r.id for r in results]


class EmailCheckTests(TestCase):
    @override_settings(DEBUG=False, EMAIL_PROVIDER="disabled")
    def test_disabled_in_production_warns(self):
        self.assertEqual(_ids(checks.check_email_provider(None)), ["mindcare.W001"])

    @override_settings(
        DEBUG=False,
        EMAIL_PROVIDER="console",
        MAILERS={
            "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}
        },
    )
    def test_console_in_production_fails(self):
        self.assertEqual(_ids(checks.check_email_provider(None)), ["mindcare.E003"])

    @override_settings(EMAIL_PROVIDER="brevo", EMAIL_PROVIDER_API_KEY="")
    def test_provider_without_key_fails(self):
        self.assertEqual(_ids(checks.check_email_provider(None)), ["mindcare.E004"])

    @override_settings(EMAIL_PROVIDER="smtp")
    def test_unknown_provider_fails(self):
        self.assertEqual(_ids(checks.check_email_provider(None)), ["mindcare.E004"])

    @override_settings(DEBUG=False, EMAIL_PROVIDER="resend", EMAIL_PROVIDER_API_KEY="k")
    def test_configured_provider_passes(self):
        self.assertEqual(checks.check_email_provider(None), [])

    @override_settings(DEBUG=True, EMAIL_PROVIDER="console")
    def test_console_in_development_passes(self):
        self.assertEqual(checks.check_email_provider(None), [])
