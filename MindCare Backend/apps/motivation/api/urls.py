"""URL routes for the Motivation Corner, included under /api/v1/motivation/."""

from django.urls import path

from apps.motivation.api.views import (
    DuaDetailView,
    DuaListView,
    QuoteListView,
    RandomQuoteView,
    ReligiousPreferenceView,
    SurahDetailView,
    SurahListView,
)

from apps.motivation.api.admin_views import (
    AdminDuaAudioView,
    AdminDuaDetailView,
    AdminDuaListView,
    AdminQuoteDetailView,
    AdminQuoteListView,
    AdminSurahAudioView,
    AdminSurahDetailView,
    AdminSurahListView,
)

app_name = "motivation"

urlpatterns = [
    path("quotes/", QuoteListView.as_view(), name="quotes"),
    path("quotes/random/", RandomQuoteView.as_view(), name="quote-random"),
    # 6.10 religious content: patients only, after opting in.
    path(
        "religious/preference/",
        ReligiousPreferenceView.as_view(),
        name="religious-preference",
    ),
    path("duas/", DuaListView.as_view(), name="duas"),
    path("duas/<int:pk>/", DuaDetailView.as_view(), name="dua"),
    path("surahs/", SurahListView.as_view(), name="surahs"),
    path("surahs/<int:number>/", SurahDetailView.as_view(), name="surah"),
    # Admin content console (admin-panel-2): admins only.
    path("admin/quotes/", AdminQuoteListView.as_view(), name="admin-quotes"),
    path("admin/quotes/<int:pk>/", AdminQuoteDetailView.as_view(), name="admin-quote"),
    path("admin/duas/", AdminDuaListView.as_view(), name="admin-duas"),
    path("admin/duas/<int:pk>/", AdminDuaDetailView.as_view(), name="admin-dua"),
    path(
        "admin/duas/<int:pk>/audio/",
        AdminDuaAudioView.as_view(),
        name="admin-dua-audio",
    ),
    path("admin/surahs/", AdminSurahListView.as_view(), name="admin-surahs"),
    path("admin/surahs/<int:pk>/", AdminSurahDetailView.as_view(), name="admin-surah"),
    path(
        "admin/surahs/<int:pk>/audio/",
        AdminSurahAudioView.as_view(),
        name="admin-surah-audio",
    ),
]
