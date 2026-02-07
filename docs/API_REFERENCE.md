# Apulu Suite API Reference

This document provides a comprehensive reference for all API endpoints in Apulu Suite.

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: Configure via `NEXT_PUBLIC_API_URL` environment variable

## Interactive Documentation

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

---

## Posts API

Endpoints for managing social media posts.

### List Posts

```http
GET /api/posts
```

List all posts with optional filtering and pagination.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | - | Filter by status: `draft`, `scheduled`, `publishing`, `published`, `failed` |
| `platform` | string | No | - | Filter by platform |
| `page` | integer | No | 1 | Page number (1-indexed) |
| `per_page` | integer | No | 20 | Items per page (max: 100) |

**Response:**

```json
{
  "posts": [
    {
      "id": "uuid",
      "content": "Post content",
      "post_type": "text",
      "media_urls": ["https://..."],
      "thumbnail_url": null,
      "hashtags": ["tag1", "tag2"],
      "status": "scheduled",
      "scheduled_at": "2026-01-31T14:00:00Z",
      "published_at": null,
      "ai_generated": false,
      "created_at": "2026-01-30T10:00:00Z",
      "updated_at": "2026-01-30T10:00:00Z",
      "platforms": [
        {
          "id": "uuid",
          "platform": "INSTAGRAM",
          "username": "user123",
          "status": "scheduled",
          "content": null,
          "platform_post_url": null,
          "likes_count": 0,
          "comments_count": 0,
          "shares_count": 0,
          "published_at": null,
          "error_message": null
        }
      ]
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "has_next": true
}
```

### List Posts (Cursor Pagination)

```http
GET /api/posts/cursor
```

List posts with cursor-based pagination. O(1) performance for large datasets.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | - | Filter by status |
| `cursor` | string | No | - | Last post ID from previous page |
| `limit` | integer | No | 20 | Items per page (max: 100) |

**Response:**

```json
{
  "posts": [...],
  "next_cursor": "post-uuid",
  "has_more": true
}
```

### Get Calendar Posts

```http
GET /api/posts/calendar
```

Get posts within a date range for calendar view.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | datetime | Yes | ISO 8601 start date |
| `end_date` | datetime | Yes | ISO 8601 end date |

### Get Single Post

```http
GET /api/posts/{post_id}
```

Retrieve a single post by ID.

### Create Post

```http
POST /api/posts
```

Create a new post (draft or scheduled).

**Request Body:**

```json
{
  "content": "Your post content here",
  "platforms": ["INSTAGRAM", "FACEBOOK", "X"],
  "scheduled_at": "2026-01-31T14:00:00Z",
  "media_urls": ["https://storage.url/image.jpg"],
  "hashtags": ["social", "marketing"],
  "post_type": "image",
  "ai_generated": false,
  "ai_prompt": null
}
```

**Post Types:** `text`, `image`, `video`, `carousel`, `story`, `reel`

**Platforms:** `INSTAGRAM`, `FACEBOOK`, `X`, `BLUESKY`, `TIKTOK`, `THREADS`, `LINKEDIN`

**Response:** Returns the created post object.

### Update Post

```http
PATCH /api/posts/{post_id}
```

Update a draft or scheduled post.

**Request Body:**

```json
{
  "content": "Updated content",
  "hashtags": ["updated", "tags"],
  "scheduled_at": "2026-02-01T10:00:00Z",
  "status": "scheduled"
}
```

### Delete Post

```http
DELETE /api/posts/{post_id}
```

Delete a post. Returns `{"success": true}` on success.

### Publish Now

```http
POST /api/posts/{post_id}/publish
```

Immediately publish a draft, scheduled, or failed post.

**Response:**

```json
{
  "success": true,
  "results": {
    "platform-post-uuid": {
      "success": true,
      "platform": "INSTAGRAM",
      "post_id": "ig-post-id",
      "url": "https://instagram.com/p/...",
      "error": null
    }
  }
}
```

### Upload Media

```http
POST /api/posts/upload
```

Upload media file for a post.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Image or video file |
| `platforms` | string | No | Comma-separated platforms for auto-crop |
| `aspect_ratio` | string | No | Force aspect ratio: `1:1`, `4:5`, `16:9`, `9:16`, `original` |

**Supported Formats:**
- Images: JPEG, PNG, GIF, WebP (max 10MB)
- Videos: MP4, QuickTime, WebM (max 100MB)

**Response:**

```json
{
  "success": true,
  "url": "https://storage.supabase.co/...",
  "filename": "image.jpg",
  "content_type": "image/jpeg",
  "size": 245678,
  "cropped": true
}
```

### Validate Content

```http
POST /api/posts/validate
```

Validate content against platform requirements before posting.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | No | Post content |
| `platforms` | array | Yes | List of platforms |
| `media_urls` | array | No | Media URLs |

**Response:**

```json
{
  "valid": false,
  "platforms": {
    "INSTAGRAM": {
      "valid": false,
      "errors": [
        {"field": "media", "message": "Instagram requires an image or video"}
      ],
      "warnings": []
    },
    "FACEBOOK": {
      "valid": true,
      "errors": [],
      "warnings": []
    }
  }
}
```

