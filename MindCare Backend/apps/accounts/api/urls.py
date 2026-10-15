"""URL routes for the accounts API, included under /api/v1/accounts/."""

from django.urls import path

from apps.accounts.api.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    RefreshView,
    RegisterView,
)

from apps.accounts.api.admin_views import (
    AdminAccountsView,
    AdminPsychologistsView,
    DeactivateAdminView,
    DemoteSelfView,
    PromoteAdminView,
    ReactivateAdminView,
    AdminUserDetailView,
    AdminUsersView,
    ApproveAccountView,
    CredentialDocumentLinkView,
    DeactivateUserView,
    OverviewView,
    PendingAccountsView,
    ReactivateUserView,
    RejectAccountView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    # Admin console (6.3): admins only.
    path("admin/pending/", PendingAccountsView.as_view(), name="admin-pending"),
    path(
        "admin/<int:user_id>/approve/",
        ApproveAccountView.as_view(),
        name="admin-approve",
    ),
    path(
        "admin/<int:user_id>/reject/", RejectAccountView.as_view(), name="admin-reject"
    ),
    path(
        "admin/documents/<int:document_id>/",
        CredentialDocumentLinkView.as_view(),
        name="admin-document",
    ),
    path("admin/overview/", OverviewView.as_view(), name="admin-overview"),
    path("admin/users/", AdminUsersView.as_view(), name="admin-users"),
    path(
        "admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user"
    ),
    path(
        "admin/users/<int:user_id>/deactivate/",
        DeactivateUserView.as_view(),
        name="admin-user-deactivate",
    ),
    path(
        "admin/users/<int:user_id>/reactivate/",
        ReactivateUserView.as_view(),
        name="admin-user-reactivate",
    ),
    path(
        "admin/psychologists/",
        AdminPsychologistsView.as_view(),
        name="admin-psychologists",
    ),
    # Super-admin workflow: super-admins only.
    path("admin/admins/", AdminAccountsView.as_view(), name="admin-admins"),
    path("admin/admins/me/demote/", DemoteSelfView.as_view(), name="admin-demote-self"),
    path(
        "admin/admins/<int:user_id>/promote/",
        PromoteAdminView.as_view(),
        name="admin-promote",
    ),
    path(
        "admin/admins/<int:user_id>/deactivate/",
        DeactivateAdminView.as_view(),
        name="admin-admin-deactivate",
    ),
    path(
        "admin/admins/<int:user_id>/reactivate/",
        ReactivateAdminView.as_view(),
        name="admin-admin-reactivate",
    ),
]
