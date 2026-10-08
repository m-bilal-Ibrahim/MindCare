"""Seed ~30 short, non-religious motivational quotes. Mostly classical or
public-domain authors, plus proverbs; admins edit or hide them in Django admin.
Reversing deletes only these exact rows."""

from django.db import migrations

QUOTES = [
    # hope
    ("A journey of a thousand miles begins with a single step.", "Lao Tzu", "hope"),
    (
        "Hope is the thing with feathers that perches in the soul.",
        "Emily Dickinson",
        "hope",
    ),
    (
        "Optimism is the faith that leads to achievement. Nothing can be done without hope and confidence.",
        "Helen Keller",
        "hope",
    ),
    ("This too shall pass.", "Persian proverb", "hope"),
    ("Act as if what you do makes a difference. It does.", "William James", "hope"),
    (
        "Begin at once to live, and count each separate day as a separate life.",
        "Seneca",
        "hope",
    ),
    ("Even the darkest night will end and the sun will rise.", "Victor Hugo", "hope"),
    (
        "With the new day comes new strength and new thoughts.",
        "Eleanor Roosevelt",
        "hope",
    ),
    # resilience
    ("The best way out is always through.", "Robert Frost", "resilience"),
    (
        "Although the world is full of suffering, it is also full of the overcoming of it.",
        "Helen Keller",
        "resilience",
    ),
    ("Fall seven times, stand up eight.", "Japanese proverb", "resilience"),
    (
        "Difficulties strengthen the mind, as labour does the body.",
        "Seneca",
        "resilience",
    ),
    (
        "He who has a why to live can bear almost any how.",
        "Friedrich Nietzsche",
        "resilience",
    ),
    (
        "It is not because things are difficult that we do not dare; it is because we do not dare that they are difficult.",
        "Seneca",
        "resilience",
    ),
    (
        "Do what you can, with what you have, where you are.",
        "Theodore Roosevelt",
        "resilience",
    ),
    (
        "Life is like riding a bicycle. To keep your balance, you must keep moving.",
        "Albert Einstein",
        "resilience",
    ),
    ("Smooth seas do not make skillful sailors.", "African proverb", "resilience"),
    (
        "You gain strength, courage and confidence by every experience in which you really stop to look fear in the face.",
        "Eleanor Roosevelt",
        "resilience",
    ),
    # calm
    ("We suffer more often in imagination than in reality.", "Seneca", "calm"),
    ("Very little is needed to make a happy life.", "Marcus Aurelius", "calm"),
    (
        "Adopt the pace of nature: her secret is patience.",
        "Ralph Waldo Emerson",
        "calm",
    ),
    (
        "The greatest weapon against stress is our ability to choose one thought over another.",
        "William James",
        "calm",
    ),
    ("Keep calm and carry on.", "British wartime poster, 1939", "calm"),
    ("One day at a time.", "Proverb", "calm"),
    (
        "Tension is who you think you should be. Relaxation is who you are.",
        "Chinese proverb",
        "calm",
    ),
    # self_care
    ("Rest is not idleness.", "John Lubbock", "self_care"),
    ("Take rest; a field that has rested gives a bountiful crop.", "Ovid", "self_care"),
    (
        "Caring for myself is not self-indulgence, it is self-preservation.",
        "Audre Lorde",
        "self_care",
    ),
    (
        "Early to bed and early to rise makes a man healthy, wealthy, and wise.",
        "Benjamin Franklin",
        "self_care",
    ),
    (
        "The time to relax is when you don't have time for it.",
        "Sydney J. Harris",
        "self_care",
    ),
]


def seed(apps, schema_editor):
    Quote = apps.get_model("motivation", "Quote")
    Quote.objects.bulk_create(
        Quote(text=text, author=author, category=category)
        for text, author, category in QUOTES
    )


def unseed(apps, schema_editor):
    Quote = apps.get_model("motivation", "Quote")
    Quote.objects.filter(text__in=[text for text, _, _ in QUOTES]).delete()


class Migration(migrations.Migration):
    dependencies = [("motivation", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
