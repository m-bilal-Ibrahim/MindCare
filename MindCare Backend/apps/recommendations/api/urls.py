"""URL routes for the recommendations API, included under /api/v1/recommendations/.

The care plan (docs/decisions.md, 2026-11-19). Phase 6's AI recommendations
will feed into the same plan only after psychologist approval.
"""

from django.urls import path

from apps.recommendations.api import views

app_name = "recommendations"

PLAN = "psychologist/patients/<int:relationship_id>/care-plan/"
MINE = "care-plans/<int:plan_id>/"

urlpatterns = [
    # Psychologists: a CURRENT patient's plan, by relationship id
    path(PLAN, views.PsychologistPlanView.as_view(), name="care-plan"),
    path(PLAN + "goals/", views.GoalsView.as_view(), name="care-plan-goals"),
    path(
        PLAN + "goals/<int:goal_id>/",
        views.GoalDetailView.as_view(),
        name="care-plan-goal",
    ),
    path(
        PLAN + "goals/<int:goal_id>/tasks/",
        views.TasksView.as_view(),
        name="care-plan-tasks",
    ),
    path(
        PLAN + "tasks/<int:task_id>/",
        views.TaskDetailView.as_view(),
        name="care-plan-task",
    ),
    path(
        PLAN + "completions/",
        views.PsychologistCompletionsView.as_view(),
        name="care-plan-completions",
    ),
    path(
        PLAN + "versions/",
        views.PlanVersionsView.as_view(),
        name="care-plan-versions",
    ),
    # Patients: their own plans
    path("care-plans/", views.MyPlansView.as_view(), name="my-care-plans"),
    path(MINE, views.MyPlanDetailView.as_view(), name="my-care-plan"),
    path(
        MINE + "completions/",
        views.MyCompletionsView.as_view(),
        name="my-care-plan-completions",
    ),
    path(
        MINE + "tasks/<int:task_id>/completions/",
        views.CompletionCreateView.as_view(),
        name="my-task-completions",
    ),
    path(
        MINE + "tasks/<int:task_id>/completions/<int:completion_id>/",
        views.CompletionDetailView.as_view(),
        name="my-task-completion",
    ),
]
