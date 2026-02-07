"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Calendar,
  Inbox,
  BarChart3,
  Settings,
  Menu,
  X,
  Sparkles,
  Bell,
  Search,
  Plus,
  ChevronRight,
  Zap,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { accountsApi } from "@/lib/api";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Inbox", href: "/inbox", icon: Inbox },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  // Page load animation trigger
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const storageKey = "apulu.lateSyncAt";
    const intervalMs = 5 * 60 * 1000;

    if (typeof window === "undefined") {
      return;
    }

    const lastSync = Number(window.sessionStorage.getItem(storageKey) || 0);
    const now = Date.now();
    if (now - lastSync < intervalMs) {
      return;
    }

    window.sessionStorage.setItem(storageKey, String(now));
    accountsApi.syncLate()
      .then(() => {
        queryClient.invalidateQueries({ queryKey: ["accounts"] });
      })
      .catch(() => {
        window.sessionStorage.removeItem(storageKey);
      });
  }, [queryClient]);

  return (
    <div className="min-h-screen">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 gradient-sidebar transform transition-all duration-500 ease-out lg:translate-x-0",
          "border-r border-white/[0.03]",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Subtle glow effect at top */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-amber-500/20 blur-[80px] pointer-events-none" />

        <div className="relative flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3.5 px-6 py-7">
            <div className="relative">
              <div className="w-11 h-11 rounded-2xl gradient-gold flex items-center justify-center shadow-lg shadow-amber-500/40 animate-pulse-glow">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-400 rounded-full border-2 border-[#0c0c0e] animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight font-display">
                Apulu Studio
              </h1>
              <p className="text-xs text-gray-500 font-medium">Social Media Suite</p>
            </div>
          </div>

          {/* Quick Action */}
          <div className="px-4 mb-8">
            <Link
              href="/dashboard"
              className="group w-full flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-2xl gradient-primary text-white font-semibold text-sm shadow-lg shadow-amber-500/30 hover:shadow-xl hover:shadow-amber-500/40 transition-all duration-300 hover:scale-[1.02] btn-glow"
            >
              <Plus className="w-4.5 h-4.5 transition-transform group-hover:rotate-90 duration-300" />
              Create Post
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 space-y-1.5">
            <p className="px-4 mb-3 text-[11px] font-bold text-gray-600 uppercase tracking-[0.15em]">
              Navigation
            </p>
            {navigation.map((item, index) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "group relative flex items-center gap-3.5 px-4 py-3.5 rounded-2xl text-sm font-medium transition-all duration-300",
                    isActive
                      ? "bg-white/[0.08] text-white"
                      : "text-gray-400 hover:bg-white/[0.04] hover:text-gray-200"
                  )}
                  style={{
                    animationDelay: mounted ? `${index * 50}ms` : "0ms",
                  }}
                >
                  {/* Active indicator glow */}
                  {isActive && (
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-amber-500/10 to-transparent pointer-events-none" />
                  )}

                  <div
                    className={cn(
                      "relative p-2.5 rounded-xl transition-all duration-300",
                      isActive
                        ? "gradient-primary shadow-lg shadow-amber-500/30"
                        : "bg-white/[0.05] group-hover:bg-white/[0.08]"
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                  </div>
                  <span className="relative">{item.name}</span>
                  {isActive && (
                    <ChevronRight className="w-4 h-4 ml-auto text-amber-400/60" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Stats mini card */}
          <div className="px-4 mb-4">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-500/10">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-violet-400" />
                <span className="text-xs font-semibold text-violet-300">This Week</span>
              </div>
              <p className="text-2xl font-bold text-white font-display">+24%</p>
              <p className="text-xs text-gray-400 mt-1">engagement growth</p>
            </div>
          </div>

          {/* Bottom section - Pro Plan */}
          <div className="p-4 m-4 rounded-2xl bg-gradient-to-br from-amber-500/15 via-orange-500/10 to-transparent border border-amber-500/20">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-amber-400 via-orange-400 to-yellow-500 flex items-center justify-center shadow-lg shadow-amber-500/30">
                <Zap className="w-5 h-5 text-gray-900" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">Pro Plan</p>
                <p className="text-xs text-amber-400/70">Unlimited access</p>
              </div>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full gradient-gold rounded-full transition-all duration-1000 ease-out"
                style={{ width: "75%" }}
              />
            </div>
            <p className="text-xs text-gray-400 mt-2.5 flex justify-between">
              <span>75% of monthly usage</span>
              <span className="text-amber-400">7 days left</span>
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-72 min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 glass border-b border-gray-200/40">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2.5 rounded-xl hover:bg-gray-100/80 transition-colors lg:hidden"
              >
                <Menu className="w-5 h-5 text-gray-700" />
              </button>

              {/* Search */}
              <div className="hidden md:flex items-center gap-3 px-4 py-2.5 bg-white/60 rounded-2xl border border-gray-200/60 w-80 focus-within:border-amber-400/50 focus-within:shadow-lg focus-within:shadow-amber-500/10 transition-all duration-300">
                <Search className="w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search posts, analytics..."
                  className="flex-1 bg-transparent text-sm text-gray-700 placeholder-gray-400 outline-none"
                />
                <kbd className="hidden lg:inline-flex items-center px-2 py-1 text-[10px] font-bold text-gray-400 bg-gray-100 rounded-lg border border-gray-200">
                  ⌘K
                </kbd>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Notifications */}
              <Link
                href="/notifications"
                className="relative p-2.5 rounded-xl bg-white/70 hover:bg-white transition-all duration-300 border border-gray-200/60 hover:shadow-md hover:scale-105"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              </Link>

              {/* Profile */}
              <Link
                href="/account"
                className="flex items-center gap-3 p-1.5 pr-4 rounded-xl bg-white/70 hover:bg-white transition-all duration-300 border border-gray-200/60 hover:shadow-md group"
              >
                <div className="w-9 h-9 rounded-xl gradient-gold flex items-center justify-center text-white font-bold text-sm shadow-md group-hover:shadow-lg transition-shadow">
                  V
                </div>
                <div className="text-left hidden sm:block">
                  <span className="text-sm font-semibold text-gray-800 block">Account</span>
                  <span className="text-xs text-gray-500">@therealvawn</span>
                </div>
              </Link>
            </div>
          </div>
        </header>

        {/* Page content with reveal animation */}
        <main
          className={cn(
            "p-6 lg:p-8",
            mounted ? "animate-slide-up" : "opacity-0"
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
