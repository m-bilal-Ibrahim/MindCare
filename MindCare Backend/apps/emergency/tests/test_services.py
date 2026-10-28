"""SOS (6.12): one compact file (Phase 2 speed mode, docs/decisions.md
2026-10-28). Happy path per endpoint, permissions, and the safety rules: SOS
never blocks, notifications at most once per 30 minutes, cancel window,
encryption at rest, audit trail, 3-contact limit, location purge."""

from datetime import date, timedelta
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import ApprovalStatus, Role
from apps.audit.models import AccessLog, AuditResource
from apps.emergency import services
from apps.emergency.models import EmergencyContact, Helpline, Hospital, SOSEvent
from apps.ngo.services import create_ngo_profile
from apps.reference.models import City, Country
from apps.relationships.services import accept_request, request_psychologist
from core.testing import (
    make_admin,
    make_patient,
    make_psychologist,
    make_user,
    ngo_profile_data,
)
from core.validators import ServiceNumberValidator

BASE = "/api/v1/emergency/"
CONTACT = {
    "name": "Sara Malik",
    "relationship": "sibling",
    "email": "Sara@Example.com",
    "phone": "03001234567",
    "consent_confirmed": True,
}


def raw_column(table, column, pk):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {column} FROM {table} WHERE id = %s", [pk])  # noqa: S608
        return cursor.fetchone()[0]


class SOSTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.pk_country = Country.objects.get(code="PK")
        self.lahore = City.objects.get(country=self.pk_country, name="Lahore")
        self.patient = make_patient(date_of_birth=date(1994, 5, 5))
        self.patient.country = self.pk_country
        self.patient.city = self.lahore
        self.patient.save(update_fields=["country", "city", "updated_at"])
        self.user = self.patient.user
        self.psych = make_psychologist()
        rel = request_psychologist(
            patient_user=self.user, psychologist_id=self.psych.pk
        )
        accept_request(psychologist_user=self.psych.user, relationship_id=rel.pk)
        self.rel = rel

    def tearDown(self):
        cache.clear()

    def as_patient(self):
        self.client.force_authenticate(self.user)

    def add_contact(self, **overrides):
        self.as_patient()
        return self.client.post(
            BASE + "contacts/", {**CONTACT, **overrides}, format="json"
        )

    def press(self, body=None):
        self.as_patient()
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(BASE + "sos/", body or {}, format="json")


