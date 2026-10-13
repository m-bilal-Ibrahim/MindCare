"""Demo accounts for presentations: 6 approved psychologists and 2 patients.

Every account is clearly fake: emails are demo.*@example.com, license numbers
start with DEMO-, and every psychologist bio starts "Demo account, not a real
psychologist." Names are plain because the person-name rule allows no brackets
(docs/validation-rules.md); re-running the seed renames accounts created with the
old "(Demo)" suffix. Accounts are created through the real services
(register_user, update_patient_profile, set_accepting_status), so they look
exactly like accounts made through the API. The password is passed in by the
caller (the seed_demo command reads it from DEMO_PASSWORD); none is stored here.

It also sets up one psychologist's caseload for the demo: demo patient 1 has an
accepted relationship with Dr. Sara Ahmed, demo patient 2 a pending request to her
(so her inbox and patient list both have something to show).

remove_demo_accounts() deletes only the emails listed below. CareRelationship
rows reference profiles with on_delete=PROTECT, so they are deleted first.
"""

from datetime import date

from django.db import transaction
from django.db.models import Q

from apps.accounts.models import ApprovalStatus, Role, User
from apps.accounts.services import register_user
from apps.patients.services import update_patient_profile
from apps.psychologists.services import update_psychologist_profile
from apps.relationships.models import CareRelationship, RelationshipStatus
from apps.relationships.selectors import patient_current
from apps.relationships.services import (
    accept_request,
    request_psychologist,
    set_accepting_status,
)

DEMO_PSYCHOLOGISTS = [
    {
        "email": "demo.psych.sara@example.com",
        "full_name": "Dr. Sara Ahmed",
        "accepting": True,
        "profile": {
            "license_number": "DEMO-0001",
            "license_issuing_country": "PK",
            "specializations": ["anxiety", "stress-management"],
            "languages": ["en", "ur"],
            "country": "PK",
            "city": "Lahore",
            "timezone": "Asia/Karachi",
            "gender": "female",
            "years_of_experience": 8,
            "bio": "Demo account, not a real psychologist. CBT for anxiety and work stress.",
        },
    },
    {
        "email": "demo.psych.bilal@example.com",
        "full_name": "Dr. Bilal Hussain",
        "accepting": True,
        "profile": {
            "license_number": "DEMO-0002",
            "license_issuing_country": "PK",
            "specializations": ["depression", "grief"],
            "languages": ["ur", "pa"],
            "country": "PK",
            "city": "Karachi",
            "timezone": "Asia/Karachi",
            "gender": "male",
            "years_of_experience": 12,
            "bio": "Demo account, not a real psychologist. Depression and bereavement support.",
        },
    },
    {
        "email": "demo.psych.ayesha@example.com",
        "full_name": "Dr. Ayesha Malik",
        "accepting": False,
        "not_accepting_reason": "fully_booked",
        "profile": {
            "license_number": "DEMO-0003",
            "license_issuing_country": "PK",
            "specializations": ["trauma-ptsd", "anxiety"],
            "languages": ["en", "ur"],
            "country": "PK",
            "city": "Islamabad",
            "timezone": "Asia/Karachi",
            "gender": "female",
            "years_of_experience": 15,
            "bio": "Demo account, not a real psychologist. Trauma-focused therapy.",
        },
    },
    {
        "email": "demo.psych.imran@example.com",
        "full_name": "Dr. Imran Khan",
        "accepting": True,
        "profile": {
            "license_number": "DEMO-0004",
            "license_issuing_country": "PK",
            "specializations": ["addiction-substance-use", "anger-management"],
            "languages": ["ps", "ur", "en"],
            "country": "PK",
            "city": "Peshawar",
            "timezone": "Asia/Karachi",
            "gender": "male",
            "years_of_experience": 6,
            "bio": "Demo account, not a real psychologist. Addiction recovery and anger management.",
        },
    },
    {
        "email": "demo.psych.emily@example.com",
        "full_name": "Dr. Emily Carter",
        "accepting": False,
        "not_accepting_reason": "away",
        "profile": {
            "license_number": "DEMO-0005",
            "license_issuing_country": "GB",
            "specializations": ["couples-relationship", "family-therapy"],
            "languages": ["en"],
            "country": "GB",
            "city": "London",
            "timezone": "Europe/London",
            "gender": "female",
            "years_of_experience": 10,
            "bio": "Demo account, not a real psychologist. Couples and family therapy, online sessions.",
        },
    },
    {
        "email": "demo.psych.omar@example.com",
        "full_name": "Dr. Omar Farooq",
        "accepting": True,
        "profile": {
            "license_number": "DEMO-0006",
            "license_issuing_country": "AE",
            "specializations": ["ocd", "sleep-issues"],
            "languages": ["ar", "en", "ur"],
            "country": "AE",
            "city": "Dubai",
            "timezone": "Asia/Dubai",
            "gender": None,
            "years_of_experience": 4,
            "bio": "Demo account, not a real psychologist. OCD and insomnia.",
        },
    },
]

