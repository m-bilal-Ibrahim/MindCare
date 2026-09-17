# Deployment

Not done yet. Placeholder — see @docs/decisions.md for the chosen providers
(Supabase/Neon for Postgres, Redis Cloud for Redis, Render for hosting).

## TODO: Render
- [ ] Create Render web service for this backend
- [ ] Set environment variables (see .env.example) in Render's dashboard
- [ ] Configure start command (gunicorn) and build command
- [ ] Set up Celery worker as a separate Render service

## TODO: Supabase / Neon (Postgres)
- [ ] Provision a Postgres instance
- [ ] Set `DATABASE_URL` in Render to the provisioned connection string
- [ ] Run migrations against the provisioned database

## TODO: Redis Cloud
- [ ] Provision a Redis instance
- [ ] Set `REDIS_URL` in Render to the provisioned connection string
