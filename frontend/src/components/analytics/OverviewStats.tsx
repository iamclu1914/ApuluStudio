"use client";

import { useQuery } from "@tanstack/react-query";
import { Users, Heart, FileText, TrendingUp, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { analyticsApi } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

export function OverviewStats() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsApi.getOverview().then((res) => res.data),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} hover={false}>
            <CardContent className="py-6">
              <div className="animate-pulse space-y-3">
                <div className="flex items-center justify-between">
                  <div className="h-10 w-10 bg-gray-200 rounded-xl" />
                  <div className="h-6 w-16 bg-gray-200 rounded-full" />
                </div>
                <div className="h-8 w-24 bg-gray-200 rounded-lg" />
                <div className="h-4 w-20 bg-gray-100 rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const stats = [
    {
      label: "Total Followers",
      value: data?.total_followers || 0,
      change: "+12.5%",
      isPositive: true,
      icon: Users,
      gradient: "from-blue-500 to-indigo-500",
      bgGradient: "from-blue-50 to-indigo-50",
    },
    {
      label: "Engagement",
      value: data?.total_engagement || 0,
      change: "+8.2%",
      isPositive: true,
      icon: Heart,
      gradient: "from-amber-500 to-orange-500",
      bgGradient: "from-amber-50 to-orange-50",
    },
    {
      label: "Posts This Week",
      value: data?.posts_this_week || 0,
      change: "-2.1%",
      isPositive: false,
      icon: FileText,
      gradient: "from-emerald-500 to-teal-500",
      bgGradient: "from-emerald-50 to-teal-50",
    },
    {
      label: "Engagement Rate",
      value: `${(data?.engagement_rate || 0).toFixed(1)}%`,
      change: "+5.4%",
      isPositive: true,
      icon: TrendingUp,
      gradient: "from-yellow-500 to-amber-500",
      bgGradient: "from-yellow-50 to-amber-50",
      isPercentage: true,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="overflow-hidden">
          <CardContent className="py-5 relative">
            {/* Background decoration */}
            <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${stat.bgGradient} rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2`} />

            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${stat.gradient} shadow-lg`}>
                  <stat.icon className="w-5 h-5 text-white" />
                </div>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                  stat.isPositive
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700"
                }`}>
                  {stat.isPositive ? (
                    <ArrowUpRight className="w-3 h-3" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3" />
                  )}
                  {stat.change}
                </div>
              </div>

              <p className="text-3xl font-bold text-gray-900">
                {stat.isPercentage ? stat.value : formatNumber(Number(stat.value))}
              </p>
              <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
