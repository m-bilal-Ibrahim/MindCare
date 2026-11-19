"""DRF views for the care plan. Thin: parse -> service/selector -> serialize.

Psychologist endpoints take the relationship id of a CURRENT patient (404
otherwise, the same as therapy notes). Patient endpoints answer 404 for a plan
that isn't theirs and 403 when they try to log on a read-only plan.
"""

from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.recommendations import selectors, services
from apps.recommendations.api.serializers import (
    CarePlanListSerializer,
    CarePlanSerializer,
    CarePlanVersionSerializer,
    CompletionCreateSerializer,
    CompletionSerializer,
    DaysQuerySerializer,
    GoalCreateSerializer,
    GoalUpdateSerializer,
    GoalWriteResultSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskWriteResultSerializer,
)
from core.exceptions import DomainValidationError
from core.permissions import IsApprovedPsychologist, IsPatient, IsPsychologist

NOT_FOUND = OpenApiResponse(description="Not your current patient, or no such item.")
INVALID = OpenApiResponse(description="Invalid input or a care plan rule.")


class CarePlanWriteThrottle(UserRateThrottle):
    scope = "care_plan"


class CarePlanTrackingThrottle(UserRateThrottle):
    scope = "care_plan_tracking"


def _ip(request):
    return request.META.get("REMOTE_ADDR")


def _run(fn, **kwargs):
    try:
        return fn(**kwargs)
    except (services.NotYourPatient, services.NotFound) as exc:
        raise Http404 from exc
    except services.Forbidden as exc:
        raise PermissionDenied(exc.message) from exc
    except DomainValidationError as exc:
        raise ValidationError(exc.errors, code=exc.code) from exc


class PsychologistView(APIView):
    permission_classes = [IsAuthenticated, IsPsychologist, IsApprovedPsychologist]

    def get_throttles(self):
        if self.request.method in ("POST", "PATCH"):
            return [CarePlanWriteThrottle()]
        return []


