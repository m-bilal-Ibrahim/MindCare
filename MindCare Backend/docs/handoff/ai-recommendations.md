# Handoff: AI social anxiety assessment with recommendations (psychologist, Web)

Implements `MindCare Web/docs/ai-recommendations-api-contract.md` (on the
`web/ai-recommendations` branch) exactly. **No Web change is needed**: that branch
already reads the new fields when they are present.

## Endpoint

`POST /api/v1/ai/anxiety-prediction/`. Unchanged URL. Bearer JWT of an **approved,
active psychologist** (anyone else gets 403). Throttle `ai_prediction`, 20/min per
user. Nothing is stored or logged.

### Request
The 17 existing keys, plus two **optional** ones (send them only if the psychologist
filled them in; `null` is also accepted):

| Key | Type | Rule |
|---|---|---|
| `Gender` | string | `Female`, `Male` or `Other` |
| `Alcohol Consumption (drinks/week)` | number | 0–100 |

Bounds and messages for all keys: `docs/validation-rules.md` (AI form rows).

### What the model predicts
**Self-rated social anxiety** (Low / Medium / High). Call it "social anxiety" on every
screen, never just "anxiety" or a diagnosis. The URL keeps its old name.

### Response 200
Full example (the AI's `/patient-summary` answer, returned unchanged):

```json
{
  "caveat": "Estimated severity and recommendation are a best-guess reconstruction (...) not validated clinical advice.",
  "predicted_class": "Medium",
  "probabilities": {"Low": 0.31, "Medium": 0.67, "High": 0.02},
  "uncertainty_flag": false,
  "warnings": [],
  "estimated_caffeine_mg": 285.0,
  "estimated_stress_level": 6,
  "confidence": 0.67,
  "confidence_label": "borderline",
  "borderline_reasons": ["top two classes are close"],
  "borderline_between": ["Low", "Medium"],
  "estimated_severity_tier": "Moderate (5-6)",
  "severity_tier_basis": {
    "method": "most common tier for this predicted level and stress level in the data",
    "share_of_matching_patients": 0.8493,
    "matching_patients": 657
  },
  "recommendation_bundle": {
    "exercises": "4-7-8 Breathing 3x/day 5 min each; ...",
    "sleep_schedule": "Target: 8 hrs/night; ...",
    "nutrition": "Protein: 50 g/day; ..."
  }
}
```

#### Every response field
From `AnxietyPredictionResponseSerializer` (`apps/ai/api/serializers.py`), which
documents the AI's answer; the backend passes it through unchanged. All fields are
always present.

| Field | Type | Notes |
|---|---|---|
| `caveat` | string | Show first: the tier and bundle are an estimate for clinician review, not validated advice |
| `predicted_class` | string | `Low`, `Medium` or `High`: predicted self-rated social anxiety |
| `probabilities` | object | `Low`, `Medium`, `High`: each a number (0–1) |
| `uncertainty_flag` | boolean | `true` when P(High) ≥ 0.025: recommend priority review |
| `warnings` | array of string | May be empty |
| `estimated_caffeine_mg` | number | From the four caffeine servings |
| `estimated_stress_level` | integer | From the four stress answers |
| `confidence` | number | 0–1 |
| `confidence_label` | string | `confident` or `borderline` |
| `borderline_reasons` | array of string | Empty when confident |
| `borderline_between` | array of string, or `null` | The two close classes, e.g. `["Low", "Medium"]` |
| `estimated_severity_tier` | string | `Minimal (1-2)`, `Mild (3-4)`, `Moderate (5-6)`, `High (7-8)` or `Severe (9-10)`. An estimate, not a model prediction |
| `severity_tier_basis` | object | See below |
| `severity_tier_basis.method` | string | How the tier was picked |
| `severity_tier_basis.share_of_matching_patients` | number (0–1), or `null` | |
| `severity_tier_basis.matching_patients` | integer | |
| `recommendation_bundle` | object | The dataset's template text for the estimated tier; decision support only, never sent to a patient without review |
| `recommendation_bundle.exercises` | string | Free text, `;`-separated items |
| `recommendation_bundle.sleep_schedule` | string | Free text, `;`-separated items |
| `recommendation_bundle.nutrition` | string | Free text, `;`-separated items |

The `;`-separated layout is the AI's current template text, not a contract: display
each bundle string as text; splitting on `;` for a list is a presentation choice.

### Errors

| Status | Body | When |
|---|---|---|
| 400 | `{"<key>": ["<message>"]}` | Invalid input, e.g. `{"Age": ["Age must be a whole number between 18 and 49."]}` |
| 400 | `{"detail": "<the AI's explanation>"}` | The AI refused the input, e.g. an implausible caffeine total |
| 401 | — | Missing or expired token (refresh, then sign in) |
| 403 | `{"detail": ...}` | Not an approved, active psychologist |
| 429 | `{"detail": ...}` | More than 20 requests a minute |
| 503 | `{"detail": "The AI service is waking up. Please try again in a minute."}` | The AI service is asleep (Render cold start) or unreachable: retry |

## Screen
**Web → therapist console → AI assessment** (`AiAssessmentPage.tsx`). Show `caveat`
first, label the tier "Estimated, not predicted", then the three bundle sections.
Psychologist-facing only: never show any of this to a patient.

## Merge order
Merge `web/ai-recommendations` right after this backend PR is deployed.
