"""Admin console API (6.3). Thin views: parse -> service/selector -> serialize.

Every endpoint: IsAuthenticated + IsAdmin + PasswordChangeNotRequired, throttle
`admin` (120/min per user). Admin management also needs IsSuperAdmin.
Approvals follow MindCare Web/docs/admin-approvals-api-contract.md.
"""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts import selectors, services
from apps.accounts.api.admin_serializers import (
    AdminAccountSerializer,
    AdminPsychologistSerializer,
    AdminPsychologistsQuerySerializer,
    CreateAdminSerializer,
    CreatedAdminSerializer,
    AdminUserDetailSerializer,
    AdminUserListItemSerializer,
    AdminUsersQuerySerializer,
    DeactivateSerializer,
    DocumentLinkSerializer,
    OverviewSerializer,
    PendingAccountSerializer,
    PendingQuerySerializer,
    RejectSerializer,
    ReviewResultSerializer,
)
from apps.accounts.models import ApprovalStatus
from apps.psychologists import services as psychologist_services
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsAdmin, IsSuperAdmin, PasswordChangeNotRequired
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError


class AdminRateThrottle(UserRateThrottle):
    scope = "admin"


class AdminAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin, PasswordChangeNotRequired]
    throttle_classes = [AdminRateThrottle]


class SuperAdminAPIView(AdminAPIView):
    permission_classes = [*AdminAPIView.permission_classes, IsSuperAdmin]


def _domain_errors(exc):
    return ValidationError(exc.errors, code=exc.code)


class PendingAccountsView(AdminAPIView):
    @extend_schema(
        parameters=[PendingQuerySerializer],
        responses={200: PendingAccountSerializer(many=True)},
        description="Pending psychologist or NGO applications, oldest first.",
    )
    def get(self, request):
        query = PendingQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        accounts = selectors.pending_accounts(role=query.validated_data["role"])
        return Response(PendingAccountSerializer(accounts, many=True).data)


class _ReviewView(AdminAPIView):
    decision = None
    body_serializer = None

    def post(self, request, user_id):
        reason = None
        if self.body_serializer is not None:
            body = self.body_serializer(data=request.data)
            body.is_valid(raise_exception=True)
            reason = body.validated_data.get("reason")
        try:
            user = services.review_pending_account(
                admin=request.user,
                user_id=user_id,
                decision=self.decision,
                reason=reason,
            )
        except services.AccountNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain_errors(exc) from exc
        return Response(ReviewResultSerializer(user).data)


class ApproveAccountView(_ReviewView):
    decision = ApprovalStatus.APPROVED

    @extend_schema(
        request=None,
        responses={
            200: ReviewResultSerializer,
            400: OpenApiResponse(description="Not pending, or deactivated."),
            404: OpenApiResponse(description="No such psychologist / NGO account."),
        },
    )
    def post(self, request, user_id):
        return super().post(request, user_id)


class RejectAccountView(_ReviewView):
    decision = ApprovalStatus.REJECTED
    body_serializer = RejectSerializer

    @extend_schema(
        request=RejectSerializer,
        responses={
            200: ReviewResultSerializer,
            400: OpenApiResponse(
                description="Not pending, deactivated, or bad reason."
            ),
            404: OpenApiResponse(description="No such psychologist / NGO account."),
        },
        description="Rejecting ends the account's care relationships.",
    )
    def post(self, request, user_id):
        return super().post(request, user_id)


class CredentialDocumentLinkView(AdminAPIView):
    @extend_schema(
        responses={200: DocumentLinkSerializer, 404: OpenApiResponse()},
        description=(
            "A signed link to one credential file, valid for a few minutes. Each "
            "call is recorded in the access audit trail first."
        ),
    )
    def get(self, request, document_id):
        try:
            document, url, expires = psychologist_services.open_credential_document(
                admin=request.user,
                document_id=document_id,
                ip=request.META.get("REMOTE_ADDR"),
            )
        except psychologist_services.DocumentNotFound as exc:
            raise Http404 from exc
        return Response(
            DocumentLinkSerializer(
                {
                    "id": document.pk,
                    "kind": document.kind,
                    "file_type": document.file_type,
                    "url": url,
                    "expires_in": expires,
                }
            ).data
        )


class OverviewView(AdminAPIView):
    @extend_schema(responses={200: OverviewSerializer})
    def get(self, request):
        return Response(OverviewSerializer(selectors.platform_overview()).data)


