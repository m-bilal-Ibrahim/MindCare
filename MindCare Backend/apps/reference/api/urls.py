"""URL routes for the reference API, included under /api/v1/reference/."""

from django.urls import path

from apps.reference.api.views import (
    CityListView,
    CountryListView,
    LanguageListView,
    SpecializationListView,
)

from apps.reference.api.admin_views import (
    AdminCitiesView,
    MergeCityView,
    RejectCityView,
    VerifyCityView,
)

app_name = "reference"

urlpatterns = [
    path("countries/", CountryListView.as_view(), name="countries"),
    path("cities/", CityListView.as_view(), name="cities"),
    path("languages/", LanguageListView.as_view(), name="languages"),
    path("specializations/", SpecializationListView.as_view(), name="specializations"),
    # Admin city verification (admin-panel-2): admins only.
    path("admin/cities/", AdminCitiesView.as_view(), name="admin-cities"),
    path(
        "admin/cities/<int:city_id>/verify/",
        VerifyCityView.as_view(),
        name="admin-city-verify",
    ),
    path(
        "admin/cities/<int:city_id>/merge/",
        MergeCityView.as_view(),
        name="admin-city-merge",
    ),
    path(
        "admin/cities/<int:city_id>/reject/",
        RejectCityView.as_view(),
        name="admin-city-reject",
    ),
]
