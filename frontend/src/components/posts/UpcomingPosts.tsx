"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Calendar, Clock, Edit2, X, Check, Trash2, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { postsApi, Post, PlatformScheduleSuggestion, ScheduleTimeSlot } from "@/lib/api";
import { formatDate, formatTime, truncateText } from "@/lib/utils";

export function UpcomingPosts() {
  const { data, isLoading } = useQuery({
    queryKey: ["posts", "scheduled"],
    queryFn: () =>
      postsApi.list({ status: "scheduled", per_page: 10 }).then((res) => res.data),
  });

  const posts = data?.posts || [];

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <LoadingSpinner size="md" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (posts.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState
            icon={Calendar}
            title="No scheduled posts"
            description="Schedule content to see it here"
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        <ul className="divide-y divide-surface-100">
          {posts.map((post) => (
            <PostItem key={post.id} post={post} />
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function PostItem({ post }: { post: Post }) {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editContent, setEditContent] = useState(post.content);
  const [editDate, setEditDate] = useState(() => {
    if (post.scheduled_at) {
      const date = new Date(post.scheduled_at);
      return date.toISOString().split("T")[0];
    }
    return "";
  });
  const [editTime, setEditTime] = useState(() => {
    if (post.scheduled_at) {
      const date = new Date(post.scheduled_at);
      return date.toTimeString().slice(0, 5);
    }
    return "";
  });

  // Memoize platform names to prevent unnecessary re-renders and API calls
  const platformNames = useMemo(
    () => post.platforms.map((p) => p.platform),
    [post.platforms]
  );

  // Fetch AI suggestions when editing
  const { data: suggestionsData } = useQuery({
    queryKey: ["schedule-suggestions", platformNames],
    queryFn: () =>
      postsApi.getScheduleSuggestions(platformNames).then((res) => res.data),
    enabled: isEditing && platformNames.length > 0,
    staleTime: 5 * 60 * 1000,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { content?: string; scheduled_at?: string }) =>
      postsApi.update(post.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["posts"] });
      setIsEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => postsApi.delete(post.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
  });

  const handleSave = () => {
    const scheduled_at =
      editDate && editTime ? `${editDate}T${editTime}:00` : undefined;
    updateMutation.mutate({
      content: editContent,
      scheduled_at,
    });
  };

  const handleCancel = () => {
    setEditContent(post.content);
    if (post.scheduled_at) {
      const date = new Date(post.scheduled_at);
      setEditDate(date.toISOString().split("T")[0]);
      setEditTime(date.toTimeString().slice(0, 5));
    }
    setIsEditing(false);
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = () => {
    deleteMutation.mutate(undefined, {
      onSuccess: () => {
        setShowDeleteConfirm(false);
      },
    });
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  // Get unique suggested times
  const suggestedTimes = (() => {
    if (!suggestionsData?.suggestions) return [];
    const times: Array<{ datetime: string; score: number; reason: string }> = [];
    const seen = new Set<string>();

    Object.values(suggestionsData.suggestions).forEach((suggestion: PlatformScheduleSuggestion) => {
      if (suggestion.best_time && !seen.has(suggestion.best_time.datetime)) {
        seen.add(suggestion.best_time.datetime);
        times.push(suggestion.best_time);
      }
      suggestion.alternative_times?.forEach((alt: ScheduleTimeSlot) => {
        if (!seen.has(alt.datetime)) {
          seen.add(alt.datetime);
          times.push(alt);
        }
      });
    });

    return times.sort((a, b) => b.score - a.score).slice(0, 6);
  })();

  const applyTime = (datetime: string) => {
    const date = new Date(datetime);
    setEditDate(date.toISOString().split("T")[0]);
    setEditTime(date.toTimeString().slice(0, 5));
  };

  const formatSuggestedTime = (datetime: string) => {
    const date = new Date(datetime);
    const day = date.toLocaleDateString("en-US", { weekday: "short" });
    const time = date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    return `${day} ${time}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "bg-green-100 text-green-700 hover:bg-green-200";
    if (score >= 60) return "bg-yellow-100 text-yellow-700 hover:bg-yellow-200";
    return "bg-surface-100 text-surface-600 hover:bg-surface-200";
  };

  if (isEditing) {
    return (
      <li className="p-4 bg-surface-50">
        <div className="space-y-3">
          {/* Caption editor */}
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full p-3 border border-surface-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            rows={3}
            placeholder="Post content..."
          />

          {/* Date and time pickers */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-surface-400" />
              <input
                type="date"
                value={editDate}
                onChange={(e) => setEditDate(e.target.value)}
                className="px-3 py-1.5 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-surface-400" />
              <input
                type="time"
                value={editTime}
                onChange={(e) => setEditTime(e.target.value)}
                className="px-3 py-1.5 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* AI Suggested Times */}
          {suggestedTimes.length > 0 && (
            <div className="bg-gradient-to-r from-primary-50 to-accent-50 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-primary-500" />
                <span className="text-xs font-medium text-primary-700">
                  AI Suggested Times
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {suggestedTimes.map((time, idx) => (
                  <button
                    key={idx}
                    onClick={() => applyTime(time.datetime)}
                    className={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${getScoreColor(
                      time.score
                    )}`}
                    title={time.reason}
                  >
                    {formatSuggestedTime(time.datetime)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Platforms display */}
          <div className="flex items-center gap-1">
            {post.platforms.map((pp) => (
              <PlatformBadge key={pp.id} platform={pp.platform} size="sm" />
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-2 border-t border-surface-200">
            <button
              onClick={handleDeleteClick}
              disabled={deleteMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>

            <ConfirmDialog
              isOpen={showDeleteConfirm}
              onClose={handleDeleteCancel}
              onConfirm={handleDeleteConfirm}
              title="Delete Scheduled Post"
              description="Are you sure you want to delete this scheduled post? This action cannot be undone."
              confirmLabel="Delete"
              cancelLabel="Cancel"
              variant="danger"
              isLoading={deleteMutation.isPending}
            />
            <div className="flex items-center gap-2">
              <button
                onClick={handleCancel}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-surface-600 hover:bg-surface-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary-500 text-white hover:bg-primary-600 rounded-lg transition-colors disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                {updateMutation.isPending ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      </li>
    );
  }

  return (
    <li className="p-4 hover:bg-surface-50 transition-colors group">
      <div className="flex items-start gap-3">
        {/* Thumbnail or placeholder */}
        <div className="w-12 h-12 rounded-lg bg-surface-100 flex-shrink-0 flex items-center justify-center overflow-hidden">
          {post.thumbnail_url || (post.media_urls && post.media_urls[0]) ? (
            <img
              src={post.thumbnail_url || post.media_urls?.[0]}
              alt=""
              className="w-full h-full object-cover"
            />
          ) : (
            <Calendar className="w-5 h-5 text-surface-400" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-surface-900 line-clamp-2">
            {truncateText(post.content, 100)}
          </p>

          <div className="flex items-center gap-3 mt-2">
            {/* Platforms */}
            <div className="flex items-center gap-1">
              {post.platforms.map((pp) => (
                <PlatformBadge
                  key={pp.id}
                  platform={pp.platform}
                  size="sm"
                />
              ))}
            </div>

            {/* Scheduled time */}
            {post.scheduled_at && (
              <div className="flex items-center gap-1 text-xs text-surface-500">
                <Clock className="w-3 h-3" />
                <span>
                  {formatDate(post.scheduled_at)} at{" "}
                  {formatTime(post.scheduled_at)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Edit button */}
        <button
          onClick={() => setIsEditing(true)}
          className="p-2 text-surface-400 hover:text-primary-500 hover:bg-surface-100 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          title="Edit post"
        >
          <Edit2 className="w-4 h-4" />
        </button>
      </div>
    </li>
  );
}
