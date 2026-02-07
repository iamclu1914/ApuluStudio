import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { QuickPost } from "@/components/posts/QuickPost";
import { UpcomingPosts } from "@/components/posts/UpcomingPosts";
import { OverviewStats } from "@/components/analytics/OverviewStats";
import { RecentActivity } from "@/components/inbox/RecentActivity";
import { Sparkles, TrendingUp, Zap } from "lucide-react";

export default function Dashboard() {
  return (
    <DashboardLayout>
      <div className="space-y-6 sm:space-y-8">
        {/* Welcome Header */}
        <div className="flex flex-col gap-3 sm:gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 font-display">
              Welcome back! <span className="inline-block animate-wave">👋</span>
            </h1>
            <p className="text-gray-500 mt-1 text-sm sm:text-base">
              Here&apos;s what&apos;s happening with your social presence today.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl bg-green-50 border border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs sm:text-sm font-medium text-green-700">All systems operational</span>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <section>
          <div className="flex items-center gap-2 mb-3 sm:mb-4">
            <div className="p-1.5 sm:p-2 rounded-lg gradient-primary">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">Overview</h2>
          </div>
          <OverviewStats />
        </section>

        {/* Quick Post */}
        <section>
          <div className="flex items-center gap-2 mb-3 sm:mb-4">
            <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <h2 className="text-base sm:text-lg font-semibold text-gray-900">Quick Post</h2>
            <span className="ml-1 sm:ml-2 px-2 py-0.5 text-[10px] sm:text-xs font-medium text-amber-700 bg-amber-100 rounded-full">
              AI Powered
            </span>
          </div>
          <QuickPost />
        </section>

        {/* Two column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
          <section>
            <div className="flex items-center gap-2 mb-3 sm:mb-4">
              <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-r from-yellow-500 to-amber-500">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <h2 className="text-base sm:text-lg font-semibold text-gray-900">Upcoming Posts</h2>
            </div>
            <UpcomingPosts />
          </section>

          <section>
            <div className="flex items-center gap-2 mb-3 sm:mb-4">
              <div className="p-1.5 sm:p-2 rounded-lg gradient-gold">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <h2 className="text-base sm:text-lg font-semibold text-gray-900">Recent Activity</h2>
            </div>
            <RecentActivity />
          </section>
        </div>
      </div>
    </DashboardLayout>
  );
}
