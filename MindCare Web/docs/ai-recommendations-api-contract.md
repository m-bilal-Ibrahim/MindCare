# AI recommendations — backend change the web is ready for

The web's **AI assessment** page (`/therapist/ai-assessment`) already shows the
recommendations, the estimated severity tier and the caveat **when the backend sends
them**. Today it doesn't, because the backend forwards to the AI service's `/predict`,
which has none of these. Nothing changes on the AI service: its `/patient-summary`
endpoint already returns everything.

Client code: `MindCare Web/src/services/psychologist.service.ts` (`predictAnxiety`,
`AnxietyPrediction`) and `MindCare Web/src/pages/AiAssessmentPage.tsx`.

## The change (backend, `apps/ai` + `integrations/ai_service`)

Keep the same endpoint and permissions:
`POST /api/v1/ai/anxiety-prediction/` — `IsAuthenticated`, `IsPsychologist`,
`IsApprovedPsychologist`, same throttle, nothing stored.

1. **Forward to `/patient-summary` instead of `/predict`**
   (`integrations/ai_service/client.py`, `PREDICT_PATH`). Its prediction fields are
   identical to `/predict`'s, with the same validation and age rules, so every existing
   response field stays the same.

2. **Accept two optional request keys** in `AnxietyPredictionRequestSerializer` and
   forward them unchanged:

   | Key | Type | Rule |
   |---|---|---|
   | `Gender` | string | `"Female"`, `"Male"` or `"Other"`; optional, may be null |
   | `Alcohol Consumption (drinks/week)` | number | 0–100; optional, may be null |

   The model never uses them; they only fill wording in the recommendations ("not
   provided" when missing). The web sends them only when the psychologist fills them in.

3. **Add these response fields** to `AnxietyPredictionResponseSerializer` (documentation
   only — the body is passed through unchanged):

   ```json
   {
     "caveat": "…",
     "estimated_severity_tier": "Moderate (5-6)",
     "severity_tier_basis": {
       "method": "…",
       "share_of_matching_patients": 0.61,
       "matching_patients": 412
     },
     "recommendation_bundle": {
       "exercises": "…",
       "sleep_schedule": "…",
       "nutrition": "…"
     }
   }
   ```

   `estimated_severity_tier` is one of `Minimal (1-2)`, `Mild (3-4)`, `Moderate (5-6)`,
   `High (7-8)`, `Severe (9-10)`. `share_of_matching_patients` may be null.

4. Update the `apps/ai` tests and `docs/module-reference.md`.

## Rules that stay in place

- Psychologist-facing only; the result is never sent to a patient.
- The web always shows `caveat` first in the result, and labels the tier as an
  estimate ("Estimated, not predicted"), because it is a best guess from the predicted
  class + stress level, not a model output.

## Compatibility

- **Before the backend change:** the web gets no recommendation fields and simply
  doesn't show that section. If the psychologist filled Gender/alcohol, the current
  backend answers `400 {"Gender": ["This field can't be set."]}`; the web then retries
  automatically without those two keys.
- **After the backend change:** the section appears with no further web changes.

## How to check it end-to-end

Sign in as an approved psychologist (e.g. Sara) → AI assessment → fill the form, with
and without Gender/alcohol → the result shows the caveat, the estimated tier and the
three recommendation sections.
