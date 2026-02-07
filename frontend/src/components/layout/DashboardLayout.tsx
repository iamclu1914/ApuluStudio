"use client";

import { useState, useEffect, useCallback } from "react";
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
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { accountsApi } from "@/lib/api";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { logout } from "@/store/auth";

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

  useEffect(() => { setMounted(true); }, []);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  // Close sidebar on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSidebarOpen(false);
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  // Prevent body scroll when sidebar is open
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [sidebarOpen]);

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  useEffect(() => {
    const storageKey = "apulu.lateSyncAt";
    const intervalMs = 5 * 60 * 1000;

    if (typeof window === "undefined") return;

    const lastSync = Number(window.sessionStorage.getItem(storageKey) || 0);
    const now = Date.now();
    if (now - lastSync < intervalMs) return;

    window.sessionStorage.setItem(storageKey, String(now));
    accountsApi.syncLate()
      .then(() => queryClient.invalidateQueries({ queryKey: ["accounts"] }))
      .catch(() => window.sessionStorage.removeItem(storageKey));
  }, [queryClient]);

  return (
    <AuthGuard>
    <div className="min-h-screen bg-stone-50/50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity duration-300"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-[280px] sm:w-72 gradient-sidebar transform transition-transform duration-300 ease-out lg:translate-x-0",
          "border-r border-white/[0.03] flex flex-col",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Subtle glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-amber-500/20 blur-[80px] pointer-events-none" />

        {/* Logo + mobile close */}
        <div className="relative flex items-center justify-between px-5 py-6 sm:px-6 sm:py-7">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl gradient-gold flex items-center justify-center shadow-lg shadow-amber-500/40">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#0c0c0e]" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight font-display">
                Apulu Studio
              </h1>
              <p className="text-[10px] sm:text-xs text-gray-500 font-medium">Social Media Suite</p>
            </div>
          </div>
          <button
            onClick={closeSidebar}
            className="lg:hidden p-2 rounded-xl hover:bg-white/[0.06] text-gray-400 hover:text-white transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Action */}
        <div className="px-4 mb-6">
          <Link
            href="/dashboard"
            className="group w-full flex items-center justify-center gap-2.5 px-5 py-3 sm:py-3.5 rounded-2xl gradient-primary text-white font-semibold text-sm shadow-lg shadow-amber-500/30 hover:shadow-xl hover:shadow-amber-500/40 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="w-4 h-4 transition-transform group-hover:rotate-90 duration-300" />
            Create Post
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
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
                  "group relative flex items-center gap-3 px-3.5 py-3 sm:py-3.5 rounded-2xl text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-white/[0.08] text-white"
                    : "text-gray-400 hover:bg-white/[0.04] hover:text-gray-200 active:bg-white/[0.06]"
                )}
                style={{ animationDelay: mounted ? `${index * 50}ms` : "0ms" }}
              >
                {isActive && (
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-amber-500/10 to-transparent pointer-events-none" />
                )}
                <div
                  className={cn(
                    "relative p-2 sm:p-2.5 rounded-xl transition-all duration-200",
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
        <div className="px-4 mb-3 hidden sm:block">
          <div className="p-4 rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-500/10">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-violet-400" />
              <span className="text-xs font-semibold text-violet-300">This Week</span>
            </div>
            <p className="text-2xl font-bold text-white font-display">+24%</p>
            <p className="text-xs text-gray-400 mt-1">engagement growth</p>
          </div>
        </div>

        {/* Pro Plan */}
        <div className="p-3.5 m-4 rounded-2xl bg-gradient-to-br from-amber-500/15 via-orange-500/10 to-transparent border border-amber-500/20 hidden sm:block">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-400 via-orange-400 to-yellow-500 flex items-center justify-center shadow-lg shadow-amber-500/30">
              <Zap className="w-4 h-4 text-gray-900" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">Pro Plan</p>
              <p className="text-xs text-amber-400/70">Unlimited access</p>
            </div>
          </div>
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full gradient-gold rounded-full transition-all duration-1000 ease-out" style={{ width: "75%" }} />
          </div>
          <p className="text-xs text-gray-400 mt-2 flex justify-between">
            <span>75% used</span>
            <span className="text-amber-400">7 days left</span>
          </p>
        </div>

        {/* Logout */}
        <div className="px-4 pb-4 pt-2">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium text-gray-400 hover:bg-white/[0.04] hover:text-gray-200 active:bg-white/[0.06] transition-all duration-200"
          >
            <div className="p-2 rounded-xl bg-white/[0.05]">
              <LogOut className="w-4 h-4" />
            </div>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-72 min-h-screen flex flex-col">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
          <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-xl hover:bg-gray-100 active:bg-gray-200 transition-colors lg:hidden"
                aria-label="Open menu"
              >
                <Menu className="w-5 h-5 text-gray-700" />
              </button>

              {/* Mobile logo */}
              <div className="flex items-center gap-2 lg:hidden">
                <div className="w-8 h-8 rounded-lg gradient-gold flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold text-gray-900 font-display text-sm">Apulu</span>
              </div>

              {/* Search — hidden on small screens */}
              <div className="hidden md:flex items-center gap-3 px-4 py-2.5 bg-gray-50 rounded-xl border border-gray-200/60 w-72 lg:w-80 focus-within:border-amber-400/50 focus-within:bg-white focus-within:shadow-lg focus-within:shadow-amber-500/5 transition-all duration-300">
                <Search className="w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search posts, analytics..."
                  className="flex-1 bg-transparent text-sm text-gray-700 placeholder-gray-400 outline-none"
                />
                <kbd className="hidden lg:inline-flex items-center px-2 py-0.5 text-[10px] font-bold text-gray-400 bg-gray-100 rounded-md border border-gray-200">
                  ⌘K
                </kbd>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              {/* Mobile search toggle */}
              <button className="p-2 rounded-xl hover:bg-gray-100 transition-colors md:hidden">
                <Search className="w-5 h-5 text-gray-600" />
              </button>

              {/* Notifications */}
              <Link
                href="/notifications"
                className="relative p-2 sm:p-2.5 rounded-xl bg-gray-50 hover:bg-gray-100 transition-all duration-200 border border-gray-200/60"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                <span className="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 w-2 h-2 bg-red-500 rounded-full" />
              </Link>

              {/* Profile */}
              <Link
                href="/account"
                className="flex items-center gap-2 sm:gap-3 p-1 sm:p-1.5 sm:pr-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-all duration-200 border border-gray-200/60 group"
              >
                <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg sm:rounded-xl gradient-gold flex items-center justify-center text-white font-bold text-sm shadow-md">
                  V
                </div>
                <div className="text-left hidden sm:block">
                  <span className="text-sm font-semibold text-gray-800 block leading-tight">Account</span>
                  <span className="text-xs text-gray-500">@therealvawn</span>
                </div>
              </Link>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main
          className={cn(
            "flex-1 p-4 sm:p-6 lg:p-8",
            mounted ? "animate-slide-up" : "opacity-0"
          )}
        >
          {children}
        </main>
      </div>
    </div>
    </AuthGuard>
  );
}
