"""
Client for the Stripe API.

Eventually this module will wrap Stripe SDK calls (payment intents,
subscriptions, webhook signature verification) used by apps/payments,
keyed off STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET in settings.
"""
