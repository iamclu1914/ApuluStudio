"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp } from "lucide-react";
import { ResponsiveContainer, LineChart, Line } from "recharts";
import { analyticsApi } from "@/lib/api";
import { formatNumber, cn } from "@/lib/utils";
import { PlatformBadge } from "@/components/ui/PlatformBadge";

type Range = "7d" | "30d" | "90d";

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const chartData = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={32}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function ChangeIndicator({ pct }: { pct: number }) {
  const isPositive = pct >= 0;
  return (
    <span
      className={cn(
        "text-xs font-medium",
        isPositive
          ? "text-green-600 dark:text-green-400"
          : "text-red-600 dark:text-red-400"
      )}
    >
      {isPositive ? "↑" : "↓"} {Math.abs(pct).toFixed(1)}%
    </span>
  );
}

function MetricCard({
  label,
  value,
  pct,
  sparkline,
  color,
  range,
}: {
  label: string;
  value: string | number;
  pct: number;
  sparkline: number[];
  color: string;
  range: Range;
}) {
  return (
    <div className="bg-white dark:bg-dark-surface rounded-xl p-4 border border-surface-200 dark:border-dark-border shadow-sm dark:shadow-none">
      <p className="text-xs text-surface-500 dark:text-surface-400 font-medium uppercase tracking-wide">
        {label}
      </p>
      <p className="text-2xl font-bold text-surface-900 dark:text-surface-50 mt-1">
        {typeof value === "number" ? formatNumber(value) : value}
      </p>
      <div className="flex items-center justify-between mt-1">
        <ChangeIndicator pct={pct} />
        <span className="text-xs text-surface-400">{range}</span>
      </div>
      {sparkline.length > 0 && (
        <div className="mt-2">
          <Sparkline data={sparkline} color={color} />
        </div>
      )}
    </div>
  );
}

function PlatformBreakdownCard({
  breakdown,
}: {
  breakdown: { platform: string; followers: number }[];
}) {
  return (
    <div className="bg-white dark:bg-dark-surface rounded-xl p-4 border border-surface-200 dark:border-dark-border shadow-sm dark:shadow-none h-full">
      <p className="text-xs text-surface-500 dark:text-surface-400 font-medium uppercase tracking-wide mb-3">
        Platforms
      </p>
      <div className="space-y-2">
        {breakdown.map((p) => (
          <div key={p.platform} className="flex items-center justify-between">
            <PlatformBadge platform={p.platform} size="sm" showLabel />
            <span className="text-sm font-medium text-surface-700 dark:text-surface-300">
              {formatNumber(p.followers)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function GrowthBanner() {
  const [range, setRange] = useState<Range>("7d");
  // Collapsed by default on mobile — SSR-safe
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setCollapsed(true);
    }
  }, []);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["analytics", "overview", range],
    queryFn: () => analyticsApi.getOverview(range).then((r) => r.data),
  });

  const collapsedBar = (
    <div className="flex items-center justify-between px-4 py-2 bg-white dark:bg-dark-surface border border-surface-200 dark:border-dark-border rounded-xl">
      <div className="flex items-center gap-4 text-sm flex-wrap">
        <span className="text-surface-500 dark:text-surface-400">
          Followers{" "}
          <strong className="text-surface-900 dark:text-surface-50">
            {formatNumber(data?.total_followers ?? 0)}
          </strong>
        </span>
        <span className="text-surface-500 dark:text-surface-400">
          Reach{" "}
          <strong className="text-surface-900 dark:text-surface-50">
            {formatNumber(data?.reach ?? 0)}
          </strong>
        </span>
        <span className="text-surface-500 dark:text-surface-400">
          Impressions{" "}
          <strong className="text-surface-900 dark:text-surface-50">
            {formatNumber(data?.impressions ?? 0)}
          </strong>
        </span>
        <span className="text-surface-500 dark:text-surface-400">
          Engagement{" "}
          <strong className="text-surface-900 dark:text-surface-50">
            {(data?.engagement_rate ?? 0).toFixed(1)}%
          </strong>
        </span>
      </div>
      <button
        onClick={() => setCollapsed(false)}
        className="p-1 rounded hover:bg-surface-100 dark:hover:bg-dark-border ml-2 flex-shrink-0"
      >
        <ChevronDown className="w-4 h-4 text-surface-400" />
      </button>
    </div>
  );

  if (collapsed) return collapsedBar;

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="bg-white dark:bg-dark-surface rounded-xl p-4 border border-surface-200 dark:border-dark-border animate-pulse"
          >
            <div className="h-3 w-16 bg-surface-200 dark:bg-dark-border rounded mb-2" />
            <div className="h-8 w-20 bg-surface-200 dark:bg-dark-border rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="bg-white dark:bg-dark-surface rounded-xl p-4 border border-surface-200 dark:border-dark-border"
          >
            <p className="text-xs text-surface-400 dark:text-surface-500 font-medium uppercase tracking-wide">
              --
            </p>
            <p className="text-sm text-surface-400 dark:text-surface-500 mt-1">
              Could not load
            </p>
          </div>
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-4 text-center text-surface-400 dark:text-surface-500 text-sm">
        No data yet — connect your accounts to see growth metrics.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-surface-700 dark:text-surface-300 uppercase tracking-wide">
          Growth Overview
        </h2>
        <div className="flex items-center gap-2">
          {/* Range selector */}
          <div className="flex items-center gap-1 bg-surface-100 dark:bg-dark-border rounded-lg p-0.5">
            {(["7d", "30d", "90d"] as Range[]).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={cn(
                  "px-3 py-1 text-xs font-medium rounded-md transition-colors",
                  range === r
                    ? "bg-white dark:bg-dark-surface text-surface-900 dark:text-surface-50 shadow-sm"
                    : "text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200"
                )}
              >
                {r}
              </button>
            ))}
          </div>
          {/* Collapse button */}
          <button
            onClick={() => setCollapsed(true)}
            className="p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-dark-border transition-colors"
            aria-label="Collapse growth banner"
          >
            <ChevronUp className="w-4 h-4 text-surface-400" />
          </button>
        </div>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        <MetricCard
          label="Followers"
          value={data.total_followers}
          pct={data.followers_change_pct ?? 0}
          sparkline={data.followers_sparkline ?? []}
          color="#7C3AED"
          range={range}
        />
        <MetricCard
          label="Reach"
          value={data.reach ?? 0}
          pct={data.reach_change_pct ?? 0}
          sparkline={data.reach_sparkline ?? []}
          color="#0085FF"
          range={range}
        />
        <MetricCard
          label="Impressions"
          value={data.impressions ?? 0}
          pct={data.impressions_change_pct ?? 0}
          sparkline={data.impressions_sparkline ?? []}
          color="#E1306C"
          range={range}
        />
        <MetricCard
          label="Engagement"
          value={`${(data.engagement_rate ?? 0).toFixed(1)}%`}
          pct={data.engagement_change_pct ?? 0}
          sparkline={data.engagement_sparkline ?? []}
          color="#16A34A"
          range={range}
        />
        <div className="col-span-2 md:col-span-1">
          <PlatformBreakdownCard
            breakdown={
              data.platform_breakdown ??
              (data.platforms?.map((p) => ({
                platform: p.platform,
                followers: p.followers,
              })) ?? [])
            }
          />
        </div>
      </div>
    </div>
  );
}
