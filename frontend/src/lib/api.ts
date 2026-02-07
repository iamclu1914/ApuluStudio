import axios from "axios";

const LOCAL_API_HOSTS = new Set(["localhost", "127.0.0.1"]);
const DEFAULT_API_URL = "http://localhost:8000/api";

function resolveApiUrl() {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL;

  if (typeof window === "undefined") {
    return configuredUrl || DEFAULT_API_URL;
  }

  const browserHost = window.location.hostname;

  if (!configuredUrl) {
    return `http://${browserHost}:8000/api`;
  }

  try {
    const parsed = new URL(configuredUrl);

    if (LOCAL_API_HOSTS.has(parsed.hostname) && !LOCAL_API_HOSTS.has(browserHost)) {
      parsed.hostname = browserHost;
      return parsed.toString();
    }
  } catch {
    // Keep configuredUrl as-is when it's not a fully qualified URL.
  }

  return configuredUrl;
}

const API_URL = resolveApiUrl();

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
  total_followers: number;
  total_engagement: number;
  posts_this_week: number;
  engagement_rate: number;
  platforms: PlatformStats[];
}

export interface PlatformStats {
  platform: string;
  followers: number;
  following: number;
  posts_count: number;
  engagement_rate: number;
}

export interface GrowthDataPoint {
  date: string;
  followers: number;
  engagement: number;
}

export interface GrowthData {
  data_points: GrowthDataPoint[];
  percent_change: number;
}

export interface TopPost {
  id: string;
  content: string;
  platform: string;
  thumbnail_url: string | null;
  published_at: string;
  likes_count: number;
  comments_count: number;
  shares_count: number;
}

export interface ScheduleTimeSlot {
  datetime: string;
  engagement_level: string;
  score: number;
  reason: string;
}

export interface PlatformScheduleSuggestion {
  platform: string;
  best_time: ScheduleTimeSlot;
  alternative_times: ScheduleTimeSlot[];
  insights: string[];
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

  getScheduleSuggestions: (platforms: string[]) =>
    api.get<{
      suggestions: Record<string, PlatformScheduleSuggestion>;
      generated_at: string;
    }>("/posts/schedule/suggestions", { params: { platforms: platforms.join(",") } }),

  getOptimalTime: (platforms: string[]) =>
    api.get<{
      optimal_time: {
        datetime: string;
        engagement_level: string;
        score: number;
        reason: string;
        platforms: string[];
      };
      generated_at: string;
    }>("/posts/schedule/optimal-time", { params: { platforms: platforms.join(",") } }),

  upload: (file: File, platforms?: string[]) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<{ url: string; filename: string; content_type: string; size: number }>(
      "/posts/upload",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        params: platforms && platforms.length > 0 ? { platforms: platforms.join(",") } : undefined,
      }
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

  syncLate: () => api.post<{ success: boolean; synced: SocialAccount[]; message: string }>("/accounts/sync/late"),
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
  getOverview: () => api.get<OverviewStats>("/analytics/overview"),

  getGrowth: (platform?: string, days?: number) =>
    api.get<GrowthData>("/analytics/growth", { params: { platform, days } }),

  getTopPosts: (days?: number, limit?: number) =>
    api.get<TopPost[]>("/analytics/top-posts", { params: { days, limit } }),
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
};
