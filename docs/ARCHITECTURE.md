# Apulu Suite Architecture

This document provides a comprehensive overview of the Apulu Suite system architecture, including component relationships, data flows, and design patterns.

## System Overview

Apulu Suite is a social media management dashboard designed for solopreneurs. It enables scheduling, cross-posting, and analytics across 7 platforms: Instagram, Facebook, X (Twitter), Bluesky, TikTok, Threads, and LinkedIn.

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Frontend ["Frontend (Next.js 16)"]
        UI[React Components]
        TQ[TanStack Query]
        ZS[Zustand Stores]
        API_Client[Axios API Client]
    end

    subgraph Backend ["Backend (FastAPI)"]
        Routes[API Routes]
        Services[Service Layer]
        Models[SQLAlchemy Models]
        BG[Background Scheduler]
    end

    subgraph External ["External Services"]
        DB[(PostgreSQL / Supabase)]
        Storage[Supabase Storage]
        AI[AI Services]
        Platforms[Social Platforms]
    end

    UI --> TQ
    UI --> ZS
    TQ --> API_Client
    API_Client --> Routes

    Routes --> Services
    Services --> Models
    Models --> DB

    Services --> Storage
    Services --> AI
    Services --> Platforms

    BG --> Services
    BG --> Models
```

## Component Architecture

### Frontend Architecture

```mermaid
flowchart TB
    subgraph AppRouter ["Next.js App Router"]
        Pages["/app Pages"]
        Layouts["Layout Components"]
    end

    subgraph Components ["React Components"]
        Layout["DashboardLayout"]
        Posts["Post Components"]
        Analytics["Analytics Components"]
        Inbox["Inbox Components"]
        UI["UI Primitives"]
    end

    subgraph State ["State Management"]
        ServerState["TanStack Query<br/>(Server State)"]
        ClientState["Zustand Stores<br/>(Client State)"]
    end

    subgraph API ["API Layer"]
        APIClient["api.ts<br/>(Axios Instance)"]
        APIModules["postsApi | accountsApi<br/>analyticsApi | aiApi | inboxApi"]
    end

    Pages --> Layout
    Layout --> Components
    Components --> ServerState
    Components --> ClientState
    ServerState --> APIModules
    APIModules --> APIClient
```

**Key Frontend Technologies:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 16.1.6 | Server-side rendering, App Router |
| UI Library | React 19 | Component-based UI |
| Styling | Tailwind CSS | Utility-first styling |
| Server State | TanStack Query v5 | Data fetching, caching |
| Client State | Zustand | Global UI state |
| HTTP Client | Axios | API communication |
| Icons | Lucide React | Icon library |

### Backend Architecture

```mermaid
flowchart TB
    subgraph API ["API Layer"]
        PostsRouter["/api/posts"]
        AccountsRouter["/api/accounts"]
        AnalyticsRouter["/api/analytics"]
        InboxRouter["/api/inbox"]
        AIRouter["/api/ai"]
        SchedulerRouter["/api/scheduler"]
    end

    subgraph Services ["Service Layer"]
        SchedulerSvc["SchedulerService"]
        AISvc["AIService"]
        StorageSvc["StorageService"]
        SmartScheduler["SmartScheduler"]
        BackgroundSvc["BackgroundScheduler"]
    end

    subgraph Platforms ["Platform Services"]
        BasePlatform["BasePlatformService"]
        MetaSvc["MetaService"]
        LinkedInSvc["LinkedInService"]
        BlueskySvc["BlueskyService"]
        LateSvc["LateService"]
    end

    subgraph Data ["Data Layer"]
        Models["SQLAlchemy Models"]
        Schemas["Pydantic Schemas"]
        DB[(PostgreSQL)]
    end

    API --> Services
    Services --> Platforms
    Services --> Data
    Platforms --> BasePlatform
    BackgroundSvc --> SchedulerSvc
