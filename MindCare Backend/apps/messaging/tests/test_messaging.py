"""Secure messaging: one compact file (speed mode, docs/decisions.md 2026-10-28).
Happy path per endpoint, participants only (admin / other psychologist 404),
care ended -> read-only, former psychologist has no access, encryption at rest,
the 5-minute delete, the send throttle, validation, and the notification that
carries no content."""

from datetime import timedelta

from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.audit.models import AccessLog, AuditAction, AuditResource
from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification, NotificationType
from apps.relationships.services import (
    accept_request,
    patient_end_relationship,
    request_psychologist,
)
from core.testing import make_admin, make_patient, make_psychologist

BASE = "/api/v1/messaging/"
TEXT = "Can we talk about my sleep diary on Friday?"


def in_care(psych, patient=None):
    patient = patient or make_patient()
    rel = request_psychologist(patient_user=patient.user, psychologist_id=psych.pk)
    accept_request(psychologist_user=psych.user, relationship_id=rel.pk)
    return patient, rel


class MessagingTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.psych = make_psychologist(full_name="Sara Ahmed")
        self.patient, self.rel = in_care(self.psych)
        self.conv = Conversation.objects.get(
            patient=self.patient, psychologist=self.psych
        )

    def tearDown(self):
        cache.clear()

    def as_(self, user):
        self.client.force_authenticate(user)

    def url(self, suffix="", conv=None):
        return f"{BASE}conversations/{(conv or self.conv).pk}/{suffix}"

    def send(self, user, body=TEXT):
        self.as_(user)
        return self.client.post(self.url("messages/"), {"body": body}, format="json")


