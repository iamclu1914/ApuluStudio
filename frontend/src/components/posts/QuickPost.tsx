"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sparkles, Image, Calendar, Send, Loader2, Wand2, Check, X, Clock, Smile, Zap, TrendingUp, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import axios from "axios";
import data from "@emoji-mart/data";
import Picker from "@emoji-mart/react";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { PlatformBadge } from "@/components/ui/PlatformBadge";
import { postsApi, accountsApi, aiApi } from "@/lib/api";
import { cn } from "@/lib/utils";

// Helper to format suggested time nicely
const formatSuggestedTime = (isoString: string) => {
  const date = new Date(isoString);
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const isToday = date.toDateString() === now.toDateString();
  const isTomorrow = date.toDateString() === tomorrow.toDateString();

  const timeStr = date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const dayStr = date.toLocaleDateString([], { weekday: "short" });

  if (isToday) return `Today ${timeStr}`;
  if (isTomorrow) return `Tomorrow ${timeStr}`;
  return `${dayStr} ${timeStr}`;
};

// Get engagement level color
const getEngagementColor = (level: string) => {
  switch (level) {
    case "peak": return "bg-green-100 text-green-700 border-green-200";
    case "high": return "bg-blue-100 text-blue-700 border-blue-200";
    case "moderate": return "bg-yellow-100 text-yellow-700 border-yellow-200";
    default: return "bg-gray-100 text-gray-700 border-gray-200";
  }
};

const PLATFORMS = ["instagram", "facebook", "x", "bluesky", "tiktok", "threads"];

// Character limits per platform
const PLATFORM_CHAR_LIMITS: Record<string, number> = {
  x: 280,
  bluesky: 300,
  threads: 500,
  instagram: 2200,
  tiktok: 2200,
  linkedin: 3000,
  facebook: 63206,
};

