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
]
