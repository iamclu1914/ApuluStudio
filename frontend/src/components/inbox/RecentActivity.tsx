"use client";

import { useQuery } from "@tanstack/react-query";
import { MessageCircle, AtSign, ExternalLink } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { inboxApi, InboxItem } from "@/lib/api";
import { formatRelativeTime, truncateText, cn } from "@/lib/utils";

export function RecentActivity() {
  const { data, isLoading } = useQuery({
    queryKey: ["inbox", "recent"],
    queryFn: () => inboxApi.get({ per_page: 5 }).then((res) => res.data),
  });

  const items = data?.items || [];
  const unreadCount = data?.unread_count || 0;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center">
            <MessageCircle className="w-10 h-10 mx-auto text-surface-300 mb-2" />
            <p className="text-surface-500">No recent activity</p>
            <p className="text-sm text-surface-400 mt-1">
              Comments and mentions will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-0">
        {unreadCount > 0 && (
          <div className="px-4 py-2 bg-primary-50 border-b border-primary-100">
            <p className="text-sm font-medium text-primary-700">
              {unreadCount} unread notification{unreadCount > 1 ? "s" : ""}
            </p>
          </div>
        )}
        <ul className="divide-y divide-surface-100">
          {items.map((item) => (
            <ActivityItem key={item.id} item={item} />
          ))}
        </ul>
        <Link
          href="/inbox"
          className="block px-4 py-3 text-center text-sm font-medium text-primary-600 hover:bg-surface-50 transition-colors"
        >
          View all activity
        </Link>
      </CardContent>
    </Card>
  );
}

function ActivityItem({ item }: { item: InboxItem }) {
  const isComment = item.type === "comment";

  return (
    <li
      className={cn(
        "p-4 hover:bg-surface-50 transition-colors",
        !item.is_read && "bg-primary-50/30"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Avatar or Icon */}
        <div className="w-10 h-10 rounded-full bg-surface-100 flex-shrink-0 flex items-center justify-center overflow-hidden">
          {item.author_avatar_url ? (
            <img
              src={item.author_avatar_url}
              alt={item.author_username}
              className="w-full h-full object-cover"
            />
          ) : isComment ? (
            <MessageCircle className="w-4 h-4 text-surface-400" />
          ) : (
            <AtSign className="w-4 h-4 text-surface-400" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-surface-900 truncate max-w-[150px] sm:max-w-none">
              @{item.author_username}
            </span>
            <PlatformBadge platform={item.platform} size="sm" />
            <span className="text-xs text-surface-400">
              {formatRelativeTime(item.timestamp)}
            </span>
          </div>

          <p className="text-sm text-surface-600 mt-1">
            {isComment ? "commented: " : "mentioned you: "}
            {item.content ? truncateText(item.content, 80) : "No content"}
          </p>

          <div className="flex items-center gap-3 mt-2">
            {isComment && item.likes_count !== null && item.likes_count > 0 && (
              <span className="text-xs text-surface-500">
                {item.likes_count} like{item.likes_count > 1 ? "s" : ""}
              </span>
            )}
            {item.post_url && (
              <a
                href={item.post_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
              >
                View <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      </div>
    </li>
  );
}