DEMO_PATIENTS = [
    {
        "email": "demo.patient.hina@example.com",
        "full_name": "Hina Raza",
        "timezone": "Asia/Karachi",
        "date_of_birth": date(1998, 4, 12),
        "gender": "female",
    },
    {
        "email": "demo.patient.daniyal@example.com",
        "full_name": "Daniyal Shah",
        "timezone": "Europe/London",
        "date_of_birth": date(1991, 9, 3),
        "gender": "male",
    },
]

# 6.3: one pending application, with fictional documents, for the admin review
# screen. Created through the real registration service; left pending.
DEMO_APPLICANT = {
    "email": "demo.applicant.nadia@example.com",
    "full_name": "Dr. Nadia Siddiqui",
    "profile": {
        "license_number": "DEMO-0007",
        "license_issuing_country": "PK",
        "specializations": ["anxiety", "sleep-issues"],
        "languages": ["en", "ur"],
        "country": "PK",
        "city": "Islamabad",
        "timezone": "Asia/Karachi",
        "gender": "female",
        "years_of_experience": 3,
        "bio": "Demo account, not a real psychologist. Applicant waiting for review.",
    },
}
# 6.3: one open report for the admin moderation screen (fictional).
DEMO_REPORT_DESCRIPTION = (
    "Demo report (fictional): messages were sent outside the agreed hours."
)

DEMO_PSYCHOLOGIST_EMAILS = [p["email"] for p in DEMO_PSYCHOLOGISTS]
DEMO_PATIENT_EMAILS = [p["email"] for p in DEMO_PATIENTS]
DEMO_EMAILS = DEMO_PSYCHOLOGIST_EMAILS + DEMO_PATIENT_EMAILS + [DEMO_APPLICANT["email"]]
# A minimal valid PDF, clearly marked fictional in its content.
DEMO_PDF = (
    b"%PDF-1.4\n% MindCare demo document - fictional, not a real credential\n"
    b"1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
)
DEMO_INBOX_PSYCHOLOGIST = "demo.psych.sara@example.com"


def _psychologist_profile_data(spec):
    from apps.reference.models import Country, Language, Specialization

    p = spec["profile"]
    country = Country.objects.get(code=p["country"])
    return {
        "license_number": p["license_number"],
        "license_issuing_country": Country.objects.get(
            code=p["license_issuing_country"]
        ),
        "license_issuing_authority": "Demo Licensing Authority (fictional)",
        "qualifications": "Demo qualification (fictional)",
        "specializations": list(
            Specialization.objects.filter(slug__in=p["specializations"])
        ),
        "years_of_experience": p["years_of_experience"],
        "languages": list(Language.objects.filter(code__in=p["languages"])),
        "country": country,
        "city": p["city"],
        "timezone": p["timezone"],
        "gender": p["gender"],
        "bio": p["bio"],
    }


def _sync_name(user, full_name):
    """Accounts seeded before the name rule were called "… (Demo)"."""
    if user.full_name != full_name:
        user.full_name = full_name
        user.save(update_fields=["full_name"])


