"""DRF views for the communities API.

Views stay thin: parse the request, delegate to services.py (writes) or
selectors.py (reads), then serialize the result. No business logic here.
"""
