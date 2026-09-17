"""
Field-level encryption helpers for sensitive data at rest.

Eventually this module will provide encrypt/decrypt helpers (or a
custom model field) for PHI-bearing columns — journal content,
clinical notes, wearable health data — so that encryption-at-rest is
applied consistently across apps instead of being reimplemented per
model.
"""
