"""DRF views for the clinical_notes API (Phase 2 module 5: therapy notes).

Views stay thin: parse the request, delegate to services.py (writes and the
audited psychologist reads) or selectors.py (the patient's own progress), then
serialize the result. No business logic here.
"""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.clinical_notes import selectors, services
from apps.clinical_notes.api.serializers import (
    AddendumSerializer,
    NoteCreateSerializer,
    NoteSerializer,
    NoteUpdateSerializer,
    NoteVersionSerializer,
    PatientProgressSerializer,
    ProgressPointSerializer,
    SummarySerializer,
    SummaryWriteSerializer,
)
from core.exceptions import DomainValidationError
from core.pagination import StandardPagination
from core.permissions import IsApprovedPsychologist, IsPatient, IsPsychologist

ERRORS = {
    400: OpenApiResponse(description="Invalid input, or the note is locked."),
    404: OpenApiResponse(description="Not your current patient, or no such note."),
}


def _ip(request):
    return request.META.get("REMOTE_ADDR")


def _run(fn, **kwargs):
    try:
        return fn(**kwargs)
    except (services.NotYourPatient, services.NotFound) as exc:
        raise Http404 from exc
    except DomainValidationError as exc:
        raise ValidationError(exc.errors, code=exc.code) from exc


class NotesWriteThrottle(UserRateThrottle):
    scope = "clinical_notes"


class PsychologistView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]

    def get_throttles(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return [NotesWriteThrottle()]
        return []

    def common(self, relationship_id):
        return {
            "psychologist_user": self.request.user,
            "relationship_id": relationship_id,
            "ip": _ip(self.request),
        }


class NotesView(PsychologistView):
    @extend_schema(
        responses={200: NoteSerializer(many=True), 404: ERRORS[404]},
        description="Every note you wrote for this CURRENT patient (across your "
        "relationships with them), newest first, paginated. Audited.",
    )
    def get(self, request, relationship_id):
        rows = _run(services.list_notes, **self.common(relationship_id))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(NoteSerializer(page, many=True).data)

    @extend_schema(
        request=NoteCreateSerializer,
        responses={201: NoteSerializer, **ERRORS},
        description="Every section is optional, but at least one section, the "
        "progress rating or the risk level is needed. Editable for 24 hours.",
    )
    def post(self, request, relationship_id):
        body = NoteCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        note = _run(
            services.create_note, **self.common(relationship_id), **body.validated_data
        )
        return Response(NoteSerializer(note).data, status=status.HTTP_201_CREATED)


class NoteDetailView(PsychologistView):
    @extend_schema(responses={200: NoteSerializer, 404: ERRORS[404]})
    def get(self, request, relationship_id, note_id):
        note = _run(services.get_note, **self.common(relationship_id), note_id=note_id)
        return Response(NoteSerializer(note).data)

    @extend_schema(
        request=NoteUpdateSerializer,
        responses={200: NoteSerializer, **ERRORS},
        description="Only within 24 hours of writing the note; every save is kept "
        "as a version. After that, add an addendum.",
    )
    def patch(self, request, relationship_id, note_id):
        body = NoteUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        note = _run(
            services.update_note,
            **self.common(relationship_id),
            note_id=note_id,
            **body.validated_data,
        )
        return Response(NoteSerializer(note).data)


class NoteVersionsView(PsychologistView):
    @extend_schema(responses={200: NoteVersionSerializer(many=True), 404: ERRORS[404]})
    def get(self, request, relationship_id, note_id):
        rows = _run(
            services.note_versions, **self.common(relationship_id), note_id=note_id
        )
        return Response(NoteVersionSerializer(rows, many=True).data)


class AddendumView(PsychologistView):
    @extend_schema(
        request=AddendumSerializer,
        responses={201: AddendumSerializer, **ERRORS},
        description="Add to a note at any time. Addenda can't be edited.",
    )
    def post(self, request, relationship_id, note_id):
        body = AddendumSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        addendum = _run(
            services.add_addendum,
            **self.common(relationship_id),
            note_id=note_id,
            text=body.validated_data["text"],
        )
        return Response(
            AddendumSerializer(addendum).data, status=status.HTTP_201_CREATED
        )


class ProgressView(PsychologistView):
    @extend_schema(
        responses={200: ProgressPointSerializer(many=True), 404: ERRORS[404]},
        description="Progress ratings (1-10) and risk levels over time, oldest "
        "first, for a chart. Audited.",
    )
    def get(self, request, relationship_id):
        rows = _run(services.progress, **self.common(relationship_id))
        return Response(ProgressPointSerializer(rows, many=True).data)


class SummaryView(PsychologistView):
    @extend_schema(
        responses={200: SummarySerializer, 404: ERRORS[404]},
        description="The summary you wrote for this patient (text null if none).",
    )
    def get(self, request, relationship_id):
        summary = _run(services.get_summary, **self.common(relationship_id))
        data = {"text": None, "updated_at": None} if summary is None else summary
        return Response(SummarySerializer(data).data)

    @extend_schema(
        request=SummaryWriteSerializer,
        responses={200: SummarySerializer, **ERRORS},
        description="Replace the summary the patient sees. Audited.",
    )
    def put(self, request, relationship_id):
        body = SummaryWriteSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        summary = _run(
            services.set_summary,
            **self.common(relationship_id),
            text=body.validated_data["text"],
        )
        return Response(SummarySerializer(summary).data)


class MyProgressView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    @extend_schema(
        responses={200: PatientProgressSerializer},
        description="Your session counts, the summary your psychologist wrote for "
        "you, and your mood insights. Never your psychologist's notes.",
    )
    def get(self, request):
        data = selectors.patient_progress(patient_profile=request.user.patient_profile)
        return Response(PatientProgressSerializer(data).data)