### Get Platform Requirements

```http
GET /api/posts/requirements
GET /api/posts/requirements/{platform}
```

Get posting requirements for all platforms or a specific platform.

**Response (single platform):**

```json
{
  "platform": "INSTAGRAM",
  "displayName": "Instagram",
  "media": {
    "mediaRequired": true,
    "maxImages": 10,
    "maxVideos": 1,
    "maxImageSizeMb": 8,
    "maxVideoSizeMb": 100,
    "maxVideoDurationSeconds": 60,
    "supportedImageFormats": ["jpg", "jpeg", "png"],
    "supportedVideoFormats": ["mp4", "mov"],
    "canMixMediaTypes": false,
    "recommendedImageSize": "1080x1350"
  },
  "content": {
    "maxCaptionLength": 2200,
    "supportsHashtags": true,
    "supportsMentions": true,
    "supportsLinks": false
  },
  "notes": ["Instagram requires at least one image or video"]
}
```

### Get Schedule Suggestions

```http
GET /api/posts/schedule/suggestions
```

Get AI-powered optimal posting time suggestions.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `platforms` | string | Yes | Comma-separated platform names |

**Response:**

```json
{
  "suggestions": {
    "INSTAGRAM": {
      "platform": "INSTAGRAM",
      "best_time": {
        "datetime": "2026-01-31T19:00:00Z",
        "engagement_level": "peak",
        "score": 95,
        "reason": "Peak engagement on Friday evenings"
      },
      "alternative_times": [
        {
          "datetime": "2026-01-31T11:00:00Z",
          "engagement_level": "high",
          "score": 85,
          "reason": "Lunch break browsing"
        }
      ],
      "insights": ["Your audience is most active between 6-9 PM"]
    }
  },
  "generated_at": "2026-01-31T10:00:00Z"
}
```

### Get Optimal Cross-Platform Time

```http
GET /api/posts/schedule/optimal-time
```

Get the single best time to post across multiple platforms.

**Query Parameters:** Same as schedule suggestions.

---

## Accounts API

Endpoints for managing connected social accounts.

### List Accounts

```http
GET /api/accounts
```

List all connected social accounts.

### Get Connection Status

```http
GET /api/accounts/status
```

Get connection status for all platforms.

**Response:**

```json
[
  {
    "platform": "instagram",
    "connected": true,
    "account": {...},
    "requires_reconnect": false
  },
  {
    "platform": "facebook",
    "connected": false,
    "account": null,
    "requires_reconnect": false
  }
]
```

### Sync LATE Accounts

```http
POST /api/accounts/sync/late
```

Sync accounts connected via LATE API into Apulu Suite.

**Response:**

```json
{
  "success": true,
  "synced": [
    {"platform": "INSTAGRAM", "username": "user123", "followers": 5000, "action": "updated"}
  ],
  "message": "Synced 1 account(s) from LATE"
}
```

### Get LATE Profiles

```http
GET /api/accounts/late/profiles
```

Get accounts directly from LATE API without syncing to database.

### Get Single Account

```http
GET /api/accounts/{account_id}
```

### Update Account Preferences

```http
PATCH /api/accounts/{account_id}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `preferred_aspect_ratio` | string | `original`, `1:1`, `4:5`, `16:9`, `9:16` |

### Disconnect Account

```http
DELETE /api/accounts/{account_id}
```

### Connect Bluesky

```http
GET /api/accounts/connect/bluesky
POST /api/accounts/connect/bluesky
```

Bluesky uses App Passwords instead of OAuth.

**POST Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `handle` | string | Yes | Bluesky handle (e.g., `user.bsky.social`) |
| `app_password` | string | Yes | App Password from bsky.app settings |

### Connect Meta (Instagram/Facebook)

```http
GET /api/accounts/connect/instagram
GET /api/accounts/connect/facebook
```

Returns OAuth URL to redirect user for authorization.

```json
{
  "auth_url": "https://facebook.com/v19.0/dialog/oauth?...",
  "state": "random-state-token"
}
```

### Connect LinkedIn

```http
GET /api/accounts/connect/linkedin
```

Returns OAuth URL for LinkedIn authorization.

### OAuth Callbacks

```http
GET /api/accounts/callback/meta
GET /api/accounts/callback/linkedin
```

Internal callback endpoints for OAuth flows. Redirect users here after authorization.

### Sync Account Data

```http
POST /api/accounts/{account_id}/sync
```

Refresh account data (followers, profile info).

---

## Analytics API

Endpoints for retrieving analytics and insights.

### Get Overview Stats

```http
GET /api/analytics/overview
```

Get aggregated overview statistics.

**Response:**

```json
{
  "total_followers": 15000,
  "total_engagement": 2500,
  "posts_this_week": 12,
  "engagement_rate": 4.2,
  "platforms": [
    {
      "platform": "INSTAGRAM",
      "followers": 8000,
      "following": 500,
      "posts_count": 150,
      "engagement_rate": 5.1
    }
  ]
}
```

### Get Growth Data

```http
GET /api/analytics/growth
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `platform` | string | - | Filter by platform |
| `days` | integer | 30 | Days of data to return |