class PressSOSTests(SOSTestCase):
    def test_empty_helplines_still_answer_with_the_emergency_message(self):
        r = self.press({"latitude": 31.520412, "longitude": 74.358749})
        self.assertEqual(r.status_code, 201, r.json())
        body = r.json()
        self.assertIn("local emergency number", body["message"])
        self.assertEqual(body["helplines"], [])
        self.assertEqual(body["hospitals"], [])
        self.assertEqual(body["psychologist"]["id"], self.psych.pk)
        self.assertEqual(body["alert"]["location_source"], "device")
        event = SOSEvent.objects.get()
        self.assertEqual(event.coordinates, "31.52,74.359")
        stored = raw_column("emergency_sosevent", "coordinates", event.pk)
        self.assertNotIn("31.52", stored)  # encrypted at rest

    def test_never_blocks_when_recording_fails(self):
        with mock.patch.object(services, "trigger_sos", side_effect=RuntimeError):
            r = self.press()
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(r.json()["alert"])
        self.assertIn("local emergency number", r.json()["message"])

    def test_bad_coordinates_are_dropped_not_refused(self):
        r = self.press({"latitude": 31.5})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["alert"]["location_source"], "profile_city")

    def test_notifies_contacts_and_psychologist_once_per_30_minutes(self):
        self.add_contact()
        self.press()
        self.assertEqual(
            sorted(m.to[0] for m in mail.outbox),
            sorted(["sara@example.com", self.psych.user.email]),
        )
        to_psych = next(m for m in mail.outbox if m.to[0] == self.psych.user.email)
        self.assertNotIn(self.user.full_name, to_psych.subject + to_psych.body)
        self.assertIn(self.patient.pseudonym, to_psych.body)
        mail.outbox.clear()
        second = self.press().json()["alert"]
        self.assertEqual(mail.outbox, [])
        self.assertEqual(second["contacts_notified"], 0)
        self.assertEqual(SOSEvent.objects.count(), 2)

    def test_only_patients_can_press(self):
        self.client.force_authenticate(self.psych.user)
        self.assertEqual(self.client.post(BASE + "sos/", {}).status_code, 403)

    def test_resources_match_country_city_and_approved_ngos(self):
        Helpline.objects.create(
            country=self.pk_country, name="Test Line", number="1122"
        )
        Helpline.objects.create(name="Anywhere Line", number="+44 20 1234")
        Helpline.objects.create(
            country=Country.objects.get(code="GB"), name="Other Line", number="999"
        )
        Hospital.objects.create(
            city=self.lahore,
            name="Test Hospital",
            phone="042 1234",
            address="Main Road, Lahore",
        )
        for status in (ApprovalStatus.APPROVED, ApprovalStatus.PENDING):
            ngo_user = make_user(role=Role.NGO, approval_status=status)
            create_ngo_profile(
                user=ngo_user,
                **ngo_profile_data(
                    organization_name=f"Org {status}",
                    registration_number=f"SECP-{status[:3].upper()}-1",
                ),
            )
        self.as_patient()
        body = self.client.get(BASE + "resources/").json()
        self.assertEqual(
            sorted(h["name"] for h in body["helplines"]), ["Anywhere Line", "Test Line"]
        )
        self.assertEqual([h["name"] for h in body["hospitals"]], ["Test Hospital"])
        self.assertEqual(
            [n["organization_name"] for n in body["ngos"]], ["Org approved"]
        )
        self.assertNotIn("official_email", body["ngos"][0])


class CancelTests(SOSTestCase):
    def test_cancel_within_five_minutes_emails_contacts(self):
        self.add_contact()
        alert = self.press().json()["alert"]
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(f"{BASE}sos/{alert['id']}/cancel/")
        self.assertEqual(r.json()["status"], "cancelled")
        self.assertEqual([m.to[0] for m in mail.outbox], ["sara@example.com"])

    def test_cannot_cancel_after_the_window_or_someone_elses(self):
        alert = self.press().json()["alert"]
        SOSEvent.objects.filter(pk=alert["id"]).update(
            created_at=timezone.now() - timedelta(minutes=6)
        )
        r = self.client.post(f"{BASE}sos/{alert['id']}/cancel/")
        self.assertEqual(r.status_code, 400)
        self.client.force_authenticate(make_patient().user)
        self.assertEqual(
            self.client.post(f"{BASE}sos/{alert['id']}/cancel/").status_code, 404
        )


class ContactTests(SOSTestCase):
    def test_add_list_update_delete_encrypted_and_audited(self):
        r = self.add_contact()
        self.assertEqual(r.status_code, 201, r.json())
        self.assertEqual(r.json()["phone"], "+923001234567")
        self.assertEqual(r.json()["email"], "sara@example.com")
        pk = r.json()["id"]
        for column in ("name", "email", "phone"):
            self.assertNotIn(
                "Sara", raw_column("emergency_emergencycontact", column, pk)
            )
            self.assertNotIn(
                "example", raw_column("emergency_emergencycontact", column, pk)
            )
        r = self.client.patch(
            f"{BASE}contacts/{pk}/", {"name": "Sara Khan"}, format="json"
        )
        self.assertEqual(r.json()["name"], "Sara Khan")
        self.assertEqual(len(self.client.get(BASE + "contacts/").json()), 1)
        self.assertEqual(self.client.delete(f"{BASE}contacts/{pk}/").status_code, 204)
        self.assertEqual(
            AccessLog.objects.filter(
                resource_type=AuditResource.EMERGENCY_CONTACT
            ).count(),
            3,
        )

    def test_validation(self):
        cases = {
            "name": ["Sara 2", "<b>Sara</b>", "   ", "S"],
            "email": ["not-an-email"],
            "phone": ["12ab"],
            "relationship": ["boss"],
        }
        for field, values in cases.items():
            for value in values:
                r = self.add_contact(**{field: value})
                self.assertEqual(r.status_code, 400, (field, value))
                self.assertIn(field, r.json())
        r = self.add_contact(consent_confirmed=False)
        self.assertEqual(
            r.json()["consent_confirmed"],
            ["Confirm this person agreed to be your emergency contact."],
        )
        self.assertEqual(self.add_contact(extra="x").status_code, 400)

    def test_at_most_three_and_only_your_own(self):
        for _ in range(3):
            self.assertEqual(self.add_contact().status_code, 201)
        r = self.add_contact()
        self.assertEqual(
            r.json()["non_field_errors"], ["You can add up to 3 emergency contacts."]
        )
        pk = EmergencyContact.objects.first().pk
        self.client.force_authenticate(make_patient().user)
        self.assertEqual(self.client.delete(f"{BASE}contacts/{pk}/").status_code, 404)


