"""Database models for the appointments app (Phase 2 module 4: booking and fees).

docs/decisions.md, 2026-10-28 (Q27-Q34):
- Each psychologist sets a per-session fee in PKR, a session length (30, 50 or
  60 minutes; a 10-minute gap always follows) and a personal Zoom / Meet link.
- Weekly working windows are wall-clock times in the psychologist's timezone,
  plus single days off.
- A patient with an accepted relationship picks a free slot; that creates a
  request the psychologist confirms or answers with another time. An
  unconfirmed request expires when its slot starts (evaluated on read).
- No double booking: a Postgres exclusion constraint (btree_gist) refuses two
  blocking sessions of one psychologist whose [start, end + gap) ranges overlap.
"""

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Func, Q
from django.utils import timezone

from core.fields import HttpsUrlField
from core.models import ValidatedModelMixin
from core.validators import whole_number_message

GAP_MINUTES = 10
MIN_FEE_PKR, MAX_FEE_PKR = 100, 100_000
FEE_MESSAGE = whole_number_message("Session fee", MIN_FEE_PKR, MAX_FEE_PKR)
VIDEO_DOMAINS = ["zoom.us", "meet.google.com"]


class SessionLength(models.IntegerChoices):
    MIN_30 = 30, "30 minutes"
    MIN_50 = 50, "50 minutes"
    MIN_60 = 60, "60 minutes"


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class BookingSettings(ValidatedModelMixin, models.Model):
    """A psychologist's fee, session length and video link. Bookable once the
    fee and link are set and at least one working window exists."""

    psychologist = models.OneToOneField(
        "psychologists.PsychologistProfile",
        on_delete=models.CASCADE,
        related_name="booking_settings",
    )
    session_minutes = models.PositiveSmallIntegerField(
        choices=SessionLength.choices, default=SessionLength.MIN_50
    )
    fee_pkr = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(MIN_FEE_PKR, message=FEE_MESSAGE),
            MaxValueValidator(MAX_FEE_PKR, message=FEE_MESSAGE),
        ],
    )
    # Shown to the patient only on confirmed sessions.
    video_link = HttpsUrlField(
        label="Video link", allowed_domains=VIDEO_DOMAINS, blank=True, default=""
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking settings #{self.pk}"


class WorkingWindow(ValidatedModelMixin, models.Model):
    """One weekly window, wall-clock time in the psychologist's timezone."""

    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.CASCADE,
        related_name="working_windows",
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F("end_time")),
                name="appointments_window_start_before_end",
            )
        ]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time}-{self.end_time}"


class DayOff(models.Model):
    """A whole local day (psychologist's timezone) with no slots."""

    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.CASCADE,
        related_name="days_off",
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["psychologist", "date"], name="appointments_one_day_off"
            )
        ]

    def __str__(self):
        return f"Day off {self.date}"


class SessionStatus(models.TextChoices):
    REQUESTED = "requested", "Requested by the patient"
    PROPOSED = "proposed", "Another time proposed by the psychologist"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired (not confirmed in time)"
    COMPLETED = "completed", "Completed"
    NO_SHOW = "no_show", "Patient didn't attend"


# These hold their slot: the exclusion constraint applies to them only.
BLOCKING_STATUSES = (
    SessionStatus.REQUESTED,
    SessionStatus.PROPOSED,
    SessionStatus.CONFIRMED,
)
AWAITING_STATUSES = (SessionStatus.REQUESTED, SessionStatus.PROPOSED)


class CancelledBy(models.TextChoices):
    PATIENT = "patient", "Patient"
    PSYCHOLOGIST = "psychologist", "Psychologist"
    SYSTEM = "system", "System (care ended)"


class TsTzRange(Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class Session(models.Model):
    # PROTECT: sessions are the basis of 6.11's fees and invoices.
    relationship = models.ForeignKey(
        "relationships.CareRelationship",
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    patient = models.ForeignKey(
        "patients.PatientProfile", on_delete=models.PROTECT, related_name="sessions"
    )
    psychologist = models.ForeignKey(
        "psychologists.PsychologistProfile",
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    status = models.CharField(
        max_length=20, choices=SessionStatus.choices, default=SessionStatus.REQUESTED
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    # ends_at + the 10-minute gap: the range the exclusion constraint protects.
    blocked_until = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(choices=SessionLength.choices)
    # The fee when the patient booked; later fee changes don't touch it.
    fee_pkr = models.PositiveIntegerField()
    # The time the patient first picked (differs from starts_at after a proposal).
    requested_starts_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.CharField(
        max_length=20, choices=CancelledBy.choices, null=True, blank=True
    )
    # A patient's cancellation of a confirmed session less than 24 h before it
    # starts. Recorded for 6.11 (fees); nothing is charged yet.
    is_late_cancellation = models.BooleanField(default=False)
    outcome_marked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at", "id"]
        constraints = [
            ExclusionConstraint(
                name="appointments_no_double_booking",
                expressions=[
                    (TsTzRange("starts_at", "blocked_until"), RangeOperators.OVERLAPS),
                    ("psychologist", RangeOperators.EQUAL),
                ],
                condition=Q(status__in=BLOCKING_STATUSES),
            ),
            models.CheckConstraint(
                condition=Q(starts_at__lt=models.F("ends_at"))
                & Q(ends_at__lte=models.F("blocked_until")),
                name="appointments_session_times_in_order",
            ),
        ]
        indexes = [
            models.Index(
                fields=["psychologist", "starts_at"], name="appointments_psych_start"
            ),
            models.Index(
                fields=["patient", "starts_at"], name="appointments_pat_start"
            ),
        ]

    def __str__(self):
        return f"Session #{self.pk} ({self.status})"

    @property
    def effective_status(self):
        """A request or proposal whose start has passed reads as expired.
        Read-only; services persist it on the next write that touches the row."""
        if self.status in AWAITING_STATUSES and self.starts_at <= timezone.now():
            return SessionStatus.EXPIRED
        return self.status