export function QuickPost() {
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [showAI, setShowAI] = useState(false);
  const [aiTopic, setAiTopic] = useState("");
  const [mediaUrls, setMediaUrls] = useState<string[]>([]);
  const [mediaPreview, setMediaPreview] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showSchedule, setShowSchedule] = useState(false);
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const emojiPickerRef = useRef<HTMLDivElement>(null);

  // Get connected accounts
  const { data: accounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((res) => res.data),
  });

  const connectedPlatforms =
    accounts?.map((a) => a.platform.toLowerCase()) || [];

  // Calculate maxLength based on selected platforms
  const maxLength = selectedPlatforms.length > 0
    ? Math.min(...selectedPlatforms.map(p => PLATFORM_CHAR_LIMITS[p] || 2200))
    : 2200;

  // Check which platforms are over their character limit
  const platformsOverLimit = selectedPlatforms.filter(
    platform => content.length > (PLATFORM_CHAR_LIMITS[platform] || 2200)
  );

  // Check if any selected platform is over its limit
  const isOverAnyLimit = platformsOverLimit.length > 0;

  // Fetch AI schedule suggestions when platforms are selected and schedule is shown
  const { data: suggestions, isLoading: suggestionsLoading } = useQuery({
    queryKey: ["schedule-suggestions", selectedPlatforms],
    queryFn: () => postsApi.getScheduleSuggestions(selectedPlatforms).then((res) => res.data),
    enabled: showSchedule && selectedPlatforms.length > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Apply a suggested time slot
  const applySuggestion = (isoString: string) => {
    const date = new Date(isoString);
    setScheduledDate(date.toISOString().split("T")[0]);
    setScheduledTime(date.toTimeString().slice(0, 5));
    toast.success("Suggested time applied!");
  };

  // Close emoji picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        emojiPickerRef.current &&
        !emojiPickerRef.current.contains(event.target as Node)
      ) {
        setShowEmojiPicker(false);
      }
    };

    if (showEmojiPicker) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showEmojiPicker]);

  // Handle emoji selection
  const handleEmojiSelect = (emoji: { native: string }) => {
    const textarea = textareaRef.current;
    if (textarea) {
      const start = textarea.selectionStart || 0;
      const end = textarea.selectionEnd || 0;
      const newContent =
        content.substring(0, start) + emoji.native + content.substring(end);
      setContent(newContent);

      // Set cursor position after emoji
      setTimeout(() => {
        textarea.focus();
        const newPos = start + emoji.native.length;
        textarea.setSelectionRange(newPos, newPos);
      }, 0);
    } else {
      setContent(content + emoji.native);
    }
  };

  // Publish post mutation
  const publishPost = useMutation({
    mutationFn: (postId: string) => postsApi.publish(postId),
    onSuccess: () => {
      toast.success("Post published successfully!");
      setContent("");
      setSelectedPlatforms([]);
      setMediaUrls([]);
      setMediaPreview(null);
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (error: unknown) => {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : "Failed to publish post";
      toast.error(message);
    },
  });

  // Create post mutation
  const createPost = useMutation({
    mutationFn: (data: {
      content: string;
      platforms: string[];
      scheduled_at?: string;
      media_urls?: string[];
      ai_generated?: boolean;
      publishNow?: boolean;
    }) => {
      const { publishNow, ...apiData } = data;
      return postsApi.create(apiData);
    },
    onSuccess: (response, variables) => {
      const isScheduled = !!variables.scheduled_at;
      if (isScheduled) {
        toast.success("Post scheduled successfully!");
        setContent("");
        setSelectedPlatforms([]);
        setMediaUrls([]);
        setMediaPreview(null);
        setScheduledDate("");
        setScheduledTime("");
        setShowSchedule(false);
        queryClient.invalidateQueries({ queryKey: ["posts"] });
      } else if (variables.publishNow) {
        // Publish immediately after creation
        publishPost.mutate(response.data.id);
      }
    },
    onError: (error: unknown) => {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "object" && detail?.errors) {
          // Validation errors - show the first error
          toast.error(detail.errors[0] || detail.message || "Validation failed");
        } else if (typeof detail === "string") {
          toast.error(detail);
        } else {
          toast.error("Failed to create post");
        }
      } else {
        toast.error("Failed to create post");
      }
    },
  });

  // Media upload handler
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4", "video/quicktime", "video/webm"];
    if (!validTypes.includes(file.type)) {
      toast.error("Invalid file type. Please upload an image or video.");
      return;
    }

    // Validate size (10MB for images, 100MB for videos)
    const maxSize = file.type.startsWith("video") ? 100 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error(`File too large. Max size: ${file.type.startsWith("video") ? "100MB" : "10MB"}`);
      return;
    }

    setIsUploading(true);
    try {
      // Show preview
      const reader = new FileReader();
      reader.onload = (e) => setMediaPreview(e.target?.result as string);
      reader.readAsDataURL(file);

      // Upload to server
      const response = await postsApi.upload(file, selectedPlatforms);
      setMediaUrls([response.data.url]);
      toast.success("Media uploaded!");
    } catch (error: unknown) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : "Failed to upload media";
      toast.error(message);
      setMediaPreview(null);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeMedia = () => {
    setMediaUrls([]);
    setMediaPreview(null);
  };

  // AI caption generation mutation
  const generateCaption = useMutation({
    mutationFn: (topic: string) =>
      aiApi.generateCaption({ topic, include_hashtags: true }),
    onSuccess: (response) => {
      const variations = response.data.variations;
      if (variations.length > 0) {
        const caption = variations[0];
        const hashtags = caption.hashtags.map((h) => `#${h}`).join(" ");
        setContent(`${caption.caption}\n\n${hashtags}`);
        toast.success("Caption generated!");
      }
      setShowAI(false);
      setAiTopic("");
    },
    onError: () => {
      toast.error("Failed to generate caption");
    },
  });

  const togglePlatform = (platform: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  // Platforms that require media
  const mediaRequiredPlatforms = ["instagram", "tiktok"];

  const handleSubmit = (schedule: boolean = false) => {
    if (!content.trim()) {
      toast.error("Please enter some content");
      return;
    }
    if (selectedPlatforms.length === 0) {
      toast.error("Please select at least one platform");
      return;
    }

    // Check if selected platforms require media
    const needsMedia = selectedPlatforms.some((p) =>
      mediaRequiredPlatforms.includes(p)
    );
    if (needsMedia && mediaUrls.length === 0) {
      const platforms = selectedPlatforms
        .filter((p) => mediaRequiredPlatforms.includes(p))
        .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
        .join(" and ");
      toast.error(`${platforms} requires media - please add an image or video`);
      return;
    }

    let scheduled_at: string | undefined;
    if (schedule && scheduledDate && scheduledTime) {
      scheduled_at = new Date(`${scheduledDate}T${scheduledTime}`).toISOString();
    } else if (schedule) {
      toast.error("Please select a date and time");
      return;
    }

    createPost.mutate({
      content: content.trim(),
      platforms: selectedPlatforms,
      scheduled_at,
      media_urls: mediaUrls.length > 0 ? mediaUrls : undefined,
      ai_generated: false,
      publishNow: !schedule, // Publish immediately if not scheduling
    });
  };

  const handleGenerateCaption = () => {
    if (!aiTopic.trim()) {
      toast.error("Please enter a topic");
      return;
    }
    generateCaption.mutate(aiTopic);
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {/* AI Generator Panel */}
        {showAI ? (
          <div className="p-6 bg-gradient-to-br from-amber-50 to-yellow-50">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl gradient-primary">
                  <Wand2 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">AI Caption Generator</h3>
                  <p className="text-sm text-gray-500">Describe your post idea</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowAI(false)}>
                Cancel
              </Button>
            </div>

            <div className="space-y-4">
              <input
                type="text"
                placeholder="e.g., Monday motivation for entrepreneurs, product launch announcement..."
                value={aiTopic}
                onChange={(e) => setAiTopic(e.target.value)}
                className="w-full px-4 py-3 text-sm bg-white border-2 border-amber-200 rounded-xl focus:outline-none focus:border-amber-500 focus:ring-4 focus:ring-amber-500/10 transition-all"
              />
              <Button
                onClick={handleGenerateCaption}
                loading={generateCaption.isPending}
                className="w-full"
                size="lg"
              >
                <Sparkles className="w-4 h-4" />
                Generate Caption
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-5">
            {/* Content Input */}
            <div className="relative">
              <Textarea
                ref={textareaRef}
                placeholder="What's on your mind? Share something amazing..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={4}
                maxLength={maxLength}
                showCount
                className={cn(
                  "resize-none border-2 border-gray-100 focus:border-amber-500 focus:ring-4 focus:ring-amber-500/10 rounded-xl transition-all",
                  isOverAnyLimit && "border-red-300 focus:border-red-500 focus:ring-red-500/10"
                )}
              />

              {/* Per-platform character limit warnings */}
              {selectedPlatforms.length > 0 && content.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {selectedPlatforms.map(platform => {
                    const limit = PLATFORM_CHAR_LIMITS[platform] || 2200;
                    const isOver = content.length > limit;
                    const remaining = limit - content.length;

                    if (!isOver) return null;

                    return (
                      <div
                        key={platform}
                        className="flex items-center gap-1.5 px-2 py-1 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600"
                      >
                        <AlertCircle className="w-3 h-3" />
                        <PlatformBadge platform={platform} size="sm" />
                        <span className="font-medium">{Math.abs(remaining)} over limit</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Media Preview */}
            {mediaPreview && (
              <div className="relative inline-block">
                <img
                  src={mediaPreview}
                  alt="Preview"
                  className="max-h-40 rounded-xl border-2 border-gray-100"
                />
                <button
                  onClick={removeMedia}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
                {isUploading && (
                  <div className="absolute inset-0 bg-black/50 rounded-xl flex items-center justify-center">
                    <Loader2 className="w-6 h-6 text-white animate-spin" />
                  </div>
                )}
              </div>
            )}

            {/* Schedule Picker */}
            {showSchedule && (
              <div className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-amber-700">
                    <Clock className="w-4 h-4" />
                    <span className="font-semibold text-sm">Schedule Post</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowSchedule(false);
                      setScheduledDate("");
                      setScheduledTime("");
                    }}
                    className="h-6 w-6 p-0 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>

                {/* AI Suggested Times */}
                {selectedPlatforms.length > 0 && suggestions?.suggestions && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-xs text-amber-600">
                      <Zap className="w-3 h-3" />
                      <span className="font-medium">Best times to post</span>
                      {suggestionsLoading && <Loader2 className="w-3 h-3 animate-spin" />}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {/* Collect all unique times, dedupe by datetime, sort by score */}
                      {(() => {
                        const seenTimes = new Set<string>();
                        const allSlots = Object.entries(suggestions.suggestions)
                          .flatMap(([platform, data]) => [
                            { ...data.best_time, platform },
                            ...data.alternative_times.map(s => ({ ...s, platform }))
                          ])
                          .filter(slot => {
                            const timeKey = slot.datetime.slice(0, 16); // Dedupe by date+hour+minute
                            if (seenTimes.has(timeKey)) return false;
                            seenTimes.add(timeKey);
                            return true;
                          })
                          .sort((a, b) => b.score - a.score)
                          .slice(0, 8); // Show up to 8 unique time slots

                        return allSlots.map((slot, idx) => (
                          <button
                            key={idx}
                            onClick={() => applySuggestion(slot.datetime)}
                            className={cn(
                              "px-2.5 py-1 rounded-full text-xs font-medium transition-all hover:scale-105 hover:shadow-sm",
                              slot.score >= 90
                                ? "bg-green-100 text-green-700 ring-1 ring-green-300"
                                : slot.score >= 80
                                ? "bg-blue-50 text-blue-600 ring-1 ring-blue-200"
                                : "bg-white text-gray-600 ring-1 ring-gray-200 hover:ring-amber-300"
                            )}
                            title={`${slot.reason} (${slot.score}% engagement)`}
                          >
                            {slot.score >= 90 && <TrendingUp className="w-3 h-3 inline mr-1" />}
                            {formatSuggestedTime(slot.datetime)}
                          </button>
                        ));
                      })()}
                    </div>
                  </div>
                )}

                {/* Date/Time Picker - Compact */}
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    min={new Date().toISOString().split("T")[0]}
                    className="flex-1 px-3 py-2 bg-white border border-amber-200 rounded-lg focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 text-sm"
                  />
                  <input
                    type="time"
                    value={scheduledTime}
                    onChange={(e) => setScheduledTime(e.target.value)}
                    className="w-28 px-3 py-2 bg-white border border-amber-200 rounded-lg focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 text-sm"
                  />
                  <Button
                    onClick={() => handleSubmit(true)}
                    loading={createPost.isPending}
                    disabled={!content.trim() || selectedPlatforms.length === 0 || !scheduledDate || !scheduledTime || isOverAnyLimit}
                    size="sm"
                    className="px-4"
                  >
                    <Calendar className="w-4 h-4" />
                    Set
                  </Button>
                </div>
              </div>
            )}

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp,video/mp4,video/quicktime,video/webm"
              onChange={handleFileSelect}
              className="hidden"
            />

            {/* Platform Selection */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">
                Select platforms to post:
              </p>
              <div className="flex flex-wrap gap-3">
                {PLATFORMS.map((platform) => {
                  const isConnected = connectedPlatforms.includes(platform);
                  const isSelected = selectedPlatforms.includes(platform);

                  return (
                    <button
                      key={platform}
                      onClick={() => isConnected && togglePlatform(platform)}
                      disabled={!isConnected}
                      className={cn(
                        "relative flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border-2 transition-all duration-200 min-w-[130px]",
                        isSelected
                          ? "border-amber-500 bg-amber-50 shadow-lg shadow-amber-500/10"
                          : "border-gray-200 hover:border-gray-300 bg-white",
                        !isConnected && "opacity-40 cursor-not-allowed grayscale"
                      )}
                    >
                      {isSelected && (
                        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full gradient-primary flex items-center justify-center">
                          <Check className="w-3 h-3 text-white" />
                        </div>
                      )}
                      <PlatformBadge platform={platform} size="sm" showLabel />
                    </button>
                  );
                })}
              </div>
              {connectedPlatforms.length === 0 && (
                <p className="text-sm text-gray-500 bg-gray-50 p-3 rounded-xl">
                  Connect your social accounts in Settings to start posting.
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAI(true)}
                  className="text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                >
                  <Sparkles className="w-4 h-4" />
                  AI Write
                </Button>
                <div className="relative" ref={emojiPickerRef}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                    className={cn(
                      "text-gray-600 hover:text-gray-800 hover:bg-gray-50",
                      showEmojiPicker && "text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                    )}
                  >
                    <Smile className="w-4 h-4" />
                    Emoji
                  </Button>
                  {showEmojiPicker && (
                    <div className="absolute bottom-full left-0 mb-2 z-50">
                      <Picker
                        data={data}
                        onEmojiSelect={handleEmojiSelect}
                        theme="light"
                        previewPosition="none"
                        skinTonePosition="search"
                      />
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className={cn(
                    "text-gray-600 hover:text-gray-800 hover:bg-gray-50",
                    mediaUrls.length > 0 && "text-green-600 hover:text-green-700 hover:bg-green-50"
                  )}
                >
                  {isUploading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Image className="w-4 h-4" />
                  )}
                  {mediaUrls.length > 0 ? "Media Added" : "Media"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSchedule(!showSchedule)}
                  className={cn(
                    "text-gray-600 hover:text-gray-800 hover:bg-gray-50",
                    showSchedule && "text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                  )}
                >
                  <Calendar className="w-4 h-4" />
                  Schedule
                </Button>
              </div>
              {!showSchedule && (
                <Button
                  onClick={() => handleSubmit(false)}
                  loading={createPost.isPending || publishPost.isPending}
                  disabled={!content.trim() || selectedPlatforms.length === 0 || isOverAnyLimit}
                  size="lg"
                >
                  <Send className="w-4 h-4" />
                  Post Now
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
