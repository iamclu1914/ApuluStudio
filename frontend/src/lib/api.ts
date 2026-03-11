import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types
export interface Platform {
  platform: string;
  connected: boolean;
  account: SocialAccount | null;
  requires_reconnect: boolean;
}

export interface SocialAccount {
  id: string;
  platform: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  follower_count: number;
  following_count: number;
  is_active: boolean;
  last_synced: string | null;
  created_at: string;
}

export interface Post {
  id: string;
  content: string;
  post_type: string;
  media_urls: string[] | null;
  thumbnail_url: string | null;
  hashtags: string[] | null;
  status: string;
  scheduled_at: string | null;
  published_at: string | null;
  ai_generated: boolean;
  created_at: string;
  updated_at: string;
  platforms: PostPlatform[];
}

export interface PostPlatform {
  id: string;
  platform: string;
  username: string;
  status: string;
  content: string | null;
  platform_post_url: string | null;
  likes_count: number;
  comments_count: number;
  shares_count: number;
  published_at: string | null;
  error_message: string | null;
}

export interface InboxItem {
  id: string;
  type: string;
  platform: string;
  content: string | null;
  author_username: string;
  author_avatar_url: string | null;
  is_read: boolean;
  timestamp: string;
  post_url: string | null;
  is_replied: boolean | null;
  likes_count: number | null;
}

export interface OverviewStats {
  // Existing fields
  total_followers: number;
  total_engagement: number;
  posts_this_week: number;
  engagement_rate: number;
  platforms: PlatformStats[];
  // New fields
  reach?: number;
  impressions?: number;
  followers_change_pct?: number;
  reach_change_pct?: number;
  impressions_change_pct?: number;
  engagement_change_pct?: number;
  followers_sparkline?: number[];
  reach_sparkline?: number[];
  impressions_sparkline?: number[];
  engagement_sparkline?: number[];
  platform_breakdown?: {
    platform: string;
    followers: number;
  }[];
}

export interface PlatformStats {
  platform: string;
  followers: number;
  following: number;
  posts_count: number;
  engagement_rate: number;
}

export interface CaptionVariation {
  tone: string;
  caption: string;
  hashtags: string[];
  character_count: number;
}

export interface CaptionResponse {
  topic: string;
  variations: CaptionVariation[];
  generated_at: string;
}

// API functions
export const postsApi = {
  list: (params?: { status?: string; page?: number; per_page?: number }) =>
    api.get<{ posts: Post[]; total: number; page: number; has_next: boolean }>(
      "/posts",
      { params }
    ),

  get: (id: string) => api.get<Post>(`/posts/${id}`),

  create: (data: {
    content: string;
    platforms: string[];
    scheduled_at?: string;
    media_urls?: string[];
    hashtags?: string[];
    ai_generated?: boolean;
  }) => api.post<Post>("/posts", data),

  update: (id: string, data: Partial<Post>) =>
    api.patch<Post>(`/posts/${id}`, data),

  delete: (id: string) => api.delete(`/posts/${id}`),

  publish: (id: string) => api.post(`/posts/${id}/publish`),

  getCalendar: (start: string, end: string) =>
    api.get<Post[]>("/posts/calendar", { params: { start_date: start, end_date: end } }),

  getSmartSlots: (platform: string) =>
    api.get(`/posts/smart-slots/${platform}`),

  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<{ url: string; filename: string; content_type: string; size: number }>(
      "/posts/upload",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },
};

export const accountsApi = {
  list: () => api.get<SocialAccount[]>("/accounts"),

  getStatus: () => api.get<Platform[]>("/accounts/status"),

  connect: (platform: string) => api.get(`/accounts/connect/${platform}`),

  connectBluesky: (handle: string, appPassword: string) =>
    api.post("/accounts/connect/bluesky", null, {
      params: { handle, app_password: appPassword },
    }),

  disconnect: (id: string) => api.delete(`/accounts/${id}`),

  sync: (id: string) => api.post(`/accounts/${id}/sync`),

  syncLate: () => api.post<{ success: boolean; synced: any[]; message: string }>("/accounts/sync/late"),
};

export const inboxApi = {
  get: (params?: { platform?: string; unread_only?: boolean; page?: number; per_page?: number }) =>
    api.get<{
      items: InboxItem[];
      total: number;
      unread_count: number;
      page: number;
      has_next: boolean;
    }>("/inbox", { params }),

  markRead: (type: "comment" | "mention", id: string) =>
    api.post(`/inbox/${type}s/${id}/read`),

  reply: (commentId: string, content: string) =>
    api.post(`/inbox/comments/${commentId}/reply`, { content }),

  markAllRead: (platform?: string) =>
    api.post("/inbox/read-all", null, { params: { platform } }),

  sync: (platform?: string) =>
    api.post("/inbox/sync", null, { params: { platform } }),
};

export const analyticsApi = {
  getOverview: (range: "7d" | "30d" | "90d" = "7d") =>
    api.get<OverviewStats>("/analytics/overview", { params: { range } }),

  getGrowth: (platform?: string, days?: number) =>
    api.get("/analytics/growth", { params: { platform, days } }),

  getTopPosts: (days?: number, limit?: number) =>
    api.get("/analytics/top-posts", { params: { days, limit } }),

  getWeeklyReport: () => api.get("/analytics/weekly-report"),
};

export const aiApi = {
  generateCaption: (data: {
    topic: string;
    url?: string;
    tone?: string;
    platform?: string;
    include_hashtags?: boolean;
  }) => api.post<CaptionResponse>("/ai/generate-caption", data),

  generateHashtags: (content: string, platform?: string, count?: number) =>
    api.post<{ hashtags: string[] }>("/ai/generate-hashtags", null, {
      params: { content, platform, count },
    }),

  optimizeContent: (content: string, targetPlatform: string) =>
    api.post("/ai/optimize-content", null, {
      params: { content, target_platform: targetPlatform },
    }),

  getCharacterLimits: () => api.get("/ai/character-limits"),
};
