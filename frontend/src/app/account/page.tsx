"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  User,
  Mail,
  Lock,
  Camera,
  Edit2,
  Shield,
  CreditCard,
  LogOut,
  Sparkles,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { accountsApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function AccountPage() {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState("Vawn");
  const [email, setEmail] = useState("vawn@example.com");
  const [username, setUsername] = useState("therealvawn");

  const { data: accounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((res) => res.data),
  });

  const connectedCount = accounts?.length || 0;

  return (
    <DashboardLayout>
      <div className="space-y-6 sm:space-y-8 max-w-4xl">
        {/* Header */}
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="p-2.5 sm:p-3 rounded-xl sm:rounded-2xl gradient-primary shadow-lg shadow-amber-500/25">
            <User className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 font-display">Account</h1>
            <p className="text-gray-500 mt-0.5 sm:mt-1 text-sm">Manage your profile and preferences</p>
          </div>
        </div>

        {/* Profile Card */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div>
                  <CardTitle>Profile Information</CardTitle>
                  <CardDescription>Update your personal details</CardDescription>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(!isEditing)}
                className="self-start sm:self-auto"
              >
                <Edit2 className="w-4 h-4" />
                {isEditing ? "Cancel" : "Edit"}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="py-6">
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 sm:gap-8">
              {/* Avatar */}
              <div className="relative flex-shrink-0">
                <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl gradient-gold flex items-center justify-center text-white text-2xl sm:text-3xl font-bold shadow-lg">
                  V
                </div>
                {isEditing && (
                  <button className="absolute -bottom-2 -right-2 p-2 rounded-xl bg-white border-2 border-gray-200 shadow-md hover:shadow-lg transition-shadow">
                    <Camera className="w-4 h-4 text-gray-600" />
                  </button>
                )}
              </div>

              {/* Form */}
              <div className="flex-1 w-full space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Display Name
                    </label>
                    <Input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      disabled={!isEditing}
                      className={cn(!isEditing && "bg-gray-50")}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Username
                    </label>
                    <Input
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={!isEditing}
                      className={cn(!isEditing && "bg-gray-50")}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Email Address
                  </label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={!isEditing}
                    className={cn(!isEditing && "bg-gray-50")}
                  />
                </div>
                {isEditing && (
                  <div className="flex gap-3 pt-2">
                    <Button>Save Changes</Button>
                    <Button variant="ghost" onClick={() => setIsEditing(false)}>
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Connected Accounts Summary */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div>
                <CardTitle>Connected Accounts</CardTitle>
                <CardDescription>
                  {connectedCount} platform{connectedCount !== 1 ? "s" : ""} connected
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="py-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-gray-600 text-sm sm:text-base">
                Manage your social media connections in Settings
              </p>
              <a
                href="/settings"
                className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-xl border-2 border-gray-200 bg-white hover:bg-gray-50 text-gray-700 transition-colors self-start sm:self-auto flex-shrink-0"
              >
                Manage Connections
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card className="border-2 border-amber-200 bg-gradient-to-br from-amber-50/50 to-yellow-50/50">
          <CardHeader className="border-b border-amber-200/50">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl gradient-gold">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <CardTitle>Pro Plan</CardTitle>
                <CardDescription>Your current subscription</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="py-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p className="text-2xl font-bold text-gray-900">$19/month</p>
                <p className="text-sm text-gray-500 mt-1">
                  Renews on February 28, 2026
                </p>
              </div>
              <div className="flex gap-3">
                <Button variant="outline">
                  <CreditCard className="w-4 h-4" />
                  Manage Billing
                </Button>
              </div>
            </div>
            <div className="mt-6 p-4 rounded-xl bg-white/60 border border-amber-200/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Monthly Usage</span>
                <span className="text-sm text-amber-600 font-medium">75 / 120 posts</span>
              </div>
              <div className="h-2 bg-amber-100 rounded-full overflow-hidden">
                <div
                  className="h-full gradient-gold rounded-full"
                  style={{ width: "62.5%" }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200">
          <CardHeader className="border-b border-red-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-red-100">
                <LogOut className="w-4 h-4 text-red-600" />
              </div>
              <div>
                <CardTitle className="text-red-700">Danger Zone</CardTitle>
                <CardDescription>Irreversible account actions</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="py-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p className="font-medium text-gray-900">Sign Out</p>
                <p className="text-sm text-gray-500">
                  Sign out of your account on this device
                </p>
              </div>
              <Button variant="outline" className="text-red-600 border-red-200 hover:bg-red-50 self-start sm:self-auto">
                <LogOut className="w-4 h-4" />
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
