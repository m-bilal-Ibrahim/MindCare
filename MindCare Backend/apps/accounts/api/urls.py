"""URL routes for the accounts API, included under /api/v1/accounts/."""

from django.urls import path

from apps.accounts.api.views import RegisterView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
]
