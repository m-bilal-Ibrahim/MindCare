"""
Shared exception types and a DRF exception handler.

Eventually this module will define domain-level exceptions (e.g.
PermissionDeniedForPatient, RecommendationNotApproved) and a custom
`exception_handler` wired into REST_FRAMEWORK['EXCEPTION_HANDLER'] so
every app raises and renders errors consistently instead of each
view inventing its own error shape.
"""
