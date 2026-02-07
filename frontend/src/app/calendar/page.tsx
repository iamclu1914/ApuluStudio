"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Calendar as CalendarIcon,
} from "lucide-react";
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
} from "date-fns";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { postsApi, Post } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function CalendarPage() {
  const router = useRouter();
  const [currentDate, setCurrentDate] = useState(new Date());

  const handleNewPost = () => {
    // Navigate to dashboard with today's date pre-filled for scheduling
    const scheduleDate = format(new Date(), "yyyy-MM-dd'T'HH:mm");
    router.push(`/dashboard?scheduleDate=${encodeURIComponent(scheduleDate)}`);
  };

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);

  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  // Fetch posts for this month
  const { data: posts } = useQuery({
    queryKey: ["posts", "calendar", format(currentDate, "yyyy-MM")],
    queryFn: () =>
      postsApi
        .getCalendar(
          monthStart.toISOString(),
          monthEnd.toISOString()
        )
        .then((res) => res.data),
  });

  const getPostsForDay = (day: Date) => {
    return (
      posts?.filter((post) => {
        const postDate = new Date(post.scheduled_at || post.created_at);
        return isSameDay(postDate, day);
      }) || []
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl gradient-primary shadow-lg shadow-amber-500/25">
            <CalendarIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Content Calendar</h1>
            <p className="text-gray-500 mt-1">
              Schedule and manage your posts
            </p>
          </div>
        </div>

        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentDate(subMonths(currentDate, 1))}
                  className="hover:bg-gray-100"
                >
                  <ChevronLeft className="w-5 h-5" />
                </Button>
                <span className="text-xl font-bold text-gray-900 min-w-[180px] text-center">
                  {format(currentDate, "MMMM yyyy")}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentDate(addMonths(currentDate, 1))}
                  className="hover:bg-gray-100"
                >
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </div>
              <Button size="lg" onClick={handleNewPost}>
                <Plus className="w-4 h-4" />
                New Post
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {/* Day headers */}
            <div className="grid grid-cols-7 border-b border-gray-100 bg-gray-50/50">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                <div
                  key={day}
                  className="py-3 text-center text-sm font-semibold text-gray-600"
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar grid */}
            <div className="grid grid-cols-7">
              {days.map((day, index) => {
                const dayPosts = getPostsForDay(day);
                const isCurrentMonth = isSameMonth(day, currentDate);
                const isToday = isSameDay(day, new Date());
                const isFirstRow = index < 7;
                const isFirstCol = index % 7 === 0;

                return (
                  <div
                    key={day.toISOString()}
                    className={cn(
                      "min-h-[120px] p-3 border-b border-r border-gray-100 transition-colors hover:bg-gray-50/50",
                      !isCurrentMonth && "bg-gray-50/30",
                      isFirstRow && "border-t-0",
                      isFirstCol && "border-l-0"
                    )}
                  >
                    <div
                      className={cn(
                        "w-8 h-8 flex items-center justify-center text-sm rounded-full mb-2 font-medium transition-all",
                        isToday
                          ? "gradient-primary text-white font-bold shadow-lg shadow-amber-500/25"
                          : isCurrentMonth
                          ? "text-gray-900 hover:bg-gray-100"
                          : "text-gray-400"
                      )}
                    >
                      {format(day, "d")}
                    </div>

                    {/* Posts for this day */}
                    <div className="space-y-1.5">
                      {dayPosts.slice(0, 3).map((post) => (
                        <PostPreview key={post.id} post={post} />
                      ))}
                      {dayPosts.length > 3 && (
                        <p className="text-xs font-medium text-amber-600 cursor-pointer hover:text-amber-700">
                          +{dayPosts.length - 3} more
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

function PostPreview({ post }: { post: Post }) {
  const statusStyles: Record<string, string> = {
    scheduled: "bg-blue-50 text-blue-700 border border-blue-200",
    published: "bg-green-50 text-green-700 border border-green-200",
    draft: "bg-gray-50 text-gray-700 border border-gray-200",
    failed: "bg-red-50 text-red-700 border border-red-200",
  };

  return (
    <div
      className={cn(
        "p-2 rounded-lg text-xs cursor-pointer hover:shadow-md transition-all",
        statusStyles[post.status] || statusStyles.draft
      )}
    >
      <div className="flex items-center gap-1.5 mb-1">
        {post.platforms.slice(0, 2).map((pp) => (
          <PlatformBadge key={pp.id} platform={pp.platform} size="sm" />
        ))}
        {post.platforms.length > 2 && (
          <span className="text-[10px] text-gray-500">+{post.platforms.length - 2}</span>
        )}
      </div>
      <p className="line-clamp-1 font-medium">{post.content}</p>
    </div>
  );
}
