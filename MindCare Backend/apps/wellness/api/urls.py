"""URL routes for the wellness library, included under /api/v1/wellness/."""

from django.urls import path

from apps.wellness.api.admin_views import (
    AdminItemAudioView,
    AdminItemDetailView,
    AdminItemImageView,
    AdminItemListView,
)
from apps.wellness.api.views import (
    FavouriteListView,
    FavouriteView,
    ItemDetailView,
    ItemListView,
)

app_name = "wellness"

urlpatterns = [
    # Patients and approved psychologists.
    path("items/", ItemListView.as_view(), name="items"),
    path("items/<int:pk>/", ItemDetailView.as_view(), name="item"),
    # Patients only.
    path("items/<int:pk>/favourite/", FavouriteView.as_view(), name="favourite"),
    path("favourites/", FavouriteListView.as_view(), name="favourites"),
    # Admins only.
    path("admin/items/", AdminItemListView.as_view(), name="admin-items"),
    path("admin/items/<int:pk>/", AdminItemDetailView.as_view(), name="admin-item"),
    path(
        "admin/items/<int:pk>/image/",
        AdminItemImageView.as_view(),
        name="admin-item-image",
    ),
    path(
        "admin/items/<int:pk>/audio/",
        AdminItemAudioView.as_view(),
        name="admin-item-audio",
    ),
]