@transaction.atomic
def seed_demo_accounts(*, password):
    """Create any missing demo account; existing ones are left as they are,
    apart from re-applying the name, bio, approval, the accepting switch and
    date of birth."""
    created = existing = 0

    for spec in DEMO_PSYCHOLOGISTS:
        user = User.objects.filter(email=spec["email"]).first()
        if user is None:
            user = register_user(
                email=spec["email"],
                password=password,
                full_name=spec["full_name"],
                role=Role.PSYCHOLOGIST,
                is_adult_confirmed=True,
                profile_data=_psychologist_profile_data(spec),
            )
            created += 1
        else:
            existing += 1
            _sync_name(user, spec["full_name"])
            if user.psychologist_profile.bio != spec["profile"]["bio"]:
                update_psychologist_profile(
                    profile=user.psychologist_profile, bio=spec["profile"]["bio"]
                )
        # No approval service exists until Phase 2.5; this is what Django admin does.
        if user.approval_status != ApprovalStatus.APPROVED:
            user.approval_status = ApprovalStatus.APPROVED
            user.save(update_fields=["approval_status"])
        set_accepting_status(
            psychologist_user=user,
            accepting=spec["accepting"],
            reason=spec.get("not_accepting_reason"),
        )

    for spec in DEMO_PATIENTS:
        user = User.objects.filter(email=spec["email"]).first()
        if user is None:
            user = register_user(
                email=spec["email"],
                password=password,
                full_name=spec["full_name"],
                role=Role.PATIENT,
                is_adult_confirmed=True,
                profile_data={"timezone": spec["timezone"]},
            )
            created += 1
        else:
            existing += 1
            _sync_name(user, spec["full_name"])
        update_patient_profile(
            profile=user.patient_profile,
            date_of_birth=spec["date_of_birth"],
            gender=spec["gender"],
        )

    _ensure_demo_relationships()
    _ensure_demo_photos_and_history()
    applicant = User.objects.filter(email=DEMO_APPLICANT["email"]).first()
    if applicant is not None:
        existing += 1
        _sync_name(applicant, DEMO_APPLICANT["full_name"])
    else:
        register_user(
            email=DEMO_APPLICANT["email"],
            password=password,
            full_name=DEMO_APPLICANT["full_name"],
            role=Role.PSYCHOLOGIST,
            is_adult_confirmed=True,
            profile_data=_psychologist_profile_data(DEMO_APPLICANT),
            credential_documents=_demo_documents(),
        )
        created += 1
    _ensure_demo_report()
    return {"created": created, "existing": existing}


# 6.1 demo data: initials avatars (generated, clearly not real photos) and a
# fictional mental health history for demo patient 1.
DEMO_HISTORY = {
    "concerns": ["anxiety", "sleep-issues"],
    "previous_diagnosis": "no",
    "current_medication": "no",
    "previous_therapy": "yes",
    "notes": "Demo history (fictional): trouble sleeping before exams.",
}
AVATAR_COLOURS = ["#2F6F73", "#7A5C99", "#B5654A", "#3D6FA8", "#5F8A3E", "#A8486E"]


def _initials_avatar(full_name, colour):
    """A 256 px square with the person's initials: obviously an avatar, never a
    real face."""
    import io

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image, ImageDraw

    from core.files import check_photo

    words = [w for w in full_name.replace("Dr.", "").split() if w]
    initials = "".join(w[0] for w in words[:2]).upper()
    image = Image.new("RGB", (256, 256), colour)
    draw = ImageDraw.Draw(image)
    draw.text((128, 128), initials, fill="white", anchor="mm", font_size=110)
    out = io.BytesIO()
    image.save(out, format="PNG")
    return check_photo(SimpleUploadedFile("avatar.png", out.getvalue()))


def _ensure_demo_photos_and_history():
    from apps.patients.models import MentalHealthHistory
    from apps.patients.services import save_mental_health_history, set_patient_photo
    from apps.psychologists.services import set_psychologist_photo
    from apps.reference.models import Specialization

    for index, spec in enumerate(DEMO_PSYCHOLOGISTS):
        profile = User.objects.get(email=spec["email"]).psychologist_profile
        if not profile.photo_key:
            set_psychologist_photo(
                profile=profile,
                checked=_initials_avatar(
                    spec["full_name"], AVATAR_COLOURS[index % len(AVATAR_COLOURS)]
                ),
            )
    hina = User.objects.get(email=DEMO_PATIENT_EMAILS[0])
    if not hina.patient_profile.photo_key:
        set_patient_photo(
            profile=hina.patient_profile,
            checked=_initials_avatar(hina.full_name, "#4A7C59"),
        )
    # 6.10: the fictional patient 1 has opted in, so the demo shows duas/surahs.
    from apps.motivation.services import set_religious_opt_in

    set_religious_opt_in(user=hina, opted_in=True)
    if not MentalHealthHistory.objects.filter(profile=hina.patient_profile).exists():
        save_mental_health_history(
            profile=hina.patient_profile,
            actor=hina,
            concerns=Specialization.objects.filter(slug__in=DEMO_HISTORY["concerns"]),
            previous_diagnosis=DEMO_HISTORY["previous_diagnosis"],
            current_medication=DEMO_HISTORY["current_medication"],
            previous_therapy=DEMO_HISTORY["previous_therapy"],
            notes=DEMO_HISTORY["notes"],
        )