```

## Data Models

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ SocialAccount : has
    User ||--o{ Post : creates

    Post ||--o{ PostPlatform : "publishes to"

    SocialAccount ||--o{ PostPlatform : receives
    SocialAccount ||--o{ Comment : receives
    SocialAccount ||--o{ Mention : receives

    PostPlatform ||--o{ Comment : has

    User {
        string id PK
        string email UK
        string name
        string avatar_url
        boolean is_active
        int max_social_accounts
        datetime created_at
        datetime updated_at
    }

    Post {
        string id PK
        string user_id FK
        string content
        string post_type
        array media_urls
        array hashtags
        string status
        datetime scheduled_at
        datetime published_at
        boolean ai_generated
    }

    PostPlatform {
        string id PK
        string post_id FK
        string social_account_id FK
        string status
        string content
        string platform_post_id
        string platform_post_url
        int likes_count
        int comments_count
        int shares_count
        datetime published_at
        string error_message
    }

    SocialAccount {
        string id PK
        string user_id FK
        string platform
        string platform_user_id
        string username
        string display_name
        string avatar_url
        string access_token
        int follower_count
        int following_count
        datetime last_synced
    }

    Comment {
        string id PK
        string social_account_id FK
        string post_platform_id FK
        string content
        string author_username
        boolean is_read
        boolean is_replied
        datetime posted_at
    }

    Mention {
        string id PK
        string social_account_id FK
        string content
        string mention_type
        string author_username
        boolean is_read
        datetime mentioned_at
    }
```

### Post Status Flow

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Create post
    DRAFT --> SCHEDULED: Set schedule time
    DRAFT --> PUBLISHING: Publish now
    SCHEDULED --> PUBLISHING: Time reached
    PUBLISHING --> PUBLISHED: Success
    PUBLISHING --> FAILED: Error
    FAILED --> SCHEDULED: Retry
    FAILED --> DRAFT: Cancel
    PUBLISHED --> [*]
```

## Platform Service Abstraction

The platform service pattern uses the Strategy pattern to abstract platform-specific implementations behind a common interface.

### Class Hierarchy

```mermaid
classDiagram
    class BasePlatformService {
        <<abstract>>
        +platform: Platform
        +post_text(content, access_token)*
        +post_image(content, image_url, access_token)*
        +post_video(content, video_url, access_token)*
        +delete_post(post_id, access_token)*
        +get_engagement(post_id, access_token)*
        +reply_to_comment(comment_id, content, access_token)*
        +get_comments(post_id, access_token)*
        +get_profile(access_token)*
        +refresh_token(refresh_token)*
    }

    class MetaService {
        +GRAPH_API_BASE: string
        +platform: Platform
        -_post_instagram_image()
        -_post_facebook_image()
        -_post_threads()
        -_post_instagram_reel()
    }

    class LinkedInService {
        +API_BASE: string
        +REST_API_BASE: string
        -_initialize_upload()
    }

    class BlueskyService {
        +ATP_SERVICE: string
        -_resolve_handle()
        -_create_session()
    }

    class LateService {
        +LATE_API_BASE: string
        +get_accounts()
    }

    BasePlatformService <|-- MetaService
    BasePlatformService <|-- LinkedInService
    BasePlatformService <|-- BlueskyService
    BasePlatformService <|-- LateService
```

### Result Types

```mermaid
classDiagram
    class PostResult {
        +success: bool
        +platform: Platform
        +platform_post_id: string
        +platform_post_url: string
        +error_message: string
        +raw_response: dict
    }

    class CommentResult {
        +success: bool
        +platform: Platform
        +comment_id: string
        +error_message: string
    }

    class EngagementData {
        +likes: int
        +comments: int
        +shares: int
        +impressions: int
        +reach: int
    }
```

## Background Scheduler Flow

The background scheduler handles automatic publishing of scheduled posts.

```mermaid
sequenceDiagram
    participant BG as BackgroundScheduler
    participant DB as Database
    participant SS as SchedulerService
    participant PS as PlatformService
    participant API as Platform API

    loop Every 60 seconds
        BG->>DB: Query due posts (status=SCHEDULED, scheduled_at <= now)
        DB-->>BG: Return due posts

        alt Posts found
            loop For each post
                BG->>SS: publish_post(post)
                SS->>DB: Update status to PUBLISHING

                loop For each platform target
                    SS->>PS: post_image/post_text()
                    PS->>API: Send content
                    API-->>PS: Response
                    PS-->>SS: PostResult
                    SS->>DB: Update PostPlatform status
                end

                SS->>DB: Update Post status (PUBLISHED/FAILED)
                SS-->>BG: Results
            end
        end
    end
