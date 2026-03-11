"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Inbox,
  BarChart3,
  Settings,
  Menu,
  Sun,
  Moon,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useThemeStore } from "@/store/theme";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Inbox", href: "/inbox", icon: Inbox },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const { isDark, toggle } = useThemeStore();

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-dark-bg transition-colors">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-dark-surface border-r border-surface-200 dark:border-dark-border transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 px-6 py-5 border-b border-surface-200 dark:border-dark-border">
            <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-surface-900 dark:text-surface-50">
              Apulu Studio
            </span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300"
                      : "text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-dark-border hover:text-surface-900 dark:hover:text-surface-50"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Bottom section */}
          <div className="p-4 border-t border-surface-200 dark:border-dark-border">
            <div className="p-3 rounded-lg bg-primary-50 dark:bg-primary-900/20">
              <p className="text-sm font-medium text-primary-900 dark:text-primary-300">
                Free Plan
              </p>
              <p className="text-xs text-primary-700 dark:text-primary-400 mt-1">
                Unlimited during beta
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-white dark:bg-dark-surface border-b border-surface-200 dark:border-dark-border">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 -ml-2 rounded-lg hover:bg-surface-100 dark:hover:bg-dark-border lg:hidden"
            >
              <Menu className="w-5 h-5 text-surface-600 dark:text-surface-400" />
            </button>

            <div className="flex items-center gap-4 ml-auto">
              <button
                onClick={toggle}
                className="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-dark-border transition-colors"
                aria-label="Toggle dark mode"
              >
                {isDark ? (
                  <Sun className="w-5 h-5 text-surface-400" />
                ) : (
                  <Moon className="w-5 h-5 text-surface-600" />
                )}
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
