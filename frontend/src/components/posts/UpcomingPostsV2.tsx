"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Calendar as CalendarIcon, List, Clock, Trash2, Edit2, ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { Card, CardContent } from "@/components/ui/Card";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { postsApi, Post } from "@/lib/api";
import { useUIStore } from "@/store/ui";
import { formatTime, truncateText, cn } from "@/lib/utils";

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  tiktok: "#FF0050",
  x: "#1D9BF0",
  threads: "#000000",
  bluesky: "#0085FF",
};

// ------- Calendar View -------

function CalendarView({ posts }: { posts: Post[] }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const postsByDay: Record<number, Post[]> = {};
  posts.forEach((p) => {
    if (!p.scheduled_at) return;
    const d = new Date(p.scheduled_at);
    if (d.getFullYear() === year && d.getMonth() === month) {
      const day = d.getDate();
      if (!postsByDay[day]) postsByDay[day] = [];
      postsByDay[day].push(p);
    }
  });

  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);

  const selectedPosts = selectedDay ? (postsByDay[selectedDay] ?? []) : [];
  const today = new Date();

  return (
    <div>
      {/* Month nav */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => setCurrentDate(new Date(year, month - 1, 1))}
          className="p-1 rounded hover:bg-surface-100 dark:hover:bg-dark-border"
        >
          <ChevronLeft className="w-4 h-4 text-surface-500" />
        </button>
        <span className="text-sm font-semibold text-surface-800 dark:text-surface-200">
          {currentDate.toLocaleString("default", { month: "long", year: "numeric" })}
        </span>
        <button
          onClick={() => setCurrentDate(new Date(year, month + 1, 1))}
          className="p-1 rounded hover:bg-surface-100 dark:hover:bg-dark-border"
        >
          <ChevronRight className="w-4 h-4 text-surface-500" />
        </button>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 mb-1">
        {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
          <div key={i} className="text-center text-xs text-surface-400 font-medium py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7 gap-0.5">
        {days.map((day, i) => (
          <button
            key={i}
            onClick={() => day && setSelectedDay(day === selectedDay ? null : day)}
            disabled={!day}
            className={cn(
              "aspect-square flex flex-col items-center justify-start pt-1 rounded-lg text-xs transition-colors",
              !day && "invisible",
              day && "hover:bg-surface-100 dark:hover:bg-dark-border",
              day === selectedDay && "bg-primary-50 dark:bg-primary-900/20 ring-1 ring-primary-500"
            )}
          >
            <span
              className={cn(
                "font-medium",
                day === today.getDate() &&
                  month === today.getMonth() &&
                  year === today.getFullYear()
                  ? "text-primary-500"
                  : "text-surface-700 dark:text-surface-300"
              )}
            >
              {day}
            </span>
            {day && postsByDay[day] && (
              <div className="flex gap-0.5 mt-0.5 flex-wrap justify-center">
                {postsByDay[day].slice(0, 3).map((p, pi) => {
                  const color =
                    PLATFORM_COLORS[p.platforms[0]?.platform?.toLowerCase()] ?? "#7C3AED";
                  return (
                    <span
                      key={pi}
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  );
                })}
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Selected day posts */}
      {selectedDay && selectedPosts.length > 0 && (
        <div className="mt-3 space-y-2 border-t border-surface-100 dark:border-dark-border pt-3">
          <p className="text-xs font-medium text-surface-500 dark:text-surface-400">
            {selectedDay}{" "}
            {currentDate.toLocaleString("default", { month: "long" })}
          </p>
          {selectedPosts.map((p) => (
            <div
              key={p.id}
              className="flex items-start gap-2 text-xs text-surface-600 dark:text-surface-400"
            >
              <Clock className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>{p.scheduled_at ? formatTime(p.scheduled_at) : ""}</span>
              <span className="truncate">{truncateText(p.content, 60)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ------- Queue View -------

function QueueView({
  posts,
  onEdit,
  onDelete,
  onCancelDelete,
  deleteConfirmId,
}: {
  posts: Post[];
  onEdit: (post: Post) => void;
  onDelete: (id: string) => void;
  onCancelDelete: () => void;
  deleteConfirmId: string | null;
}) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-8">
        <CalendarIcon className="w-10 h-10 mx-auto text-surface-300 mb-2" />
        <p className="text-sm text-surface-500 dark:text-surface-400">No scheduled posts</p>
        <p className="text-xs text-surface-400 dark:text-surface-500 mt-1">
          Use the compose area above to schedule content
        </p>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-surface-100 dark:divide-dark-border">
      {posts.map((post) => (
        <li key={post.id} className="py-3 flex items-start gap-3 group">
          {/* Thumbnail */}
          <div className="w-12 h-12 rounded-lg bg-surface-100 dark:bg-dark-border flex-shrink-0 overflow-hidden">
            {post.thumbnail_url || post.media_urls?.[0] ? (
              <img
                src={post.thumbnail_url ?? post.media_urls![0]}
                alt=""
                className="w-full h-full object-cover object-top"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <CalendarIcon className="w-5 h-5 text-surface-300" />
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p className="text-sm text-surface-900 dark:text-surface-100 line-clamp-2">
              {truncateText(post.content, 80)}
            </p>
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <div className="flex gap-1">
                {post.platforms.map((pp) => (
                  <PlatformBadge key={pp.id} platform={pp.platform} size="sm" />
                ))}
              </div>
              {post.scheduled_at && (
                <span className="text-xs text-surface-400 dark:text-surface-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(post.scheduled_at).toLocaleDateString()}{" "}
                  {formatTime(post.scheduled_at)}
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity relative">
            <button
              onClick={() => onEdit(post)}
              className="p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-dark-border text-surface-400 hover:text-surface-600 dark:hover:text-surface-300"
            >
              <Edit2 className="w-3.5 h-3.5" />
            </button>

            <div className="relative">
              <button
                onClick={() => onDelete(post.id)}
                className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-surface-400 hover:text-red-500"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
              {/* Confirmation popover */}
              {post.id === deleteConfirmId && (
                <div className="absolute right-0 top-8 z-10 bg-white dark:bg-dark-surface border border-red-200 dark:border-red-800 rounded-lg shadow-lg p-3 w-40 text-center">
                  <p className="text-xs text-surface-700 dark:text-surface-300 mb-2">
                    Delete this post?
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => onDelete(post.id)}
                      className="flex-1 px-2 py-1 text-xs bg-red-500 text-white rounded-md hover:bg-red-600"
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => onCancelDelete()}
                      className="flex-1 px-2 py-1 text-xs border border-surface-200 dark:border-dark-border rounded-md hover:bg-surface-100 dark:hover:bg-dark-border"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

// ------- Main Component -------

export function UpcomingPostsV2({ onEditPost }: { onEditPost?: (post: Post) => void }) {
  const queryClient = useQueryClient();
  const view = useUIStore((s) => s.upcomingView);
  const setView = useUIStore((s) => s.setUpcomingView);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["posts", "scheduled"],
    queryFn: () =>
      postsApi.list({ status: "scheduled", per_page: 20 }).then((r) => r.data),
  });

  const deletePost = useMutation({
    mutationFn: (id: string) => postsApi.delete(id),
    onSuccess: () => {
      toast.success("Post deleted");
      setDeleteConfirm(null);
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: () => toast.error("Failed to delete post"),
  });

  const posts = data?.posts ?? [];

  return (
    <Card>
      <CardContent className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-surface-900 dark:text-surface-100">
            Upcoming Posts
          </h3>
          <div className="flex items-center gap-1 bg-surface-100 dark:bg-dark-border rounded-lg p-0.5">
            <button
              onClick={() => setView("calendar")}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors",
                view === "calendar"
                  ? "bg-white dark:bg-dark-surface text-surface-900 dark:text-surface-100 shadow-sm"
                  : "text-surface-400 hover:text-surface-600 dark:hover:text-surface-300"
              )}
            >
              <CalendarIcon className="w-3.5 h-3.5" /> Calendar
            </button>
            <button
              onClick={() => setView("queue")}
              className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors",
                view === "queue"
                  ? "bg-white dark:bg-dark-surface text-surface-900 dark:text-surface-100 shadow-sm"
                  : "text-surface-400 hover:text-surface-600 dark:hover:text-surface-300"
              )}
            >
              <List className="w-3.5 h-3.5" /> Queue
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : view === "calendar" ? (
          <CalendarView posts={posts} />
        ) : (
          <QueueView
            posts={posts}
            onEdit={(post) => onEditPost?.(post)}
            onDelete={(id) => {
              if (deleteConfirm === id) {
                deletePost.mutate(id);
              } else {
                setDeleteConfirm(id);
              }
            }}
            onCancelDelete={() => setDeleteConfirm(null)}
            deleteConfirmId={deleteConfirm}
          />
        )}
      </CardContent>
    </Card>
  );
}
