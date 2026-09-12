"""
Shared, app-agnostic DRF permission classes.

Eventually this module will hold cross-cutting permission checks used
by more than one app (e.g. role checks for patient/psychologist/admin
account types). Object-level ownership checks specific to a single
app's data (e.g. "is this psychologist's own patient") belong in that
app's own permissions.py instead, per the project's hard rule that
role-based access alone is never sufficient.
"""
