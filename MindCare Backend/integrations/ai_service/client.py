"""
Client for the separate AI inference service.

Eventually this module will wrap HTTP calls to the standalone FastAPI
AI service (kept out of this Django monolith — see docs/decisions.md)
for things like generating draft patient recommendations. Per the
project's hard rule, anything this client returns must still pass
through the psychologist approval workflow in apps/recommendations
before it ever reaches a patient.
"""