class PatientView(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def get_throttles(self):
        if self.request.method in ("POST", "DELETE"):
            return [CarePlanTrackingThrottle()]
        return []


# --- psychologist -------------------------------------------------------------


class PsychologistPlanView(PsychologistView):
    @extend_schema(
        responses={200: CarePlanSerializer, 404: NOT_FOUND},
        description="A current patient's care plan with adherence (`id: null` and "
        "no goals if none yet). Audited.",
    )
    def get(self, request, relationship_id):
        data = _run(
            services.get_plan,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            ip=_ip(request),
        )
        return Response(CarePlanSerializer(data).data)


class GoalsView(PsychologistView):
    @extend_schema(
        request=GoalCreateSerializer,
        responses={201: GoalWriteResultSerializer, 400: INVALID, 404: NOT_FOUND},
        description="Add a goal (creates the plan on the first goal). At most 10 "
        "active goals. The patient gets a content-free notification. Audited.",
    )
    def post(self, request, relationship_id):
        body = GoalCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        goal = _run(
            services.create_goal,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            ip=_ip(request),
            **body.validated_data,
        )
        return Response(
            GoalWriteResultSerializer(goal).data, status=status.HTTP_201_CREATED
        )


class GoalDetailView(PsychologistView):
    @extend_schema(
        request=GoalUpdateSerializer,
        responses={200: GoalWriteResultSerializer, 400: INVALID, 404: NOT_FOUND},
        description="Edit a goal or change its status (active / achieved / "
        "dropped). Goals are never deleted. Versioned and audited.",
    )
    def patch(self, request, relationship_id, goal_id):
        body = GoalUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        goal = _run(
            services.update_goal,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            goal_id=goal_id,
            ip=_ip(request),
            **body.validated_data,
        )
        return Response(GoalWriteResultSerializer(goal).data)


class TasksView(PsychologistView):
    @extend_schema(
        request=TaskCreateSerializer,
        responses={201: TaskWriteResultSerializer, 400: INVALID, 404: NOT_FOUND},
        description="Add a task to an active goal. At most 10 active tasks per "
        "goal and 30 per plan. Versioned and audited.",
    )
    def post(self, request, relationship_id, goal_id):
        body = TaskCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        task = _run(
            services.create_task,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            goal_id=goal_id,
            ip=_ip(request),
            **body.validated_data,
        )
        return Response(
            TaskWriteResultSerializer(task).data, status=status.HTTP_201_CREATED
        )


class TaskDetailView(PsychologistView):
    @extend_schema(
        request=TaskUpdateSerializer,
        responses={200: TaskWriteResultSerializer, 400: INVALID, 404: NOT_FOUND},
        description="Edit a task or archive it (`status: archived`). Tasks are "
        "never deleted; completions are never changed. Versioned and audited.",
    )
    def patch(self, request, relationship_id, task_id):
        body = TaskUpdateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        task = _run(
            services.update_task,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            task_id=task_id,
            ip=_ip(request),
            **body.validated_data,
        )
        return Response(TaskWriteResultSerializer(task).data)


class PsychologistCompletionsView(PsychologistView):
    @extend_schema(
        parameters=[DaysQuerySerializer],
        responses={200: CompletionSerializer(many=True), 404: NOT_FOUND},
        description="The patient's completions for the last `days` (7, 30 or 90; "
        "default 30), notes and difficulty included, newest first. Audited.",
    )
    def get(self, request, relationship_id):
        query = DaysQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        rows = _run(
            services.list_completions,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            days=int(query.validated_data["days"]),
            ip=_ip(request),
        )
        return Response(CompletionSerializer(rows, many=True).data)


class PlanVersionsView(PsychologistView):
    @extend_schema(
        responses={200: CarePlanVersionSerializer(many=True), 404: NOT_FOUND},
        description="Every saved version of the plan, newest first. Audited.",
    )
    def get(self, request, relationship_id):
        versions = _run(
            services.list_versions,
            psychologist_user=request.user,
            relationship_id=relationship_id,
            ip=_ip(request),
        )
        return Response(CarePlanVersionSerializer(versions, many=True).data)


# --- patient --------------------------------------------------------------------


class MyPlansView(PatientView):
    @extend_schema(
        responses={200: CarePlanListSerializer(many=True)},
        description="Your care plans (one per psychologist you have had), most "
        "recently updated first. `can_track` is true only for your current "
        "psychologist's plan.",
    )
    def get(self, request):
        rows = [
            selectors.plan_summary(plan=plan)
            for plan in selectors.patient_plans(
                patient_profile=request.user.patient_profile
            )
        ]
        return Response(CarePlanListSerializer(rows, many=True).data)


class MyPlanDetailView(PatientView):
    @extend_schema(
        responses={200: CarePlanSerializer, 404: NOT_FOUND},
        description="One of your care plans with goals, tasks, what's done today "
        "and adherence.",
    )
    def get(self, request, plan_id):
        plan = _run(
            selectors.patient_plan,
            patient_profile=request.user.patient_profile,
            plan_id=plan_id,
        )
        return Response(CarePlanSerializer(selectors.plan_detail(plan=plan)).data)


class MyCompletionsView(PatientView):
    @extend_schema(
        parameters=[DaysQuerySerializer],
        responses={200: CompletionSerializer(many=True), 404: NOT_FOUND},
        description="Your completions on this plan for the last `days` (7, 30 or "
        "90; default 30), newest first.",
    )
    def get(self, request, plan_id):
        query = DaysQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        plan = _run(
            selectors.patient_plan,
            patient_profile=request.user.patient_profile,
            plan_id=plan_id,
        )
        rows = selectors.completions_for_plan(
            plan=plan, days=int(query.validated_data["days"])
        )
        return Response(CompletionSerializer(rows, many=True).data)


class CompletionCreateView(PatientView):
    @extend_schema(
        request=CompletionCreateSerializer,
        responses={
            201: CompletionSerializer,
            400: INVALID,
            403: OpenApiResponse(description="Read-only: care ended or is paused."),
            404: NOT_FOUND,
        },
        description="Mark a task done for today (default) or yesterday, with an "
        "optional note and difficulty. One per task per day. Audited.",
    )
    def post(self, request, plan_id, task_id):
        body = CompletionCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        completion = _run(
            services.log_completion,
            patient_profile=request.user.patient_profile,
            plan_id=plan_id,
            task_id=task_id,
            ip=_ip(request),
            **body.validated_data,
        )
        return Response(
            CompletionSerializer(completion).data, status=status.HTTP_201_CREATED
        )


class CompletionDetailView(PatientView):
    @extend_schema(
        responses={
            204: None,
            400: OpenApiResponse(description="Not logged today."),
            403: OpenApiResponse(description="Read-only: care ended or is paused."),
            404: NOT_FOUND,
        },
        description="Undo a completion, only on the day you logged it. Audited.",
    )
    def delete(self, request, plan_id, task_id, completion_id):
        _run(
            services.undo_completion,
            patient_profile=request.user.patient_profile,
            plan_id=plan_id,
            task_id=task_id,
            completion_id=completion_id,
            ip=_ip(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