```

## Data Flow Diagrams

### Post Creation Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as QuickPost Component
    participant TQ as TanStack Query
    participant API as FastAPI
    participant Val as Validator
    participant DB as Database
    participant Storage as Supabase Storage

    User->>UI: Enter content, select platforms
    User->>UI: Add media (optional)

    alt Has media
        UI->>Storage: Upload file
        Storage-->>UI: Media URL
    end

    User->>UI: Click "Post Now" / "Schedule"
    UI->>TQ: createPost mutation
    TQ->>API: POST /api/posts

    API->>Val: Validate content for platforms
    Val-->>API: Validation result

    alt Validation fails
        API-->>TQ: 400 Error with details
        TQ-->>UI: Show validation errors
    end

    API->>DB: Create Post + PostPlatform records
    DB-->>API: Post created

    alt Publish Now
        API->>API: Trigger immediate publish
    end

    API-->>TQ: Post response
    TQ-->>UI: Update UI, invalidate queries
    UI-->>User: Success notification
```

### OAuth Connection Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant OAuth as OAuth Provider
    participant DB as Database

    User->>Frontend: Click "Connect Platform"
    Frontend->>Backend: GET /api/accounts/connect/{platform}
    Backend->>Backend: Generate state token
    Backend-->>Frontend: Return auth_url + state
    Frontend->>OAuth: Redirect to auth URL

    User->>OAuth: Authorize app
    OAuth->>Backend: Callback with code + state

    Backend->>Backend: Verify state token
    Backend->>OAuth: Exchange code for tokens
    OAuth-->>Backend: Access token + refresh token

    Backend->>OAuth: Get user profile
    OAuth-->>Backend: Profile data

    Backend->>DB: Create/update SocialAccount
    DB-->>Backend: Account saved

    Backend-->>Frontend: Redirect to settings
    Frontend-->>User: Show connected account
```

## Technology Stack Summary

### Backend Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | Latest |
| Runtime | Python | 3.12 |
| ORM | SQLAlchemy | 2.0 |
| Database | PostgreSQL | Via Supabase |
| Async Driver | asyncpg | Latest |
| HTTP Client | httpx | Latest |
| Validation | Pydantic | v2 |
| Migrations | Alembic | Latest |

### Frontend Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | Next.js | 16.1.6 |
| Language | TypeScript | 5.x |
| UI Library | React | 19.x |
| Styling | Tailwind CSS | 4.x |
| State (Server) | TanStack Query | 5.x |
| State (Client) | Zustand | Latest |
| HTTP Client | Axios | Latest |
| Notifications | React Hot Toast | Latest |

### Infrastructure

| Component | Service |
|-----------|---------|
| Database | Supabase PostgreSQL |
| File Storage | Supabase Storage |
| AI Services | OpenAI / Anthropic Claude |
| Containerization | Docker / Docker Compose |

## Security Considerations

1. **OAuth State Tokens**: Temporary state tokens prevent CSRF attacks during OAuth flows
2. **Token Storage**: Access tokens stored encrypted in database (production recommendation)
3. **API Key Management**: Environment variables for sensitive credentials
4. **Input Validation**: Pydantic schemas validate all input data
5. **Platform-Specific Validation**: Content validated against platform requirements before posting

## Scalability Notes

1. **Background Scheduler**: Runs as asyncio task; for high-volume, consider Celery or similar
2. **Database Connections**: Async session with connection pooling via SQLAlchemy
3. **Cursor Pagination**: O(1) pagination for large post lists
4. **Media Processing**: Images auto-cropped on upload; consider queueing for high volume
5. **Rate Limiting**: Platform APIs have rate limits; implement backoff strategies in production