### Get Top Posts

```http
GET /api/analytics/top-posts
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 30 | Time period |
| `limit` | integer | 10 | Max posts to return |

### Get Weekly Report

```http
GET /api/analytics/weekly-report
```

Get a summary report for the past week.

---

## Inbox API

Endpoints for the unified inbox (comments and mentions).

### Get Inbox Items

```http
GET /api/inbox
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `platform` | string | - | Filter by platform |
| `unread_only` | boolean | false | Only unread items |
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page |

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "type": "comment",
      "platform": "INSTAGRAM",
      "content": "Great post!",
      "author_username": "follower123",
      "author_avatar_url": "https://...",
      "is_read": false,
      "timestamp": "2026-01-30T15:30:00Z",
      "post_url": "https://instagram.com/p/...",
      "is_replied": false,
      "likes_count": 5
    }
  ],
  "total": 100,
  "unread_count": 15,
  "page": 1,
  "has_next": true
}
```

### Sync Inbox

```http
POST /api/inbox/sync
```

Fetch new comments and mentions from platforms.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | string | Sync specific platform only |

### Mark Comment as Read

```http
POST /api/inbox/comments/{comment_id}/read
```

### Reply to Comment

```http
POST /api/inbox/comments/{comment_id}/reply
```

**Request Body:**

```json
{
  "content": "Thank you!"
}
```

### Mark Mention as Read

```http
POST /api/inbox/mentions/{mention_id}/read
```

### Mark All as Read

```http
POST /api/inbox/read-all
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | string | Mark only specific platform as read |

---

## AI API

Endpoints for AI-powered content generation.

### Generate Caption

```http
POST /api/ai/generate-caption
```

Generate caption variations for a topic.

**Request Body:**

```json
{
  "topic": "Monday motivation for entrepreneurs",
  "url": null,
  "tone": "professional",
  "platform": "LINKEDIN",
  "include_hashtags": true,
  "max_length": 500
}
```

**Response:**

```json
{
  "topic": "Monday motivation for entrepreneurs",
  "variations": [
    {
      "tone": "professional",
      "caption": "Start your week with purpose...",
      "hashtags": ["MondayMotivation", "Entrepreneur", "Success"],
      "character_count": 245
    },
    {
      "tone": "casual",
      "caption": "New week, new opportunities!...",
      "hashtags": ["MondayVibes", "StartupLife"],
      "character_count": 198
    }
  ],
  "generated_at": "2026-01-31T10:00:00Z"
}
```

### Generate Hashtags

```http
POST /api/ai/generate-hashtags
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | string | - | Content to analyze |
| `platform` | string | - | Target platform |
| `count` | integer | 10 | Number of hashtags |

**Response:**

```json
{
  "hashtags": ["socialmedia", "marketing", "growth", "entrepreneur"]
}
```

### Optimize Content

```http
POST /api/ai/optimize-content
```

Optimize content for a specific platform.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | Original content |
| `target_platform` | string | Yes | Target platform |
| `source_platform` | string | No | Source platform (for conversion) |

**Response:**

```json
{
  "original": "Original long-form content...",
  "optimized": "Optimized content for X...",
  "target_platform": "X"
}
```

### Get Character Limits

```http
GET /api/ai/character-limits
```

Get character limits for all platforms.

**Response:**

```json
{
  "limits": {
    "X": 280,
    "INSTAGRAM": 2200,
    "FACEBOOK": 63206,
    "LINKEDIN": 3000,
    "THREADS": 500,
    "BLUESKY": 300,
    "TIKTOK": 2200
  }
}
```

---

## Scheduler API

Endpoints for the background scheduler service.

### Get Scheduler Status

```http
GET /api/scheduler/status
```

Check if the background scheduler is running.

**Response:**

```json
{
  "running": true,
  "check_interval": 60
}
```

### Trigger Manual Check

```http
POST /api/scheduler/check-now
```

Manually trigger a check for due posts (useful for testing).

---

## Health Check

```http
GET /health
```

Check API health status.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T10:00:00Z"
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request

```json
{
  "detail": "Error message describing the problem"
}
```

Or for validation errors:

```json
{
  "detail": {
    "message": "Content validation failed",
    "errors": ["INSTAGRAM: Media is required"],
    "warnings": ["Caption is close to character limit"]
  }
}
```

### 404 Not Found

```json
{
  "detail": "Post not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error message"
}
```

---

## Rate Limits

Platform APIs have their own rate limits. Apulu Suite implements backoff strategies, but be aware of:

| Platform | Typical Limits |
|----------|---------------|
| Instagram | 25 posts/day |
| Facebook | 100 API calls/hour |
| LinkedIn | 100 posts/day |
| Bluesky | 50 posts/day |
| X (Twitter) | Varies by tier |
| TikTok | 50 posts/day |

---

## Authentication

Currently, the API uses a temporary user ID for development. In production, implement proper authentication using:

- OAuth 2.0 / OpenID Connect
- JWT tokens
- Session cookies

Add authentication headers to requests:

```http
Authorization: Bearer <access_token>
```
