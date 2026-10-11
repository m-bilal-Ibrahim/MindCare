# Handoff: AI assessment with recommendations (psychologist, Web)

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

### Response 200
Everything it returned before, plus:

```json
{
  "caveat": "Estimated severity and recommendation are a best-guess reconstruction (...) not validated clinical advice.",
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

`estimated_severity_tier` is one of `Minimal (1-2)`, `Mild (3-4)`, `Moderate (5-6)`,
`High (7-8)`, `Severe (9-10)`. `share_of_matching_patients` may be `null`.

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