def _demo_documents():
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.psychologists.models import DocumentKind
    from core.files import PDF, check_upload

    def checked(name):
        return check_upload(
            SimpleUploadedFile(name, DEMO_PDF),
            label="Demo document",
            allowed=(PDF,),
            max_mb=1,
        )

    return {
        DocumentKind.LICENSE: [checked("license.pdf")],
        DocumentKind.DEGREE: [checked("degree.pdf")],
    }


def _ensure_demo_report():
    """The inbox psychologist reports their accepted demo patient (fictional),
    unless an open report already exists."""
    from apps.moderation.models import Report, ReportReason, ReportStatus
    from apps.moderation.services import submit_report

    psych_user = User.objects.get(email=DEMO_INBOX_PSYCHOLOGIST)
    patient = User.objects.get(email=DEMO_PATIENT_EMAILS[0])
    rel = (
        CareRelationship.objects.filter(
            psychologist__user=psych_user,
            patient__user=patient,
            status=RelationshipStatus.ACCEPTED,
        )
        .order_by("-id")
        .first()
    )
    if (
        rel is None
        or Report.objects.filter(
            reporter=psych_user, relationship=rel, status=ReportStatus.OPEN
        ).exists()
    ):
        return
    submit_report(
        reporter=psych_user,
        reason=ReportReason.INAPPROPRIATE_CONTENT,
        description=DEMO_REPORT_DESCRIPTION,
        relationship_id=rel.pk,
    )


def _ensure_demo_relationships():
    """Patient 1 accepted with the inbox psychologist, patient 2 pending to her.
    A patient who already has an open row (e.g. changed during a demo) is left
    alone; an expired pending request is replaced by request_psychologist()."""
    psych_user = User.objects.get(email=DEMO_INBOX_PSYCHOLOGIST)
    psych_id = psych_user.psychologist_profile.pk
    accepted_email, pending_email = DEMO_PATIENT_EMAILS

    patient = User.objects.get(email=accepted_email)
    current = patient_current(patient_user=patient)
    if current is None:
        current = request_psychologist(patient_user=patient, psychologist_id=psych_id)
    if (
        current.status == RelationshipStatus.PENDING
        and current.psychologist_id == psych_id
    ):
        accept_request(psychologist_user=psych_user, relationship_id=current.pk)

    patient = User.objects.get(email=pending_email)
    if patient_current(patient_user=patient) is None:
        request_psychologist(patient_user=patient, psychologist_id=psych_id)


@transaction.atomic
def remove_demo_accounts():
    """Delete the demo accounts only: reports and relationship rows first
    (PROTECT), document files from storage, then the users (profiles cascade).
    Audit rows stay: they are append-only and hold only ids."""
    from apps.moderation.models import Report
    from apps.psychologists.models import CredentialDocument
    from integrations.storage_client.client import delete_file

    users = User.objects.filter(email__in=DEMO_EMAILS)
    Report.objects.filter(Q(reporter__in=users) | Q(reported_user__in=users)).delete()
    from apps.patients.models import PatientProfile
    from apps.psychologists.models import PsychologistProfile

    keys = list(
        CredentialDocument.objects.filter(profile__user__in=users).values_list(
            "storage_key", flat=True
        )
    )
    keys += [
        key
        for model in (PatientProfile, PsychologistProfile)
        for key in model.objects.filter(user__in=users).values_list(
            "photo_key", flat=True
        )
        if key
    ]
    transaction.on_commit(lambda: [delete_file(key) for key in keys])
    rels = CareRelationship.objects.filter(
        Q(patient__user__in=users) | Q(psychologist__user__in=users)
    )
    relationships = rels.count()
    rels.delete()
    count = users.count()
    users.delete()
    return {"users": count, "relationships": relationships}
