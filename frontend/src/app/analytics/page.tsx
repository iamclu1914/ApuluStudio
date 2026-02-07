"use client";

import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, TrendingDown, Award, BarChart3 } from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { OverviewStats } from "@/components/analytics/OverviewStats";
import { analyticsApi, GrowthDataPoint, TopPost } from "@/lib/api";
import { formatNumber, formatDate, cn } from "@/lib/utils";

export default function AnalyticsPage() {
  const { data: growth } = useQuery({
    queryKey: ["analytics", "growth"],
    queryFn: () => analyticsApi.getGrowth(undefined, 30).then((res) => res.data),
  });

  const { data: topPosts } = useQuery({
    queryKey: ["analytics", "top-posts"],
    queryFn: () => analyticsApi.getTopPosts(7, 5).then((res) => res.data),
  });

  const chartData =
    growth?.data_points?.map((point: GrowthDataPoint) => ({
      date: formatDate(point.date),
      followers: point.followers,
      engagement: point.engagement,
    })) || [];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="p-2.5 sm:p-3 rounded-xl sm:rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 shadow-lg shadow-green-500/25">
            <BarChart3 className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 font-display">Analytics</h1>
            <p className="text-gray-500 mt-0.5 sm:mt-1 text-sm sm:text-base">
              Track your social media performance
            </p>
          </div>
        </div>

        {/* Overview Stats */}
        <OverviewStats />

        {/* Growth Chart */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500">
                  <TrendingUp className="w-4 h-4 text-white" />
                </div>
                <div>
                  <CardTitle>Follower Growth</CardTitle>
                  <CardDescription>Last 30 days performance</CardDescription>
                </div>
              </div>
              {growth && (
                <div
                  className={cn(
                    "flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-semibold",
                    growth.percent_change >= 0
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  )}
                >
                  {growth.percent_change >= 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  {growth.percent_change >= 0 ? "+" : ""}
                  {growth.percent_change}%
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[250px] sm:h-[350px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <defs>
                    <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e2e8f0" }}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e2e8f0" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "none",
                      borderRadius: "12px",
                      boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
                      padding: "12px 16px",
                    }}
                    labelStyle={{ color: "#1f2937", fontWeight: 600, marginBottom: 4 }}
                    itemStyle={{ color: "#8b5cf6" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="followers"
                    stroke="#8b5cf6"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 6, fill: "#8b5cf6", stroke: "white", strokeWidth: 2 }}
                    fill="url(#colorFollowers)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Posts */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500">
                <Award className="w-4 h-4 text-white" />
              </div>
              <div>
                <CardTitle>Top Performing Posts</CardTitle>
                <CardDescription>Your best content this week</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {!topPosts || topPosts.length === 0 ? (
              <div className="py-16 text-center">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                  <Award className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-900 font-semibold text-lg">No posts data available</p>
                <p className="text-sm text-gray-500 mt-1">Start posting to see your top content</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {topPosts.map((post: TopPost, index: number) => (
                  <li key={post.id} className="p-3.5 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 hover:bg-gray-50/50 transition-colors">
                    <div className="flex items-center gap-3 sm:gap-4">
                      <div
                        className={cn(
                          "w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center font-bold text-xs sm:text-sm shadow-lg flex-shrink-0",
                          index === 0
                            ? "bg-gradient-to-br from-yellow-400 to-orange-500 text-white"
                            : index === 1
                            ? "bg-gradient-to-br from-gray-300 to-gray-400 text-white"
                            : index === 2
                            ? "bg-gradient-to-br from-orange-300 to-orange-400 text-white"
                            : "bg-gray-100 text-gray-500"
                        )}
                      >
                        {index + 1}
                      </div>

                      <div className="w-10 h-10 sm:w-14 sm:h-14 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 flex-shrink-0 overflow-hidden shadow-inner">
                        {post.thumbnail_url ? (
                          <img
                            src={post.thumbnail_url}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-lg sm:text-2xl">
                            📝
                          </div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 font-medium line-clamp-1">
                          {post.content}
                        </p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <PlatformBadge platform={post.platform} size="sm" />
                          <span className="text-xs text-gray-500">
                            {formatDate(post.published_at)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 sm:gap-6 text-sm ml-11 sm:ml-0">
                      <div className="text-center">
                        <p className="font-bold text-gray-900 text-base sm:text-lg">
                          {formatNumber(post.likes_count)}
                        </p>
                        <p className="text-xs text-gray-500 font-medium">Likes</p>
                      </div>
                      <div className="text-center">
                        <p className="font-bold text-gray-900 text-base sm:text-lg">
                          {formatNumber(post.comments_count)}
                        </p>
                        <p className="text-xs text-gray-500 font-medium">Comments</p>
                      </div>
                      <div className="text-center">
                        <p className="font-bold text-gray-900 text-base sm:text-lg">
                          {formatNumber(post.shares_count)}
                        </p>
                        <p className="text-xs text-gray-500 font-medium">Shares</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
