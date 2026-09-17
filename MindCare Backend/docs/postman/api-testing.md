# API Testing — Postman Setup

We don't maintain a hand-written Postman collection file. It would drift out of
sync the moment an endpoint changes, silently, until someone notices requests
failing for the wrong reason. Instead, we keep the collection *generated live*
from the same source of truth as the code itself.

## Why: drf-spectacular already gives us this

Phase 0 wired up `drf-spectacular`, which generates an OpenAPI schema directly
from the DRF serializers and views — always accurate, because it's derived from
the real code, not written by hand alongside it.

- Schema (JSON): `/api/schema/`
- Interactive docs (Swagger UI): `/api/docs/`

## Importing into Postman (do this once, refresh anytime)

1. Postman → **Import** → **Link**
2. Paste the schema URL:
   - Local dev: `http://localhost:8000/api/schema/`
   - Deployed (Render): `https://<your-render-url>/api/schema/`
3. Postman builds a full collection — every endpoint, every request/response
   shape — automatically.
4. Whenever new endpoints land, click **Import** again with the same link and
   choose "replace" to refresh. No manual collection editing, ever.

## Environment switching

Two environment files are included in this folder:
- `mindcare-local.postman_environment.json` — points at `localhost:8000`
- `mindcare-prod.postman_environment.json` — points at the deployed Render URL
  (fill in the real URL once Phase 1 is deployed — see `docs/deployment.md`)

Import both (**Import** → select files), then use the environment dropdown
(top-right in Postman) to switch between local and live — same collection,
same requests, different `base_url`.

## For frontend integration

Anyone on the Web or App team can import the same schema link themselves — no
handoff document, no "here's a doc of our endpoints" that goes stale a week
later. The live schema *is* the handoff, and it can't go out of date because
there's nothing separate to remember to update.
