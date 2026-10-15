"""admin-panel-2: admin city verification (list unverified, verify, merge, reject)."""

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.ngo.models import NGOServiceArea
from apps.ngo.services import create_ngo_profile
from apps.reference import selectors, services
from apps.reference.models import City, Country
from core.exceptions import DomainValidationError
from core.testing import (
    make_admin,
    make_patient,
    make_psychologist,
    make_user,
    ngo_profile_data,
)

CITIES = "/api/v1/reference/admin/cities/"


def url(city_id, action):
    return f"{CITIES}{city_id}/{action}/"


class CityServiceTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.pk = Country.objects.get(code="PK")
        self.lahore = City.objects.get(country=self.pk, name="Lahore")

    def typo_city(self, name="Lahor"):
        return City.objects.create(country=self.pk, name=name)

    def test_verify(self):
        city = self.typo_city("Okara Cantt")
        services.verify_city(actor=self.admin, city_id=city.pk)
        city.refresh_from_db()
        self.assertTrue(city.is_verified)
        with self.assertRaises(DomainValidationError):
            services.verify_city(actor=self.admin, city_id=city.pk)

    def test_merge_moves_profiles_and_dedupes_service_areas(self):
        typo = self.typo_city()
        psychologist = make_psychologist(city="Lahor")
        self.assertEqual(psychologist.city_id, typo.pk)
        ngo = create_ngo_profile(
            user=make_user(role=Role.NGO),
            **ngo_profile_data(
                city="Lahor",
                service_areas=[
                    {"country": self.pk, "city": "Lahor"},
                    {"country": self.pk, "city": "Lahore"},
                ],
            ),
        )
        self.assertEqual(selectors.admin_cities().get(pk=typo.pk).usage_count, 3)

        services.merge_city(actor=self.admin, city_id=typo.pk, into_id=self.lahore.pk)

        self.assertFalse(City.objects.filter(pk=typo.pk).exists())
        psychologist.refresh_from_db()
        ngo.refresh_from_db()
        self.assertEqual(psychologist.city_id, self.lahore.pk)
        self.assertEqual(ngo.city_id, self.lahore.pk)
        self.assertEqual(
            list(
                NGOServiceArea.objects.filter(ngo=ngo).values_list("city_id", flat=True)
            ),
            [self.lahore.pk],
        )

    def test_merge_rules(self):
        typo = self.typo_city()
        other_country = City.objects.create(
            country=Country.objects.get(code="GB"), name="London"
        )
        cases = [
            (typo.pk, typo.pk, "into"),
            (typo.pk, 999999, "into"),
            (typo.pk, other_country.pk, "into"),
            (self.lahore.pk, typo.pk, "city"),  # a verified city isn't merged away
        ]
        for source, target, key in cases:
            with self.subTest(source=source, target=target):
                with self.assertRaises(DomainValidationError) as ctx:
                    services.merge_city(
                        actor=self.admin, city_id=source, into_id=target
                    )
                self.assertIn(key, ctx.exception.errors)
        with self.assertRaises(services.CityNotFound):
            services.merge_city(actor=self.admin, city_id=999999, into_id=typo.pk)

    def test_reject_only_unused_unverified(self):
        unused = self.typo_city("Spamtown")
        services.reject_city(actor=self.admin, city_id=unused.pk)
        self.assertFalse(City.objects.filter(pk=unused.pk).exists())

        self.typo_city()
        make_psychologist(city="Lahor")
        used = City.objects.get(name="Lahor")
        with self.assertRaises(DomainValidationError) as ctx:
            services.reject_city(actor=self.admin, city_id=used.pk)
        self.assertIn("Merge it", ctx.exception.errors["city"][0])
        with self.assertRaises(DomainValidationError):
            services.reject_city(actor=self.admin, city_id=self.lahore.pk)

    def test_patient_city_counts_as_usage(self):
        typo = self.typo_city()
        patient = make_patient()
        patient.city = typo
        patient.save(update_fields=["city"])
        with self.assertRaises(DomainValidationError):
            services.reject_city(actor=self.admin, city_id=typo.pk)


class AdminCitiesAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.force_authenticate(make_admin())
        self.pk = Country.objects.get(code="PK")

    def test_lists_unverified_oldest_first_by_default(self):
        first = City.objects.create(country=self.pk, name="Firstville")
        second = City.objects.create(country=self.pk, name="Abbottville")
        r = self.client.get(CITIES)
        self.assertEqual(r.status_code, 200)
        ids = [row["id"] for row in r.json()["results"]]
        self.assertEqual(ids, [first.pk, second.pk])
        row = r.json()["results"][0]
        self.assertEqual(
            set(row),
            {"id", "name", "country", "country_name", "is_verified", "usage_count"},
        )
        self.assertEqual(row["usage_count"], 0)

    def test_filters_and_query_validation(self):
        City.objects.create(country=self.pk, name="Firstville")
        r = self.client.get(
            CITIES, {"status": "all", "country": "PK", "search": "lahore"}
        )
        self.assertEqual([c["name"] for c in r.json()["results"]], ["Lahore"])
        for params in ({"status": "nope"}, {"country": "pakistan"}, {"country": "p1"}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(CITIES, params).status_code, 400)

    def test_verify_merge_reject_endpoints(self):
        lahore = City.objects.get(country=self.pk, name="Lahore")
        new = City.objects.create(country=self.pk, name="Newtown")
        r = self.client.post(url(new.pk, "verify"))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["is_verified"])
        self.assertEqual(self.client.post(url(new.pk, "verify")).status_code, 400)

        typo = City.objects.create(country=self.pk, name="Lahor")
        r = self.client.post(url(typo.pk, "merge"), {"into": lahore.pk}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], lahore.pk)

        spam = City.objects.create(country=self.pk, name="Spamtown")
        self.assertEqual(self.client.post(url(spam.pk, "reject")).status_code, 204)
        self.assertEqual(self.client.post(url(spam.pk, "reject")).status_code, 404)

    def test_merge_body_validation(self):
        typo = City.objects.create(country=self.pk, name="Lahor")
        for body in ({}, {"into": "x"}, {"into": 0}, {"into": 1, "extra": 1}):
            with self.subTest(body=body):
                r = self.client.post(url(typo.pk, "merge"), body, format="json")
                self.assertEqual(r.status_code, 400)

    def test_non_admins_refused(self):
        for user in (make_patient().user, make_psychologist().user):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(CITIES).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(CITIES).status_code, 401)

    def test_admin_on_temporary_password_refused(self):
        self.client.force_authenticate(make_admin(must_change_password=True))
        self.assertEqual(self.client.get(CITIES).status_code, 403)
