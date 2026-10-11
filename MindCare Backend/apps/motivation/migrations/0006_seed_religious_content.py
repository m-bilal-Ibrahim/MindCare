"""Seeds 10 Quranic duas and 5 short surahs (6.10), text only.

Read from apps/motivation/data/religious_content.json, which was built from the
alquran.cloud API: Arabic is the Tanzil Quran Text (Simple), CC BY 3.0, copied
verbatim; English is Marmaduke Pickthall's 1930 translation (public domain).
Nothing was typed from memory. Audio is added later by admins. The text must
still be checked by someone knowledgeable before launch (docs/decisions.md,
2026-10-11).
"""

import json
from pathlib import Path

from django.db import migrations

DATA = Path(__file__).resolve().parents[1] / "data" / "religious_content.json"


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def forwards(apps, schema_editor):
    Dua = apps.get_model("motivation", "Dua")
    Surah = apps.get_model("motivation", "Surah")
    data = load()
    for order, item in enumerate(data["duas"], start=1):
        Dua.objects.get_or_create(
            reference=item["reference"],
            defaults={
                "title": item["title"],
                "arabic": item["arabic"],
                "translation": item["translation"],
                "sort_order": order,
            },
        )
    for item in data["surahs"]:
        Surah.objects.get_or_create(
            number=item["number"],
            defaults={
                "name_arabic": item["name_arabic"],
                "name_english": item["name_english"],
                "name_meaning": item["name_meaning"],
                "ayah_count": item["ayah_count"],
                "arabic": item["arabic"],
                "translation": item["translation"],
            },
        )


def backwards(apps, schema_editor):
    data = load()
    apps.get_model("motivation", "Dua").objects.filter(
        reference__in=[d["reference"] for d in data["duas"]]
    ).delete()
    apps.get_model("motivation", "Surah").objects.filter(
        number__in=[s["number"] for s in data["surahs"]]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("motivation", "0005_religious_content")]

    operations = [migrations.RunPython(forwards, backwards)]