class FlowTests(MessagingTestCase):
    def test_conversation_created_on_accept_and_listed_for_both(self):
        self.as_(self.patient.user)
        rows = self.client.get(f"{BASE}conversations/").json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["other_party"]["name"], "Sara Ahmed")
        self.assertTrue(rows[0]["can_send"])
        self.as_(self.psych.user)
        rows = self.client.get(f"{BASE}conversations/").json()
        self.assertEqual(rows[0]["other_party"]["name"], self.patient.user.full_name)

    def test_send_read_page_unread_and_mark_read(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.send(self.patient.user, "  " + TEXT + "  ")
        self.assertEqual(r.status_code, 201, r.json())
        self.assertEqual(r.json()["body"], TEXT)
        self.assertTrue(r.json()["is_mine"])
        self.assertTrue(r.json()["can_delete"])

        self.as_(self.psych.user)
        rows = self.client.get(f"{BASE}conversations/").json()
        self.assertEqual(rows[0]["unread_count"], 1)
        self.assertNotIn(TEXT, str(rows))  # never the text in the list
        self.assertEqual(self.client.get(f"{BASE}unread-count/").json()["count"], 1)
        page = self.client.get(self.url("messages/")).json()
        self.assertEqual(page["results"][0]["body"], TEXT)
        self.assertFalse(page["results"][0]["is_mine"])
        self.assertIsNone(page["next_before"])
        self.assertEqual(self.client.post(self.url("read/")).json()["count"], 1)
        self.assertEqual(self.client.get(f"{BASE}unread-count/").json()["count"], 0)
        self.assertEqual(
            AccessLog.objects.filter(
                resource_type=AuditResource.MESSAGE, action=AuditAction.CREATE
            ).count(),
            1,
        )

    def test_cursor_pagination_newest_first(self):
        for i in range(5):
            self.send(self.patient.user, f"Message number {i}")
        page = self.client.get(self.url("messages/"), {"limit": 2}).json()
        self.assertEqual(
            [m["body"] for m in page["results"]],
            ["Message number 4", "Message number 3"],
        )
        older = self.client.get(
            self.url("messages/"), {"limit": 2, "before": page["next_before"]}
        ).json()
        self.assertEqual(older["results"][0]["body"], "Message number 2")

    def test_detail_has_safety_notice(self):
        self.as_(self.patient.user)
        data = self.client.get(self.url()).json()
        self.assertIn("SOS", data["safety_notice"])

    def test_notification_without_content(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.send(self.patient.user)
        note = Notification.objects.get(recipient=self.psych.user)
        self.assertEqual(note.type, NotificationType.NEW_MESSAGE)
        self.assertEqual(note.body, "You have a new message.")
        self.assertEqual(note.target_id, self.conv.pk)
        self.assertNotIn("sleep", note.title + note.body)
        self.assertFalse(Notification.objects.filter(recipient=self.patient.user))

    def test_body_encrypted_at_rest(self):
        self.send(self.patient.user)
        with connection.cursor() as cur:
            cur.execute("SELECT body FROM messaging_message")
            raw = cur.fetchone()[0]
        self.assertNotIn("sleep", raw)
        self.assertEqual(Message.objects.get().body, TEXT)


class AccessTests(MessagingTestCase):
    def test_outsiders_get_404(self):
        other = make_psychologist()
        for user in (make_admin(), other.user, make_patient().user):
            self.as_(user)
            self.assertEqual(self.client.get(self.url()).status_code, 404)
            self.assertEqual(self.client.get(self.url("messages/")).status_code, 404)
            r = self.client.post(self.url("messages/"), {"body": TEXT}, format="json")
            self.assertEqual(r.status_code, 404)
            self.assertEqual(self.client.post(self.url("read/")).status_code, 404)
            self.assertEqual(self.client.get(f"{BASE}conversations/").json(), [])

    def test_care_ended_read_only_for_patient_and_closed_for_psychologist(self):
        self.send(self.patient.user)
        patient_end_relationship(patient_user=self.patient.user, confirm=True)
        self.as_(self.patient.user)
        self.assertEqual(self.client.get(self.url("messages/")).status_code, 200)
        self.assertFalse(self.client.get(self.url()).json()["can_send"])
        r = self.send(self.patient.user)
        self.assertEqual(r.status_code, 403)
        self.assertIn("read-only", r.json()["detail"])
        self.as_(self.psych.user)
        self.assertEqual(self.client.get(self.url("messages/")).status_code, 404)
        self.assertEqual(self.client.get(f"{BASE}conversations/").json(), [])
        self.assertEqual(self.client.get(f"{BASE}unread-count/").json()["count"], 0)

    def test_care_resumed_reuses_conversation(self):
        patient_end_relationship(patient_user=self.patient.user, confirm=True)
        in_care(self.psych, self.patient)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(self.send(self.psych.user).status_code, 201)

    def test_paused_psychologist_has_no_access(self):
        self.psych.user.approval_status = "pending"
        self.psych.user.save(update_fields=["approval_status"])
        self.assertEqual(self.send(self.psych.user).status_code, 404)


class DeleteTests(MessagingTestCase):
    def test_delete_within_five_minutes_wipes_body_and_audits(self):
        mid = self.send(self.patient.user).json()["id"]
        r = self.client.delete(self.url(f"messages/{mid}/"))
        self.assertEqual(r.status_code, 204)
        msg = Message.objects.get(pk=mid)
        self.assertIsNotNone(msg.deleted_at)
        self.assertEqual(msg.body, "")
        page = self.client.get(self.url("messages/")).json()
        self.assertTrue(page["results"][0]["is_deleted"])
        self.assertIsNone(page["results"][0]["body"])
        self.assertTrue(
            AccessLog.objects.filter(
                resource_type=AuditResource.MESSAGE, action=AuditAction.DELETE
            ).exists()
        )
        self.assertEqual(
            self.client.delete(self.url(f"messages/{mid}/")).status_code, 400
        )

    def test_delete_after_five_minutes_or_others_message_refused(self):
        mid = self.send(self.patient.user).json()["id"]
        self.as_(self.psych.user)
        self.assertEqual(
            self.client.delete(self.url(f"messages/{mid}/")).status_code, 403
        )
        Message.objects.filter(pk=mid).update(
            created_at=timezone.now() - timedelta(minutes=6)
        )
        self.as_(self.patient.user)
        r = self.client.delete(self.url(f"messages/{mid}/"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("5 minutes", str(r.json()))


class ValidationAndThrottleTests(MessagingTestCase):
    def test_invalid_bodies(self):
        for body in ("", "   ", "x" * 2001, "<script>alert(1)</script>", "?!..."):
            r = self.send(self.patient.user, body)
            self.assertEqual(r.status_code, 400, body)
            self.assertIn("body", r.json())
        r = self.client.post(
            self.url("messages/"), {"body": TEXT, "sender": 1}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.send(self.patient.user, "ok").status_code, 201)

    def test_send_throttle_30_per_10_minutes(self):
        from apps.messaging.api.views import MessageSendThrottle

        self.assertEqual(MessageSendThrottle().parse_rate("30/10m"), (30, 600))
        codes = [self.send(self.patient.user).status_code for _ in range(31)]
        self.assertEqual(codes.count(201), 30)
        self.assertEqual(codes[-1], 429)
        # reads aren't counted against the send limit
        self.assertEqual(self.client.get(self.url("messages/")).status_code, 200)
