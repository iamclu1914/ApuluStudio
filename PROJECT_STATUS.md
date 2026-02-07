# Apulu Suite - Project Status

**Last Updated:** January 30, 2026

## Overview

Apulu Suite is an all-in-one social media management dashboard designed for solopreneurs. It enables scheduling, cross-posting, and analytics across multiple social media platforms.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16.1.6, React, TypeScript, Tailwind CSS, TanStack Query |
| **Backend** | FastAPI, Python 3.12, SQLAlchemy 2.0, Async PostgreSQL |
| **Database** | PostgreSQL (Supabase) |
| **Storage** | Supabase Storage |
| **AI** | OpenAI, Anthropic Claude |

## Supported Platforms

| Platform | Status | Integration |
|----------|--------|-------------|
| Instagram | ✅ Active | LATE API / Meta API |
| Facebook | ✅ Active | Meta API |
| X (Twitter) | ✅ Active | LATE API |
| Bluesky | ✅ Active | AT Protocol (atproto) |
| TikTok | ✅ Active | LATE API |
| Threads | ✅ Active | LATE API / Meta API |
| LinkedIn | ✅ Active | LinkedIn API |

## Current Features

### Post Management
- [x] Create and schedule posts
- [x] Cross-post to multiple platforms simultaneously
- [x] Draft posts for later
- [x] Edit scheduled posts with inline editing
- [x] Delete posts
- [x] Publish immediately option
- [x] Platform-specific content validation
- [x] Media upload (images/videos) to Supabase Storage

### Smart Scheduling
- [x] AI-powered optimal posting time suggestions
- [x] Platform-specific engagement patterns (7 platforms)
- [x] Cross-platform optimal time calculation
- [x] **Background scheduler for automatic publishing** (Fixed Jan 30, 2026)

### Analytics
- [x] Overview dashboard with engagement metrics
- [x] Per-platform statistics
- [x] Post performance tracking
- [x] Follower counts

### Inbox
- [x] Unified inbox for mentions/comments
- [x] Recent activity feed

### UI/UX
- [x] Responsive dashboard layout
- [x] Platform badges with brand colors
- [x] Emoji picker for posts
- [x] Calendar view for scheduled posts
- [x] Quick post composer with AI suggestions

## API Endpoints

### Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts` | List posts (paginated) |
| GET | `/api/posts/cursor` | List posts (cursor pagination) |
| GET | `/api/posts/calendar` | Get posts for calendar view |
| GET | `/api/posts/{id}` | Get single post |
| POST | `/api/posts` | Create post |
| PATCH | `/api/posts/{id}` | Update post |
| DELETE | `/api/posts/{id}` | Delete post |
| POST | `/api/posts/{id}/publish` | Publish immediately |
| POST | `/api/posts/upload` | Upload media |
| POST | `/api/posts/validate` | Validate content for platforms |
| GET | `/api/posts/requirements` | Get all platform requirements |
| GET | `/api/posts/requirements/{platform}` | Get platform requirements |
| GET | `/api/posts/schedule/suggestions` | Get AI scheduling suggestions |
| GET | `/api/posts/schedule/optimal-time` | Get optimal cross-platform time |

### Scheduler
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduler/status` | Check scheduler status |
| POST | `/api/scheduler/check-now` | Manually trigger publish check |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts` | List connected accounts |
| GET | `/api/analytics/overview` | Get analytics overview |
| GET | `/api/inbox` | Get inbox items |
| GET | `/api/ai/generate` | Generate AI content |
| GET | `/health` | Health check |

## Recent Updates (January 30, 2026)

### Bug Fixes
- **Fixed: Scheduled posts not publishing automatically**
  - Created `background_scheduler.py` service
  - Runs every 60 seconds to check for due posts
  - Integrated into FastAPI app lifecycle
  - Added `/api/scheduler/status` and `/api/scheduler/check-now` endpoints

### Infrastructure
- Added Docker support for production deployment
  - `docker-compose.yml` - Development setup
  - `docker-compose.prod.yml` - Production setup with resource limits
  - Dockerfiles for frontend and backend (dev + prod variants)
  - Auto-restart policies for reliability
  - Health checks for both services

## Running the Project

### Development (Manual)
```bash
# Backend
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Development (Docker)
```bash
# Requires Docker Desktop
docker-compose up -d

# Or use the convenience script
start.bat
```

### Production (Docker)
```bash
docker-compose -f docker-compose.prod.yml up -d

# Or
start.bat prod
```

## Service URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |

## Environment Variables

### Backend (`.env`)
```
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
LATE_API_KEY=...  # Optional: for Instagram, TikTok, X, Threads
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## Project Structure

```
Apulu Suite/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── core/             # Config, database, logging
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   │       ├── platforms/    # Platform integrations
│   │       ├── scheduler_service.py
│   │       ├── smart_scheduler.py
│   │       └── background_scheduler.py
│   ├── alembic/              # Database migrations
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── lib/              # Utilities, API client
│   │   └── types/            # TypeScript types
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── package.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── start.bat
├── stop.bat
└── PROJECT_STATUS.md
```

## Known Issues

None currently.

## Roadmap

- [ ] User authentication (OAuth)
- [ ] Team collaboration features
- [ ] Advanced analytics with charts
- [ ] Content calendar drag-and-drop
- [ ] Hashtag suggestions
- [ ] Competitor analysis
- [ ] Bulk scheduling from CSV
- [ ] Mobile app (React Native)
