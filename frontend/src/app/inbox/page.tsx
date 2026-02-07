"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  MessageCircle,
  AtSign,
  CheckCheck,
  RefreshCw,
  Inbox as InboxIcon,
  ExternalLink,
} from "lucide-react";
import toast from "react-hot-toast";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { inboxApi, InboxItem } from "@/lib/api";
import { formatRelativeTime, cn } from "@/lib/utils";

type FilterType = "all" | "unread" | "comment" | "mention";

export default function InboxPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<FilterType>("all");
  const [platformFilter, setPlatformFilter] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["inbox", filter, platformFilter],
    queryFn: () =>
      inboxApi
        .get({
          unread_only: filter === "unread",
          platform: platformFilter || undefined,
        })
        .then((res) => res.data),
  });

  const syncMutation = useMutation({
    mutationFn: () => inboxApi.sync(platformFilter || undefined),
    onSuccess: () => {
      toast.success("Inbox synced");
      refetch();
    },
    onError: () => {
      toast.error("Failed to sync");
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => inboxApi.markAllRead(platformFilter || undefined),
    onSuccess: () => {
      toast.success("All marked as read");
      queryClient.invalidateQueries({ queryKey: ["inbox"] });
    },
  });

  const items = data?.items || [];
  const filteredItems =
    filter === "comment"
      ? items.filter((i) => i.type === "comment")
      : filter === "mention"
      ? items.filter((i) => i.type === "mention")
      : items;

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl gradient-gold shadow-lg shadow-amber-500/25">
              <InboxIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Inbox</h1>
              <p className="text-gray-500 mt-1">
                {data?.unread_count || 0} unread notification
                {data?.unread_count !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => syncMutation.mutate()}
              loading={syncMutation.isPending}
            >
              <RefreshCw className="w-4 h-4" />
              Sync
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => markAllReadMutation.mutate()}
              disabled={data?.unread_count === 0}
            >
              <CheckCheck className="w-4 h-4" />
              Mark All Read
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1.5">
            {(["all", "unread", "comment", "mention"] as FilterType[]).map(
              (f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "px-4 py-2 text-sm font-medium rounded-lg transition-all capitalize",
                    filter === f
                      ? "bg-white text-gray-900 shadow-md"
                      : "text-gray-600 hover:text-gray-900 hover:bg-white/50"
                  )}
                >
                  {f === "all" ? "All" : f}
                </button>
              )
            )}
          </div>

          <select
            value={platformFilter || ""}
            onChange={(e) => setPlatformFilter(e.target.value || null)}
            className="px-4 py-2.5 text-sm font-medium border-2 border-gray-200 rounded-xl bg-white focus:outline-none focus:border-amber-500 focus:ring-4 focus:ring-amber-500/10 transition-all cursor-pointer"
          >
            <option value="">All Platforms</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="bluesky">Bluesky</option>
            <option value="tiktok">TikTok</option>
            <option value="threads">Threads</option>
          </select>
        </div>

        {/* Items List */}
        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="py-16 flex items-center justify-center">
                <div className="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : filteredItems.length === 0 ? (
              <div className="py-16 text-center">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                  <MessageCircle className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-900 font-semibold text-lg">No items found</p>
                <p className="text-sm text-gray-500 mt-1">
                  {filter === "unread"
                    ? "You're all caught up!"
                    : "Activity will appear here"}
                </p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {filteredItems.map((item) => (
                  <InboxListItem key={item.id} item={item} />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        {data?.has_next && (
          <div className="flex justify-center">
            <Button variant="outline" size="lg">
              Load More
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

function InboxListItem({ item }: { item: InboxItem }) {
  const queryClient = useQueryClient();
  const isComment = item.type === "comment";

  const markReadMutation = useMutation({
    mutationFn: () =>
      inboxApi.markRead(isComment ? "comment" : "mention", item.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inbox"] });
    },
  });

  const handleReply = (e: React.MouseEvent) => {
    e.stopPropagation();
    toast("Reply feature coming soon!", {
      icon: "💬",
      duration: 3000,
    });
  };

  return (
    <li
      className={cn(
        "p-5 hover:bg-gray-50/50 transition-colors cursor-pointer",
        !item.is_read && "bg-amber-50/30"
      )}
      onClick={() => !item.is_read && markReadMutation.mutate()}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex-shrink-0 flex items-center justify-center overflow-hidden shadow-inner">
          {item.author_avatar_url ? (
            <img
              src={item.author_avatar_url}
              alt={item.author_username}
              className="w-full h-full object-cover"
            />
          ) : isComment ? (
            <MessageCircle className="w-5 h-5 text-gray-500" />
          ) : (
            <AtSign className="w-5 h-5 text-gray-500" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-gray-900">
              @{item.author_username}
            </span>
            <span className="text-gray-500">
              {isComment ? "commented" : "mentioned you"}
            </span>
            <PlatformBadge platform={item.platform} size="sm" />
            <span className="text-sm text-gray-400">
              {formatRelativeTime(item.timestamp)}
            </span>
          </div>

          <p className="text-gray-700 mt-2 leading-relaxed">{item.content || "No content"}</p>

          <div className="flex items-center gap-4 mt-3">
            {isComment && item.likes_count !== null && item.likes_count > 0 && (
              <span className="text-sm text-gray-500">
                {item.likes_count} like{item.likes_count > 1 ? "s" : ""}
              </span>
            )}
            {item.post_url && (
              <a
                href={item.post_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-amber-600 hover:text-amber-700 font-medium flex items-center gap-1 transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                View on {item.platform}
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
            {isComment && (
              <button
                onClick={handleReply}
                className="text-sm text-amber-600 hover:text-amber-700 font-semibold transition-colors"
              >
                Reply
              </button>
            )}
          </div>
        </div>

        {/* Status indicator */}
        {!item.is_read && (
          <div className="w-3 h-3 rounded-full gradient-primary flex-shrink-0 mt-1 shadow-lg shadow-amber-500/50" />
        )}
      </div>
    </li>
  );
}
