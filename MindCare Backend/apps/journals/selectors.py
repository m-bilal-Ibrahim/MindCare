"""Read-path query logic for journals (mood check-ins, Phase 2 module 3).

"Local day" is the patient's timezone, or Asia/Karachi if none is stored. The
streak is the run of consecutive local days with a check-in that ends today, or
yesterday if today's isn't in yet (it isn't broken until a day is missed).
Insights are calculated here; nothing is AI-generated.
"""

from collections import Counter
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.journals.models import Mood, MoodCheckIn

DEFAULT_TZ = "Asia/Karachi"
INSIGHT_WINDOWS = (7, 30, 90)
TOP_TAGS = 3


def patient_today(patient_profile, *, now=None):
    try:
        tz = ZoneInfo(patient_profile.timezone or DEFAULT_TZ)
    except (ValueError, KeyError):
        tz = ZoneInfo(DEFAULT_TZ)
    return (now or timezone.now()).astimezone(tz).date()


def patients_checked_in(*, patient_days):
    """Which of {patient_id: local_date} already checked in on that day. Reads
    ids and dates only (never the encrypted note); used by the check-in
    reminder."""
    if not patient_days:
        return set()
    rows = MoodCheckIn.objects.filter(
        patient_id__in=patient_days.keys(),
        local_date__in=set(patient_days.values()),
    ).values_list("patient_id", "local_date")
    return {pid for pid, day in rows if patient_days.get(pid) == day}


def check_ins_for(*, patient_profile):
    return MoodCheckIn.objects.filter(patient=patient_profile)


def today_check_in(*, patient_profile, now=None):
    today = patient_today(patient_profile, now=now)
    return today, check_ins_for(patient_profile=patient_profile).filter(
        local_date=today
    ).first()


def streak(dates, today):
    days = set(dates)
    day = today if today in days else today - timedelta(days=1)
    count = 0
    while day in days:
        count += 1
        day -= timedelta(days=1)
    return count


def _window(rows, start):
    picked = [r for r in rows if r["local_date"] >= start]
    moods = [r["mood"] for r in picked]
    tags = Counter(tag for r in picked for tag in r["tags"])
    return {
        "check_ins": len(picked),
        "average_mood": round(sum(moods) / len(moods), 2) if moods else None,
        "distribution": {str(m): moods.count(m) for m in Mood.values},
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))[
                :TOP_TAGS
            ]
        ],
    }


def insights(*, patient_profile, now=None):
    """Averages, mood distribution and top tags for the last 7, 30 and 90 local
    days (today included), plus the current streak."""
    today = patient_today(patient_profile, now=now)
    oldest = today - timedelta(days=max(INSIGHT_WINDOWS) - 1)
    rows = list(
        check_ins_for(patient_profile=patient_profile)
        .filter(local_date__gte=oldest)
        .values("local_date", "mood", "tags")
    )
    all_dates = check_ins_for(patient_profile=patient_profile).values_list(
        "local_date", flat=True
    )
    return {
        "today": today,
        "streak": streak(all_dates, today),
        "windows": {
            str(days): _window(rows, today - timedelta(days=days - 1))
            for days in INSIGHT_WINDOWS
        },
    }


def journal_entries_for(*, patient_profile, date_from=None, date_to=None, tag=None):
    """The patient's own entries, newest first. Only the patient ever calls
    this (there is no psychologist or admin path). Dates filter in the
    database; the tag is encrypted, so it filters the decrypted rows here."""
    from apps.journals.models import JournalEntry

    qs = JournalEntry.objects.filter(patient=patient_profile)
    if date_from:
        qs = qs.filter(local_date__gte=date_from)
    if date_to:
        qs = qs.filter(local_date__lte=date_to)
    if not tag:
        return qs
    return [entry for entry in qs if tag in entry.tag_list]


def journal_entry(*, patient_profile, entry_id):
    """One of the patient's own entries, or None."""
    from apps.journals.models import JournalEntry

    return JournalEntry.objects.filter(pk=entry_id, patient=patient_profile).first()


def mood_history_for_psychologist(*, patient_profile, days, now=None):
    """Mood and tags only (never the note), newest first."""
    today = patient_today(patient_profile, now=now)
    return check_ins_for(patient_profile=patient_profile).filter(
        local_date__gte=today - timedelta(days=days - 1)
    )
