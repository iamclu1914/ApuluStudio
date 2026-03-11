"use client";

import { useQuery } from "@tanstack/react-query";
import { Heart, MessageCircle, Users, Repeat2, CheckCircle, ExternalLink } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { inboxApi, InboxItem } from "@/lib/api";
import { formatRelativeTime, truncateText, cn } from "@/lib/utils";

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  tiktok: "#FF0050",
  x: "#1D9BF0",
  threads: "#000000",
  bluesky: "#0085FF",
};

const TYPE_ICONS: Record<string, React.ElementType> = {
  like: Heart,
  comment: MessageCircle,
  follow: Users,
  repost: Repeat2,
  published: CheckCircle,
};

function ActivityItem({ item }: { item: InboxItem }) {
  const Icon = TYPE_ICONS[item.type] ?? MessageCircle;
  const platformColor = PLATFORM_COLORS[item.platform?.toLowerCase()] ?? "#7C3AED";

  return (
    <li
      className={cn(
        "px-4 py-3 hover:bg-surface-50 dark:hover:bg-dark-border/50 transition-colors relative"
      )}
    >
      {!item.is_read && (
        <span
          className="absolute left-0 top-0 bottom-0 w-0.5 rounded-full"
          style={{ backgroundColor: platformColor }}
        />
      )}
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center"
          style={{ backgroundColor: `${platformColor}20` }}
        >
          <Icon className="w-4 h-4" style={{ color: platformColor }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            {item.author_username && (
              <span className="text-sm font-medium text-surface-900 dark:text-surface-100">
                @{item.author_username}
              </span>
            )}
            {/* Platform dot */}
            <span
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: platformColor }}
            />
            <span className="text-xs text-surface-400 dark:text-surface-500">
              {formatRelativeTime(item.timestamp)}
            </span>
          </div>

          <p className="text-xs text-surface-500 dark:text-surface-400 mt-0.5">
            {item.type === "comment" && item.content
              ? `"${truncateText(item.content, 60)}"`
              : item.type === "like"
              ? "liked your post"
              : item.type === "follow"
              ? "followed you"
              : item.type === "repost"
              ? "reposted your content"
              : item.type === "published"
              ? "Post published successfully"
              : item.content
              ? truncateText(item.content, 60)
              : ""}
          </p>

          {item.post_url && (
            <a
              href={item.post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary-500 hover:text-primary-600 flex items-center gap-0.5 mt-1 w-fit"
            >
              View post <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

export function RecentActivityV2() {
  const { data, isLoading, isError, dataUpdatedAt } = useQuery({
    queryKey: ["inbox", "recent"],
    queryFn: () => inboxApi.get({ per_page: 10 }).then((r) => r.data),
    refetchInterval: 60_000,
  });

  const items = data?.items ?? [];
  const lastUpdatedStr = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <Card>
      <CardContent className="p-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-surface-100 dark:border-dark-border">
          <h3 className="text-sm font-semibold text-surface-900 dark:text-surface-100">
            Recent Activity
          </h3>
          <div className="flex items-center gap-3">
            {isError && lastUpdatedStr && (
              <span className="text-xs text-amber-500">
                Last updated {lastUpdatedStr}
              </span>
            )}
            {!isError && lastUpdatedStr && (
              <span className="text-xs text-surface-400 dark:text-surface-500">
                Updated {lastUpdatedStr}
              </span>
            )}
            <Link
              href="/inbox"
              className="text-xs font-medium text-primary-500 hover:text-primary-600"
            >
              View all →
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-8">
            <MessageCircle className="w-10 h-10 mx-auto text-surface-300 mb-2" />
            <p className="text-sm text-surface-500 dark:text-surface-400">No recent activity</p>
          </div>
        ) : (
          <ul className="divide-y divide-surface-100 dark:divide-dark-border">
            {items.map((item) => (
              <ActivityItem key={item.id} item={item} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