class AdminUsersView(AdminAPIView):
    @extend_schema(
        parameters=[AdminUsersQuerySerializer],
        responses={200: AdminUserListItemSerializer(many=True)},
        description=(
            "Every non-admin account, newest first, paginated. Patients are found "
            "by pseudonym only, and private patients show no name or email."
        ),
    )
    def get(self, request):
        query = AdminUsersQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        users = selectors.admin_users(
            role=query.validated_data.get("role"),
            status=query.validated_data.get("status"),
            search=(query.validated_data.get("search") or "").strip() or None,
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(users, request, view=self)
        return paginator.get_paginated_response(
            AdminUserListItemSerializer(page, many=True).data
        )


class AdminUserDetailView(AdminAPIView):
    @extend_schema(
        responses={200: AdminUserDetailSerializer, 404: OpenApiResponse()},
        description=(
            "Opening a private patient reveals their real name and email; the "
            "reveal is recorded in the access audit trail."
        ),
    )
    def get(self, request, user_id):
        user = selectors.admin_user(user_id=user_id)
        if user is None:
            raise Http404
        return Response(
            AdminUserDetailSerializer(user, context={"request": request}).data
        )


class DeactivateUserView(AdminAPIView):
    @extend_schema(
        request=DeactivateSerializer,
        responses={
            200: ReviewResultSerializer,
            400: OpenApiResponse(),
            404: OpenApiResponse(),
        },
        description="Ends their care relationships. Admin accounts can't be changed here.",
    )
    def post(self, request, user_id):
        body = DeactivateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            user = services.deactivate_account(
                admin=request.user,
                user_id=user_id,
                reason=body.validated_data.get("reason"),
            )
        except services.AccountNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain_errors(exc) from exc
        return Response(ReviewResultSerializer(user).data)


class ReactivateUserView(AdminAPIView):
    @extend_schema(
        request=None,
        responses={
            200: ReviewResultSerializer,
            400: OpenApiResponse(),
            404: OpenApiResponse(),
        },
        description="Relationships that ended stay ended.",
    )
    def post(self, request, user_id):
        try:
            user = services.reactivate_account(admin=request.user, user_id=user_id)
        except services.AccountNotFound as exc:
            raise Http404 from exc
        except DomainValidationError as exc:
            raise _domain_errors(exc) from exc
        return Response(ReviewResultSerializer(user).data)


class AdminPsychologistsView(AdminAPIView):
    @extend_schema(
        parameters=[AdminPsychologistsQuerySerializer],
        responses={200: AdminPsychologistSerializer(many=True)},
        description=(
            "Every psychologist with active / accepting status and patient counts "
            "only (never who the patients are). Paginated, by name."
        ),
    )
    def get(self, request):
        query = AdminPsychologistsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        profiles = selectors.admin_psychologists(
            accepting=query.validated_data.get("accepting"),
            status=query.validated_data.get("status"),
            search=query.validated_data.get("search") or None,
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(profiles, request, view=self)
        return paginator.get_paginated_response(
            AdminPsychologistSerializer(page, many=True).data
        )


# --- Super-admin workflow: managing admin accounts ------------------------------


class AdminAccountsView(SuperAdminAPIView):
    @extend_schema(
        responses={200: AdminAccountSerializer(many=True)},
        description="Every admin account, oldest first. Super-admins only.",
    )
    def get(self, request):
        return Response(
            AdminAccountSerializer(selectors.admin_accounts(), many=True).data
        )

    @extend_schema(
        request=CreateAdminSerializer,
        responses={201: CreatedAdminSerializer, 400: OpenApiResponse()},
        description=(
            "Create an ordinary admin. The response carries a one-time temporary "
            "password, shown only here; the new admin must change it "
            "(POST /accounts/password/change/) before any admin endpoint works."
        ),
    )
    def post(self, request):
        body = CreateAdminSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            user, password = services.create_admin_account(
                actor=request.user, **body.validated_data
            )
        except services.DuplicateEmailError as exc:
            raise ValidationError({"email": [str(exc)]}) from exc
        data = AdminAccountSerializer(user).data
        data["temporary_password"] = password
        return Response(data, status=status.HTTP_201_CREATED)


class _AdminAccountActionView(SuperAdminAPIView):
    service = None

    @extend_schema(
        request=None,
        responses={
            200: AdminAccountSerializer,
            400: OpenApiResponse(description="The rule this action would break."),
            404: OpenApiResponse(description="No such admin account."),
        },
    )
    def post(self, request, user_id):
        try:
            user = type(self).service(actor=request.user, user_id=user_id)
        except services.AccountNotFound as exc:
            raise Http404 from exc
        except services.NotSuperAdmin as exc:
            raise PermissionDenied(IsSuperAdmin.message) from exc
        except DomainValidationError as exc:
            raise _domain_errors(exc) from exc
        return Response(AdminAccountSerializer(user).data)


class PromoteAdminView(_AdminAccountActionView):
    service = services.promote_admin


class DeactivateAdminView(_AdminAccountActionView):
    service = services.deactivate_admin


class ReactivateAdminView(_AdminAccountActionView):
    service = services.reactivate_admin


class DemoteSelfView(SuperAdminAPIView):
    @extend_schema(
        request=None,
        responses={
            200: AdminAccountSerializer,
            400: OpenApiResponse(description="You're the only super-admin."),
        },
        description="Step down to ordinary admin. The last super-admin can't.",
    )
    def post(self, request):
        try:
            user = services.demote_self(actor=request.user)
        except services.NotSuperAdmin as exc:
            raise PermissionDenied(IsSuperAdmin.message) from exc
        except DomainValidationError as exc:
            raise _domain_errors(exc) from exc
        return Response(AdminAccountSerializer(user).data)
