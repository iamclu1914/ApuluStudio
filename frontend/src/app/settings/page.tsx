"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Link as LinkIcon,
  Check,
  AlertCircle,
  ExternalLink,
  Trash2,
  RefreshCw,
  Settings,
  Shield,
  Sparkles,
} from "lucide-react";
import toast from "react-hot-toast";
import axios from "axios";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { accountsApi } from "@/lib/api";
import { formatNumber, formatDate, cn } from "@/lib/utils";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [blueskyHandle, setBlueskyHandle] = useState("");
  const [blueskyPassword, setBlueskyPassword] = useState("");
  const [showBlueskyForm, setShowBlueskyForm] = useState(false);

  const { data: connectionStatus, isLoading } = useQuery({
    queryKey: ["accounts", "status"],
    queryFn: () => accountsApi.getStatus().then((res) => res.data),
  });

  const connectBluesky = useMutation({
    mutationFn: () =>
      accountsApi.connectBluesky(blueskyHandle, blueskyPassword),
    onSuccess: () => {
      toast.success("Bluesky connected!");
      setBlueskyHandle("");
      setBlueskyPassword("");
      setShowBlueskyForm(false);
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : "Failed to connect Bluesky";
      toast.error(message);
    },
  });

  const disconnectAccount = useMutation({
    mutationFn: (id: string) => accountsApi.disconnect(id),
    onSuccess: () => {
      toast.success("Account disconnected");
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
    onError: () => {
      toast.error("Failed to disconnect");
    },
  });

  const syncAccount = useMutation({
    mutationFn: (id: string) => accountsApi.sync(id),
    onSuccess: () => {
      toast.success("Account synced");
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
    onError: () => {
      toast.error("Failed to sync");
    },
  });

  const syncLateAccounts = useMutation({
    mutationFn: () => accountsApi.syncLate(),
    onSuccess: (response) => {
      const count = response.data.synced?.length || 0;
      toast.success(`Synced ${count} account(s) from LATE`);
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : "Failed to sync LATE accounts";
      toast.error(message);
    },
  });

  const platforms: {
    key: string;
    name: string;
    description: string;
    oauth: boolean;
  }[] = [
    {
      key: "instagram",
      name: "Instagram",
      description: "Requires Instagram Business account connected to a Facebook Page",
      oauth: true,
    },
    {
      key: "facebook",
      name: "Facebook",
      description: "Connect your Facebook Pages for posting",
      oauth: true,
    },
    {
      key: "bluesky",
      name: "Bluesky",
      description: "Connect using an App Password from bsky.app settings",
      oauth: false,
    },
    {
      key: "tiktok",
      name: "TikTok",
      description: "Connect your TikTok account for video content",
      oauth: true,
    },
    {
      key: "x",
      name: "X (Twitter)",
      description: "Connect your X account for posting",
      oauth: true,
    },
    {
      key: "threads",
      name: "Threads",
      description: "Requires Instagram connection",
      oauth: true,
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-4xl">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl gradient-primary shadow-lg shadow-amber-500/25">
            <Settings className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-500 mt-1">
              Manage your connected accounts and preferences
            </p>
          </div>
        </div>

        {/* Connected Accounts */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-500">
                  <LinkIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <CardTitle>Connected Accounts</CardTitle>
                  <CardDescription>Link your social media profiles</CardDescription>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => syncLateAccounts.mutate()}
                loading={syncLateAccounts.isPending}
              >
                <RefreshCw className="w-4 h-4" />
                Sync from LATE
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="py-12 flex items-center justify-center">
                <div className="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {platforms.map((platform) => {
                  const status = connectionStatus?.find(
                    (s) => s.platform.toLowerCase() === platform.key
                  );
                  const isConnected = status?.connected;
                  const account = status?.account;

                  return (
                    <li key={platform.key} className="p-5 hover:bg-gray-50/50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <PlatformBadge
                            platform={platform.key}
                            size="lg"
                          />
                          <div>
                            <h3 className="font-semibold text-gray-900">
                              {platform.name}
                            </h3>
                            <p className="text-sm text-gray-500 mt-0.5 max-w-md">
                              {platform.description}
                            </p>

                            {account && (
                              <div className="mt-3 flex items-center gap-4">
                                <span className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 text-sm font-medium text-gray-700">
                                  @{account.username}
                                </span>
                                <span className="text-sm text-gray-500">
                                  {formatNumber(account.follower_count)} followers
                                </span>
                                <span className="text-xs text-gray-400">
                                  Synced: {account.last_synced ? formatDate(account.last_synced) : "Never"}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {isConnected ? (
                            <>
                              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-100 text-sm font-medium text-green-700">
                                <Check className="w-4 h-4" />
                                Connected
                              </span>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  account && syncAccount.mutate(account.id)
                                }
                                loading={syncAccount.isPending}
                                className="text-gray-500 hover:text-gray-700"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  account &&
                                  disconnectAccount.mutate(account.id)
                                }
                                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
                          ) : status?.requires_reconnect ? (
                            <Button variant="outline" size="sm">
                              <AlertCircle className="w-4 h-4 mr-1.5 text-amber-500" />
                              Reconnect
                            </Button>
                          ) : platform.key === "bluesky" ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setShowBlueskyForm(true)}
                            >
                              <LinkIcon className="w-4 h-4 mr-1.5" />
                              Connect
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                toast(
                                  `Connect ${platform.name} via LATE dashboard, then click "Sync from LATE"`,
                                  { icon: "ℹ️" }
                                );
                              }}
                            >
                              <LinkIcon className="w-4 h-4 mr-1.5" />
                              Connect
                            </Button>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Bluesky Connection Form */}
        {showBlueskyForm && (
          <Card className="border-2 border-amber-200 bg-gradient-to-br from-amber-50/50 to-yellow-50/50">
            <CardHeader>
              <div className="flex items-center gap-3">
                <PlatformBadge platform="bluesky" size="lg" />
                <div>
                  <CardTitle>Connect Bluesky</CardTitle>
                  <CardDescription>Use an App Password for secure access</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>How to get an App Password:</strong>
                </p>
                <ol className="text-sm text-blue-700 mt-2 space-y-1 list-decimal list-inside">
                  <li>Go to <a
                    href="https://bsky.app/settings/app-passwords"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium underline hover:text-blue-900"
                  >
                    bsky.app/settings/app-passwords
                    <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a></li>
                  <li>Click "Add App Password"</li>
                  <li>Name it "Apulu Studio" and copy the password</li>
                </ol>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Handle
                  </label>
                  <Input
                    placeholder="yourname.bsky.social"
                    value={blueskyHandle}
                    onChange={(e) => setBlueskyHandle(e.target.value)}
                    className="bg-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    App Password
                  </label>
                  <Input
                    type="password"
                    placeholder="xxxx-xxxx-xxxx-xxxx"
                    value={blueskyPassword}
                    onChange={(e) => setBlueskyPassword(e.target.value)}
                    className="bg-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <Button
                  onClick={() => connectBluesky.mutate()}
                  loading={connectBluesky.isPending}
                  disabled={!blueskyHandle || !blueskyPassword}
                  size="lg"
                >
                  <Check className="w-4 h-4" />
                  Connect Bluesky
                </Button>
                <Button
                  variant="ghost"
                  size="lg"
                  onClick={() => {
                    setShowBlueskyForm(false);
                    setBlueskyHandle("");
                    setBlueskyPassword("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Security Section */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div>
                <CardTitle>Security & Privacy</CardTitle>
                <CardDescription>Your data protection settings</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="py-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50">
                <div>
                  <p className="font-medium text-gray-900">Data Encryption</p>
                  <p className="text-sm text-gray-500">All credentials are encrypted at rest</p>
                </div>
                <span className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium">
                  Enabled
                </span>
              </div>
              <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50">
                <div>
                  <p className="font-medium text-gray-900">OAuth Tokens</p>
                  <p className="text-sm text-gray-500">Securely stored in Supabase</p>
                </div>
                <span className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium">
                  Secure
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* App Info */}
        <Card>
          <CardHeader className="border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl gradient-gold">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <CardTitle>About Apulu Studio</CardTitle>
                <CardDescription>Version and build information</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="py-6">
            <div className="flex items-center gap-6">
              <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center shadow-lg shadow-amber-500/25">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">Apulu Studio</h3>
                <p className="text-gray-500">v0.1.0 Beta</p>
                <p className="text-sm text-gray-400 mt-1">
                  Built with Next.js, FastAPI, and Supabase
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
