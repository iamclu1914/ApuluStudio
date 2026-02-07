# Apulu Suite Developer Guide

This guide provides everything you need to get started developing with Apulu Suite.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Backend Development](#backend-development)
6. [Frontend Development](#frontend-development)
7. [Platform Integrations](#platform-integrations)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| PostgreSQL | 15+ | Database (or use Supabase) |
| Git | Latest | Version control |
| Docker | Latest | Optional: containerized development |

### Recommended Tools

- **VS Code** with extensions:
  - Python
  - Pylance
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
- **Postman** or **Insomnia** for API testing
- **TablePlus** or **DBeaver** for database management

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd "Apulu Suite"

# Start all services
docker-compose up -d

# Or use the convenience script (Windows)
start.bat
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Option 2: Manual Setup

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

---

## Project Structure

```
Apulu Suite/
|
|-- backend/                    # FastAPI Backend
|   |-- app/
|   |   |-- api/
|   |   |   |-- routes/         # API endpoint handlers
|   |   |   |   |-- posts.py    # Post CRUD operations
|   |   |   |   |-- accounts.py # Social account management
|   |   |   |   |-- analytics.py# Analytics endpoints
|   |   |   |   |-- inbox.py    # Unified inbox
|   |   |   |   |-- ai.py       # AI content generation
|   |   |   |-- __init__.py
|   |   |
|   |   |-- core/               # Core configurations
|   |   |   |-- config.py       # Settings management
|   |   |   |-- database.py     # Database connection
|   |   |   |-- logger.py       # Logging setup
|   |   |   |-- constants.py    # Application constants
|   |   |
|   |   |-- models/             # SQLAlchemy ORM models
|   |   |   |-- user.py
|   |   |   |-- post.py
|   |   |   |-- social_account.py
|   |   |   |-- engagement.py
|   |   |
|   |   |-- schemas/            # Pydantic validation schemas
|   |   |   |-- post.py
|   |   |   |-- social_account.py
|   |   |   |-- analytics.py
|   |   |
|   |   |-- services/           # Business logic layer
|   |   |   |-- scheduler_service.py    # Post scheduling
|   |   |   |-- background_scheduler.py # Auto-publish daemon
|   |   |   |-- ai_service.py          # AI integrations
|   |   |   |-- storage_service.py     # Media storage
|   |   |   |-- smart_scheduler.py     # Optimal time suggestions
|   |   |   |-- platforms/             # Platform integrations
|   |   |       |-- base.py            # Abstract base class
|   |   |       |-- meta.py            # Instagram/Facebook/Threads
|   |   |       |-- linkedin.py
|   |   |       |-- bluesky.py
|   |   |       |-- late.py            # LATE API wrapper
|   |   |       |-- requirements.py    # Platform requirements
|   |   |
|   |   |-- main.py             # FastAPI application entry
|   |
|   |-- alembic/                # Database migrations
|   |-- requirements.txt
|   |-- Dockerfile
|
|-- frontend/                   # Next.js Frontend
|   |-- src/
|   |   |-- app/                # Next.js App Router pages
|   |   |   |-- page.tsx        # Landing page
|   |   |   |-- dashboard/
|   |   |   |-- calendar/
|   |   |   |-- inbox/
|   |   |   |-- analytics/
|   |   |   |-- settings/
|   |   |
|   |   |-- components/         # React components
|   |   |   |-- layout/         # Layout components
|   |   |   |-- posts/          # Post-related components
|   |   |   |-- analytics/      # Analytics components
|   |   |   |-- inbox/          # Inbox components
|   |   |   |-- ui/             # Reusable UI primitives
|   |   |
|   |   |-- lib/                # Utilities
|   |   |   |-- api.ts          # API client and types
|   |   |   |-- utils.ts        # Helper functions
|   |   |
|   |   |-- store/              # Zustand state stores
|   |   |-- types/              # TypeScript definitions
|   |
|   |-- package.json
|   |-- Dockerfile
|
|-- docs/                       # Documentation
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- CLAUDE.md                   # AI assistant context
|-- PROJECT_STATUS.md           # Current project status
```

---

## Development Workflow

### Git Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Push and create PR:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### Environment Files

**Backend `.env`:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/apulu

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Platform APIs
LATE_API_KEY=your-late-api-key

# Meta (Instagram/Facebook)
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret

# LinkedIn
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

**Frontend `.env.local`:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## Backend Development

### Creating a New API Endpoint

1. **Define the Pydantic schema** in `app/schemas/`:

```python
# app/schemas/example.py
from pydantic import BaseModel

class ExampleCreate(BaseModel):
    name: str
    description: str | None = None

class ExampleResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True
```

2. **Create the SQLAlchemy model** in `app/models/`:

```python
# app/models/example.py
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Example(Base):
    __tablename__ = "examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

3. **Create the API route** in `app/api/routes/`:

```python
# app/api/routes/example.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.example import Example
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter()

@router.post("", response_model=ExampleResponse)
async def create_example(
    data: ExampleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new example."""
    example = Example(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
    )
    db.add(example)
    await db.commit()
    await db.refresh(example)
    return example
```

4. **Register the router** in `app/api/routes/__init__.py`:

```python
from app.api.routes.example import router as example_router

# In main.py
app.include_router(example_router, prefix="/api/examples", tags=["examples"])
```

5. **Create a migration**:

```bash
alembic revision --autogenerate -m "add examples table"
alembic upgrade head
```

### Adding a New Platform Service

1. **Create the service class** extending `BasePlatformService`:

```python
# app/services/platforms/newplatform.py
from app.services.platforms.base import (
    BasePlatformService,
    PostResult,
    CommentResult,
    EngagementData,
)
from app.models.social_account import Platform

class NewPlatformService(BasePlatformService):
    platform = Platform.NEWPLATFORM
    API_BASE = "https://api.newplatform.com/v1"

    async def post_text(
        self,
        content: str,
        access_token: str,
        **kwargs,
    ) -> PostResult:
        # Implementation here
        pass

    # Implement all abstract methods...
```

2. **Add the platform enum** in `app/models/social_account.py`:

```python
class Platform(str, Enum):
    # ...existing platforms...
    NEWPLATFORM = "NEWPLATFORM"
```

3. **Register in SchedulerService**:

```python
# app/services/scheduler_service.py
self._platform_services[Platform.NEWPLATFORM] = NewPlatformService()
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## Frontend Development

### Creating a New Page

1. **Create the page file** in `src/app/`:

```tsx
// src/app/newpage/page.tsx
import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function NewPage() {
  return (
    <DashboardLayout>
      <div>
        <h1 className="text-2xl font-bold">New Page</h1>
        {/* Page content */}
      </div>
    </DashboardLayout>
  );
}
```

2. **Add to navigation** in `DashboardLayout.tsx`:

```tsx
const navigation = [
  // ...existing items...
  { name: "New Page", href: "/newpage", icon: SomeIcon },
];
```

### Using the API Client

```tsx
// Using TanStack Query for data fetching
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { postsApi } from "@/lib/api";

function MyComponent() {
  const queryClient = useQueryClient();

  // Fetching data
  const { data: posts, isLoading } = useQuery({
    queryKey: ["posts"],
    queryFn: () => postsApi.list().then(res => res.data),
  });

  // Mutating data
  const createPost = useMutation({
    mutationFn: (data) => postsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["posts"] });
      toast.success("Post created!");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Error");
    },
  });

  // Usage
  const handleSubmit = () => {
    createPost.mutate({
      content: "Hello world",
      platforms: ["INSTAGRAM"],
    });
  };
}
```

### Creating a New Component

```tsx
// src/components/ui/NewComponent.tsx
"use client";

import { cn } from "@/lib/utils";

interface NewComponentProps {
  title: string;
  className?: string;
  children: React.ReactNode;
}

export function NewComponent({ title, className, children }: NewComponentProps) {
  return (
    <div className={cn("p-4 rounded-lg bg-white shadow", className)}>
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </div>
  );
}
```

### State Management with Zustand

```tsx
// src/store/uiStore.ts
import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));

// Usage in component
function MyComponent() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  // ...
}
```

---

## Platform Integrations

### LATE API Integration

LATE API handles posting to Instagram, X, TikTok, and Threads. Configure by:

1. Get API key from [LATE](https://trylate.com)
2. Add to `.env`: `LATE_API_KEY=your-key`
3. Sync accounts: `POST /api/accounts/sync/late`

### Meta API (Instagram/Facebook)

1. Create a Meta Developer App
2. Configure OAuth redirect URIs
3. Add credentials to `.env`
4. Users connect via OAuth flow

### Bluesky

Uses App Passwords instead of OAuth:

1. Users create app password at bsky.app/settings
2. Connect via `POST /api/accounts/connect/bluesky`

### LinkedIn

1. Create LinkedIn Developer App
2. Configure OAuth settings
3. Add credentials to `.env`
4. Users connect via OAuth flow

---

## Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_posts.py

# Run with verbose output
pytest -v

# Run async tests
pytest -v --asyncio-mode=auto
```

### Frontend Testing

```bash
cd frontend

# Run tests
npm run test

# Run with coverage
npm run test:coverage

# Run linter
npm run lint
```

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

```
sqlalchemy.exc.OperationalError: connection refused
```

**Solution:** Ensure PostgreSQL is running and `DATABASE_URL` is correct.

#### CORS Errors

```
Access-Control-Allow-Origin header missing
```

**Solution:** Check CORS configuration in `app/main.py`. Ensure frontend URL is in allowed origins.

#### OAuth Callback Errors

```
Invalid OAuth state
```

**Solution:** OAuth state tokens expire. Retry the connection flow.

#### Media Upload Failures

```
Failed to upload media
```

**Solution:** Check Supabase Storage bucket permissions and file size limits.

### Debugging Tips

1. **Backend Logs:** Check terminal running `uvicorn`
2. **API Docs:** Test endpoints at `http://localhost:8000/api/docs`
3. **Database:** Use Alembic to check migration status
4. **Frontend:** Use React DevTools and Network tab

### Getting Help

1. Check existing documentation in `/docs`
2. Review `CLAUDE.md` for AI assistant context
3. Check `PROJECT_STATUS.md` for known issues
4. Open an issue on the repository

---

## Next Steps

- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for system design details
- Explore [API_REFERENCE.md](./API_REFERENCE.md) for all endpoints
- Check `PROJECT_STATUS.md` for current roadmap items
