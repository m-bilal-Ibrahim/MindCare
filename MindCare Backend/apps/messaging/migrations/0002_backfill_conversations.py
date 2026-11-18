"""Create the conversation for every pair already in accepted care, since new
ones are created when a request is accepted."""

from django.db import migrations


def backfill(apps, schema_editor):
    CareRelationship = apps.get_model("relationships", "CareRelationship")
    Conversation = apps.get_model("messaging", "Conversation")
    pairs = CareRelationship.objects.filter(status="accepted").values_list(
        "patient_id", "psychologist_id"
    )
    for patient_id, psychologist_id in pairs:
        Conversation.objects.get_or_create(
            patient_id=patient_id, psychologist_id=psychologist_id
        )


class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0001_initial"),
        ("relationships", "0001_initial"),
    ]

    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
