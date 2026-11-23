"""Seed 14 PLACEHOLDER wellness items (2 per category), all HIDDEN.

General wellbeing practices written by the MindCare team: no numbers, no claims
that anything treats or cures a condition, and a safety note on every physical
item. They must be reviewed by a clinical advisor before launch
(docs/decisions.md, 2026-11-23); an admin publishes each one after review.
No media is seeded: admins upload images and audio they hold the rights to.
"""

from django.db import migrations

SOURCE = "MindCare team (placeholder)"
MOVE_SAFELY = (
    "Move gently and stop if you feel pain, dizziness or shortness of breath. "
    "Check with your doctor first if you have an injury or a health condition."
)
BREATHE_SAFELY = (
    "Breathe gently and never strain. If you feel light-headed, stop and breathe "
    "normally."
)

ITEMS = [
    # --- nutrition ---------------------------------------------------------
    {
        "kind": "article",
        "category": "nutrition",
        "title": "Regular meals through the day",
        "summary": "Why eating at fairly regular times can help your day feel "
        "steadier, and simple ways to make it easier.",
        "body": (
            "Long gaps without food can leave some people feeling tired, "
            "irritable or unfocused. Eating at roughly regular times gives your "
            "day a rhythm.\n\n"
            "Ideas that may help:\n"
            "- Plan a simple breakfast you can make quickly.\n"
            "- Keep an easy snack, such as fruit or nuts, with you.\n"
            "- If you often forget lunch, set a gentle reminder.\n\n"
            "Everyone's needs are different. If you have a medical condition or "
            "follow a special diet, follow the advice of your doctor or dietitian."
        ),
        "duration_minutes": 3,
        "difficulty": "gentle",
        "sort_order": 10,
    },
    {
        "kind": "article",
        "category": "nutrition",
        "title": "Drinking water through the day",
        "summary": "A short guide to building a habit of drinking water " "regularly.",
        "body": (
            "Many people forget to drink water when they are busy or stressed. "
            "Small habits make it easier to remember.\n\n"
            "Ideas that may help:\n"
            "- Keep a bottle or glass of water where you can see it.\n"
            "- Have a glass of water with each meal.\n"
            "- Drink a little more on hot days or after being active.\n\n"
            "If a doctor has told you to limit fluids, follow their advice."
        ),
        "duration_minutes": 2,
        "difficulty": "gentle",
        "sort_order": 20,
    },
    # --- exercise ----------------------------------------------------------
    {
        "kind": "routine",
        "category": "exercise",
        "title": "A gentle walk",
        "summary": "An easy walk at your own pace, indoors or outside.",
        "steps": [
            "Put on comfortable shoes and choose a safe route.",
            "Start slowly for the first few minutes to warm up.",
            "Walk at a pace where you can still talk comfortably.",
            "Notice your surroundings: sounds, colours and the air.",
            "Slow down for the last few minutes before you stop.",
        ],
        "duration_minutes": 15,
        "difficulty": "gentle",
        "safety_note": MOVE_SAFELY,
        "sort_order": 10,
    },
    {
        "kind": "routine",
        "category": "exercise",
        "title": "Simple seated stretches",
        "summary": "Gentle stretches you can do in a chair during a break.",
        "steps": [
            "Sit upright with both feet flat on the floor.",
            "Slowly roll your shoulders backwards a few times, then forwards.",
            "Gently tilt your head towards one shoulder, then the other.",
            "Stretch both arms above your head and reach up softly.",
            "Twist gently to one side holding the chair, then to the other.",
            "Finish with a few slow, easy breaths.",
        ],
        "duration_minutes": 5,
        "difficulty": "gentle",
        "safety_note": MOVE_SAFELY,
        "sort_order": 20,
    },
    # --- yoga --------------------------------------------------------------
    {
        "kind": "routine",
        "category": "yoga",
        "title": "Gentle morning yoga sequence",
        "summary": "A slow, beginner-friendly sequence to start the day.",
        "steps": [
            "Stand tall with your feet hip-width apart and breathe slowly.",
            "Raise your arms overhead as you breathe in, lower them as you "
            "breathe out.",
            "Come onto your hands and knees and move gently between arching and "
            "rounding your back.",
            "Sit back towards your heels and rest your forehead down in child's "
            "pose.",
            "Return to standing slowly and take a few calm breaths.",
        ],
        "duration_minutes": 10,
        "difficulty": "gentle",
        "safety_note": MOVE_SAFELY,
        "sort_order": 10,
    },
    {
        "kind": "routine",
        "category": "yoga",
        "title": "Restful evening stretch",
        "summary": "A quiet floor sequence for the end of the day.",
        "steps": [
            "Sit on a mat or soft surface with your legs stretched out.",
            "Reach gently towards your feet without forcing the stretch.",
            "Lie on your back and hug your knees towards your chest.",
            "Let your knees fall gently to one side, then to the other.",
            "Rest on your back with your arms by your sides and breathe slowly.",
        ],
        "duration_minutes": 10,
        "difficulty": "gentle",
        "safety_note": MOVE_SAFELY,
        "sort_order": 20,
    },
    # --- stress reduction --------------------------------------------------
    {
        "kind": "practice",
        "category": "stress_reduction",
        "title": "Box breathing",
        "summary": "Breathe in, hold, breathe out and hold again, each for a "
        "slow count.",
        "steps": [
            "Sit comfortably and let your shoulders relax.",
            "Breathe in slowly through your nose for a count of four.",
            "Hold your breath gently for a count of four.",
            "Breathe out slowly for a count of four.",
            "Hold again for a count of four, then repeat.",
        ],
        "duration_minutes": 3,
        "difficulty": "gentle",
        "safety_note": BREATHE_SAFELY,
        "breath_in_seconds": 4,
        "breath_hold_seconds": 4,
        "breath_out_seconds": 4,
        "breath_hold_after_out_seconds": 4,
        "sort_order": 10,
    },
    {
        "kind": "practice",
        "category": "stress_reduction",
        "title": "5-4-3-2-1 grounding",
        "summary": "Bring your attention to the present by noticing what is "
        "around you.",
        "steps": [
            "Name five things you can see around you.",
            "Name four things you can feel, such as your feet on the floor.",
            "Name three things you can hear.",
            "Name two things you can smell, or two smells you like.",
            "Name one thing you can taste, or take a slow sip of water.",
        ],
        "duration_minutes": 5,
        "difficulty": "gentle",
        "sort_order": 20,
    },
    # --- mindfulness -------------------------------------------------------
    {
        "kind": "practice",
        "category": "mindfulness",
        "title": "A short body scan",
        "summary": "Move your attention slowly through your body, noticing "
        "without judging.",
        "steps": [
            "Sit or lie down somewhere comfortable and close your eyes if you " "like.",
            "Notice your breathing without trying to change it.",
            "Bring your attention to your feet, then slowly up through your legs.",
            "Continue through your back, stomach, chest, arms and shoulders.",
            "Finish with your face and head, then take a slow breath and open "
            "your eyes.",
        ],
        "duration_minutes": 10,
        "difficulty": "gentle",
        "sort_order": 10,
    },
    {
        "kind": "practice",
        "category": "mindfulness",
        "title": "A mindful tea or coffee break",
        "summary": "Use an everyday drink as a short moment of focus.",
        "steps": [
            "Make your drink slowly, noticing each step.",
            "Hold the cup and notice its warmth and weight.",
            "Notice the smell before you take a sip.",
            "Take small sips and notice the taste.",
            "When your mind wanders, gently bring it back to the drink.",
        ],
        "duration_minutes": 5,
        "difficulty": "gentle",
        "sort_order": 20,
    },
    # --- relaxation --------------------------------------------------------
    {
        "kind": "practice",
        "category": "relaxation",
        "title": "Progressive muscle relaxation",
        "summary": "Gently tense and then release muscle groups, one at a time.",
        "steps": [
            "Sit or lie down somewhere comfortable.",
            "Gently tense the muscles in your feet for a few seconds.",
            "Release them and notice the difference for a few breaths.",
            "Move up through your legs, hands, arms, shoulders and face.",
            "Finish by resting and breathing slowly.",
        ],
        "duration_minutes": 10,
        "difficulty": "gentle",
        "safety_note": (
            "Tense only gently, never to the point of pain. Skip any area with an "
            "injury."
        ),
        "sort_order": 10,
    },
    {
        "kind": "practice",
        "category": "relaxation",
        "title": "Slow breathing with a longer out-breath",
        "summary": "Breathe in gently, then breathe out a little more slowly.",
        "steps": [
            "Sit comfortably and rest one hand on your stomach.",
            "Breathe in gently through your nose for a count of four.",
            "Breathe out slowly through your mouth for a count of six.",
            "Repeat at a pace that feels easy.",
        ],
        "duration_minutes": 3,
        "difficulty": "gentle",
        "safety_note": BREATHE_SAFELY,
        "breath_in_seconds": 4,
        "breath_hold_seconds": 0,
        "breath_out_seconds": 6,
        "breath_hold_after_out_seconds": 0,
        "sort_order": 20,
    },
    # --- sleep -------------------------------------------------------------
    {
        "kind": "article",
        "category": "sleep",
        "title": "Building a wind-down routine",
        "summary": "Simple steps to help your evening move gently towards sleep.",
        "body": (
            "A short, calm routine before bed tells your body the day is "
            "ending.\n\n"
            "Ideas that may help:\n"
            "- Dim the lights a little in the hour before bed.\n"
            "- Put screens away for a while before sleeping.\n"
            "- Choose a quiet activity, such as reading or a gentle stretch.\n"
            "- Keep your bedroom comfortable, dark and quiet.\n\n"
            "If sleep problems continue, talk to your psychologist or doctor."
        ),
        "duration_minutes": 3,
        "difficulty": "gentle",
        "sort_order": 10,
    },
    {
        "kind": "article",
        "category": "sleep",
        "title": "Keeping a regular sleep and wake time",
        "summary": "Why a steady routine for sleeping and waking can help, and "
        "how to start.",
        "body": (
            "Going to bed and waking up at similar times each day, including "
            "weekends, helps many people feel more rested.\n\n"
            "Ideas that may help:\n"
            "- Pick a wake-up time you can keep most days.\n"
            "- Get some daylight soon after waking.\n"
            "- If you can't sleep, get up for a short quiet activity, then try "
            "again.\n\n"
            "If sleep problems continue, talk to your psychologist or doctor."
        ),
        "duration_minutes": 3,
        "difficulty": "gentle",
        "sort_order": 20,
    },
]


def seed(apps, schema_editor):
    WellnessItem = apps.get_model("wellness", "WellnessItem")
    for data in ITEMS:
        if WellnessItem.objects.filter(title=data["title"]).exists():
            continue
        item = WellnessItem(source=SOURCE, is_published=False, **data)
        item.save()


def unseed(apps, schema_editor):
    WellnessItem = apps.get_model("wellness", "WellnessItem")
    WellnessItem.objects.filter(
        source=SOURCE,
        title__in=[d["title"] for d in ITEMS],
        ever_linked=False,
        care_plan_tasks__isnull=True,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("wellness", "0001_initial"),
        ("recommendations", "0003_careplantask_content"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
