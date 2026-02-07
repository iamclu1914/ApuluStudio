# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Apulu Suite is a social media management dashboard for solopreneurs. It enables scheduling, cross-posting, and analytics across 7 platforms: Instagram, Facebook, X (Twitter), Bluesky, TikTok, Threads, and LinkedIn.

## Development Commands

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Testing
pytest
pytest -v --asyncio-mode=auto
```

### Frontend (Next.js 16)
```bash
cd frontend
npm install
npm run dev      # Development server on port 3000
npm run build    # Production build
npm run lint     # ESLint
```

### Docker (Recommended)
```bash
docker-compose up -d --build              # Development
docker-compose -f docker-compose.prod.yml up -d  # Production
start.bat                                  # Windows convenience script
stop.bat
```

### Service URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/api/docs

## Architecture

```
Frontend (Next.js App Router + TanStack Query + Zustand)
    │
    │ Axios REST API
    ▼
Backend (FastAPI + SQLAlchemy async)
    │
    ├── API Routes (/api/posts, /api/accounts, /api/analytics, /api/inbox, /api/ai)
    ├── Services Layer (scheduling, AI, storage, platforms)
    └── Platform Integrations (7 platforms via abstracted services)
    │
    ▼
PostgreSQL (Supabase) + Supabase Storage (media)
```

### Key Backend Patterns

**Async-first with dependency injection:**
```python
@router.get("/posts")
async def list_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    query = select(Post).options(selectinload(Post.platforms))
    result = await db.execute(query)
    return result.scalars().all()
```

**Platform abstraction** (`backend/app/services/platforms/`):
- `BasePlatformService` defines interface: `post_text()`, `post_image()`, `post_video()`, `get_engagement()`
- Concrete implementations: `MetaPlatformService`, `BlueskySkyService`, `LinkedInService`, `LATEService`

**Background scheduler** (`backend/app/services/background_scheduler.py`):
- AsyncIO task runs every 60 seconds
- Auto-publishes posts when `scheduled_at <= now`
- Updates status: SCHEDULED → PUBLISHING → PUBLISHED/FAILED

### Key Frontend Patterns

**State management:**
- Server state: TanStack Query (React Query v5)
- Client state: Zustand stores in `frontend/src/store/`

**API client** (`frontend/src/lib/api.ts`):
```typescript
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
})
```

## Database Models

Core models in `backend/app/models/`:
- **Post**: Master post with content, status (DRAFT/SCHEDULED/PUBLISHING/PUBLISHED/FAILED), media_urls, scheduled_at
- **PostPlatform**: Per-platform post with platform-specific content and engagement metrics
- **SocialAccount**: Connected platform accounts with OAuth tokens
- **User**: User with relationships to posts and accounts

## Platform Integration

| Platform | Integration |
|----------|-------------|
| Instagram, TikTok, X, Threads | LATE API |
| Facebook, Instagram (alt), Threads (alt) | Meta API |
| Bluesky | AT Protocol (atproto) |
| LinkedIn | LinkedIn API |

Platform requirements validation in `backend/app/services/platforms/requirements.py` (character limits, media types, hashtag rules).

## Environment Variables

**Backend (.env):**
```
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
LATE_API_KEY=...
OPENAI_API_KEY=...  # or ANTHROPIC_API_KEY
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## Key Directories

```
backend/app/
├── api/routes/      # FastAPI endpoints
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic validation schemas
├── services/        # Business logic
│   └── platforms/   # Platform-specific integrations
└── core/            # Config, database, middleware

frontend/src/
├── app/             # Next.js App Router pages
├── components/      # React components
├── lib/             # API client, utilities
├── store/           # Zustand stores
└── types/           # TypeScript definitions
```
