# Deployment (Production)

This guide deploys:
- Backend: Render (FastAPI)
- Frontend: Vercel (Next.js)

If you want a different host, say the word and we can swap the config.

## 1) Push to GitHub
Make sure the repo is in GitHub so the hosts can pull from it.

## 2) Backend on Render
Use the `render.yaml` at repo root.

Steps:
1) Create a new Render service from this repo.
2) Render will detect `render.yaml` and create the backend service.
3) Set the required environment variables (below).
4) Deploy.

### Required backend env vars
Set these in Render > Environment:
- `DEBUG=false`
- `SECRET_KEY`
- `ENCRYPTION_KEY`
- `DATABASE_URL`
- `DATABASE_SSL_MODE` (recommend `require` or `verify-full`)
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `AI_PROVIDER` (`openai` or `anthropic`)
- `LATE_API_KEY`
- `LATE_SYNC_INTERVAL_SECONDS` (default `300`)
- `LATE_SYNC_USER_ID` (recommended in production)
- `FRONTEND_URL` (Vercel app URL)
- `BACKEND_URL` (Render backend URL)

### Database migrations
Run once after the first deploy:
```
alembic upgrade head
```
You can run this as a one-off command in Render or from your local machine using the same `DATABASE_URL`.

### Scheduler
The backend runs a background scheduler. Keep a single backend instance to avoid duplicate publishes.

## 3) Frontend on Vercel
Create a Vercel project and set the root directory to `frontend/`.

Set environment variables:
- `NEXT_PUBLIC_API_URL=https://<your-backend-domain>/api`
- `NEXT_PUBLIC_APP_NAME=Apulu Studio`

Deploy.

## 4) Verify
Open:
- Backend health: `https://<backend>/health`
- Frontend: `https://<frontend>/`

## 5) Production safety checklist
- `DEBUG=false` on backend
- Remove local dev secrets from `.env`
- Confirm CORS allows your frontend URL (`FRONTEND_URL`)
- Use an App Password for Bluesky (not your main password)
