"""URL routes for the Motivation Corner, included under /api/v1/motivation/."""

from django.urls import path

from apps.motivation.api.views import QuoteListView, RandomQuoteView

app_name = "motivation"

urlpatterns = [
    path("quotes/", QuoteListView.as_view(), name="quotes"),
    path("quotes/random/", RandomQuoteView.as_view(), name="quote-random"),
]