class PsychologistAndAdminTests(SOSTestCase):
    def test_psychologist_sees_own_patients_alerts_audited(self):
        self.press()
        self.client.force_authenticate(self.psych.user)
        rows = self.client.get(BASE + "psychologist/alerts/").json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["relationship_id"], self.rel.pk)
        self.assertEqual(rows[0]["patient_name"], self.user.full_name)
        self.assertTrue(
            AccessLog.objects.filter(resource_type=AuditResource.SOS_EVENT).exists()
        )
        self.client.force_authenticate(make_psychologist().user)
        self.assertEqual(self.client.get(BASE + "psychologist/alerts/").json(), [])
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.get(BASE + "psychologist/alerts/").status_code, 403
        )

    def test_admin_list_detail_follow_up_close(self):
        alert = self.press({"latitude": 31.5204, "longitude": 74.3587}).json()["alert"]
        admin = make_admin()
        self.client.force_authenticate(admin)
        listed = self.client.get(BASE + "admin/sos/?status=open").json()["results"][0]
        self.assertEqual(listed["patient"]["display_name"], self.patient.pseudonym)
        self.assertNotIn("latitude", listed)
        detail = self.client.get(f"{BASE}admin/sos/{alert['id']}/").json()
        self.assertEqual(detail["patient"]["display_name"], self.user.full_name)
        self.assertEqual((detail["latitude"], detail["longitude"]), (31.52, 74.359))
        self.assertTrue(
            AccessLog.objects.filter(
                actor_id=admin.pk, resource_type=AuditResource.SOS_EVENT
            ).exists()
        )
        r = self.client.post(f"{BASE}admin/sos/{alert['id']}/follow-up/")
        self.assertEqual(r.json()["status"], "followed_up")
        r = self.client.post(
            f"{BASE}admin/sos/{alert['id']}/close/",
            {"outcome": "patient_safe"},
            format="json",
        )
        self.assertEqual(
            (r.json()["status"], r.json()["outcome"]), ("closed", "patient_safe")
        )
        again = self.client.post(
            f"{BASE}admin/sos/{alert['id']}/close/", {"outcome": "other"}, format="json"
        )
        self.assertEqual(again.status_code, 400)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(BASE + "admin/sos/").status_code, 403)

    def test_purge_clears_old_coordinates(self):
        alert = self.press({"latitude": 10, "longitude": 10}).json()["alert"]
        SOSEvent.objects.filter(pk=alert["id"]).update(
            created_at=timezone.now() - timedelta(days=91)
        )
        self.assertEqual(services.purge_old_locations(), 1)
        self.assertEqual(SOSEvent.objects.get(pk=alert["id"]).coordinates, None)


class ServiceNumberRuleTests(SimpleTestCase):
    def test_rule(self):
        check = ServiceNumberValidator("Number")
        for ok in ("1122", "15", "+92 42 111-222-333"):
            check(ok)
        for bad in ("12a", "1", "+", "<1122>", "1" * 21):
            with self.assertRaises(ValidationError, msg=bad):
                check(bad)
