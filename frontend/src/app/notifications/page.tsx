"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  Check,
  CheckCheck,
  MessageCircle,
  Heart,
  UserPlus,
  Share2,
  Filter,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { formatRelativeTime, cn } from "@/lib/utils";

// Mock notifications data - replace with real API
const mockNotifications = [
  {
    id: "1",
    type: "comment",
    platform: "instagram",
    title: "New comment on your post",
    message: "@musicfan123 commented: \"This track is fire! Can't stop listening\"",
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    read: false,
  },
  {
    id: "2",
    type: "like",
    platform: "tiktok",
    title: "Your video is trending",
    message: "Your latest video received 1,234 new likes",
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    read: false,
  },
  {
    id: "3",
    type: "follower",
    platform: "x",
    title: "New followers",
    message: "You gained 45 new followers today",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    read: true,
  },
  {
    id: "4",
    type: "share",
    platform: "threads",
    title: "Your post was shared",
    message: "@influencer shared your post with their 50K followers",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    read: true,
  },
];

const notificationIcons = {
  comment: MessageCircle,
  like: Heart,
  follower: UserPlus,
  share: Share2,
};

export default function NotificationsPage() {
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const [notifications, setNotifications] = useState(mockNotifications);

  const unreadCount = notifications.filter((n) => !n.read).length;
  const filteredNotifications =
    filter === "unread" ? notifications.filter((n) => !n.read) : notifications;

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl gradient-primary shadow-lg shadow-amber-500/25">
              <Bell className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
              <p className="text-gray-500 mt-1">
                {unreadCount > 0
                  ? `${unreadCount} unread notification${unreadCount > 1 ? "s" : ""}`
                  : "You're all caught up!"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={markAllAsRead}
              disabled={unreadCount === 0}
            >
              <CheckCheck className="w-4 h-4" />
              Mark all read
            </Button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilter("all")}
            className={cn(
              "px-4 py-2 rounded-xl text-sm font-medium transition-all",
              filter === "all"
                ? "bg-amber-100 text-amber-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            )}
          >
            All
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={cn(
              "px-4 py-2 rounded-xl text-sm font-medium transition-all",
              filter === "unread"
                ? "bg-amber-100 text-amber-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            )}
          >
            Unread {unreadCount > 0 && `(${unreadCount})`}
          </button>
        </div>

        {/* Notifications List */}
        <Card>
          <CardContent className="p-0">
            {filteredNotifications.length === 0 ? (
              <div className="py-12 text-center">
                <Bell className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                <p className="text-gray-500">No notifications to show</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {filteredNotifications.map((notification) => {
                  const Icon = notificationIcons[notification.type as keyof typeof notificationIcons] || Bell;
                  return (
                    <li
                      key={notification.id}
                      className={cn(
                        "p-5 hover:bg-gray-50/50 transition-colors cursor-pointer",
                        !notification.read && "bg-amber-50/30"
                      )}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={cn(
                            "p-2.5 rounded-xl",
                            !notification.read
                              ? "bg-amber-100 text-amber-600"
                              : "bg-gray-100 text-gray-500"
                          )}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-gray-900">
                              {notification.title}
                            </span>
                            <PlatformBadge platform={notification.platform} size="sm" />
                            {!notification.read && (
                              <span className="w-2 h-2 bg-amber-500 rounded-full" />
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{notification.message}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {formatRelativeTime(notification.timestamp)}
                          </p>
                        </div>
                        {!notification.read && (
                          <Button variant="ghost" size="sm" className="text-gray-400">
                            <Check className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
