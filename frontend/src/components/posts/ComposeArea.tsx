"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Image, Calendar, Send, X, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { postsApi, accountsApi, Post } from "@/lib/api";
import { cn } from "@/lib/utils";

const PLATFORMS = [
  { id: "instagram", label: "IG", color: "#E1306C" },
  { id: "tiktok", label: "TK", color: "#FF0050" },
  { id: "x", label: "X", color: "#1D9BF0" },
  // Threads: border-only to avoid invisible black-on-white issue
  { id: "threads", label: "TH", color: "currentColor", borderOnly: true },
  { id: "bluesky", label: "BS", color: "#0085FF" },
];

const CHAR_LIMIT_WITH_X = 280;
const CHAR_LIMIT_DEFAULT = 2200;

function getCharLimit(selectedPlatforms: string[]) {
  return selectedPlatforms.includes("x") ? CHAR_LIMIT_WITH_X : CHAR_LIMIT_DEFAULT;
}

function CharCounter({ count, limit }: { count: number; limit: number }) {
  const pct = count / limit;
  const color =
    pct >= 1
      ? "text-red-500"
      : pct >= 0.9
      ? "text-amber-500"
      : "text-surface-400 dark:text-surface-500";
  return (
    <span className={cn("text-xs font-mono", color)}>
      {count}/{limit}
    </span>
  );
}

export function ComposeArea({
  editingPost,
  onEditComplete,
}: {
  editingPost?: Post | null;
  onEditComplete?: () => void;
}) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [content, setContent] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [scheduledAt, setScheduledAt] = useState<string>("");
  const [mediaFiles, setMediaFiles] = useState<File[]>([]);
  const [mediaPreviews, setMediaPreviews] = useState<string[]>([]);

  // Pre-fill when editing a post
  useEffect(() => {
    if (editingPost) {
      setContent(editingPost.content);
      setSelectedPlatforms(
        editingPost.platforms.map((pp) => pp.platform.toLowerCase())
      );
      setScheduledAt(editingPost.scheduled_at?.slice(0, 16) ?? "");
      // Media files cannot be reconstructed from URLs — clear silently
      setMediaFiles([]);
      setMediaPreviews([]);
    }
  }, [editingPost]);

  const charLimit = getCharLimit(selectedPlatforms);
  const isScheduled = scheduledAt !== "";

  const { data: accounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => accountsApi.list().then((r) => r.data),
  });

  const connectedPlatforms = accounts?.map((a) => a.platform.toLowerCase()) ?? [];

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    const allConnected = PLATFORMS.filter((p) =>
      connectedPlatforms.includes(p.id)
    ).map((p) => p.id);
    setSelectedPlatforms(
      selectedPlatforms.length === allConnected.length ? [] : allConnected
    );
  };

  const handleMediaChange = (files: FileList | null) => {
    if (!files) return;
    let arr = Array.from(files);

    const isVideo = (f: File) => f.type.startsWith("video/");
    const hasVideo = arr.some(isVideo);
    const hasImage = arr.some((f) => !isVideo(f));

    // X constraint: max 4 images OR 1 video, no mixing
    if (selectedPlatforms.includes("x")) {
      if (hasVideo && hasImage) {
        toast.error("X doesn't support mixing images and video. Please pick one.");
        return;
      }
      if (hasVideo && arr.length > 1) {
        arr = [arr.find(isVideo)!];
        toast("Only 1 video allowed for X — keeping the first one.");
      }
    }

    arr = arr.slice(0, 4);
    setMediaFiles(arr);
    setMediaPreviews(arr.map((f) => URL.createObjectURL(f)));
  };

  const removeMedia = (i: number) => {
    setMediaFiles((prev) => prev.filter((_, idx) => idx !== i));
    setMediaPreviews((prev) => prev.filter((_, idx) => idx !== i));
  };

  // TikTok video warning
  const tiktokVideoWarning =
    selectedPlatforms.includes("tiktok") &&
    mediaFiles.length > 0 &&
    mediaFiles.every((f) => !f.type.startsWith("video/"));

  const createPost = useMutation({
    mutationFn: async () => {
      let mediaUrls: string[] = [];
      if (mediaFiles.length > 0) {
        for (const file of mediaFiles) {
          const res = await postsApi.upload(file);
          mediaUrls.push(res.data.url);
        }
      }
      return postsApi.create({
        content: content.trim(),
        platforms: selectedPlatforms,
        scheduled_at: scheduledAt || undefined,
        media_urls: mediaUrls.length > 0 ? mediaUrls : undefined,
      });
    },
    onSuccess: () => {
      const msg = isScheduled
        ? `Scheduled for ${new Date(scheduledAt).toLocaleString()}`
        : "Posted!";
      toast.success(msg);
      setContent("");
      setSelectedPlatforms([]);
      setScheduledAt("");
      setMediaFiles([]);
      setMediaPreviews([]);
      onEditComplete?.();
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to post");
    },
  });

  const canSubmit =
    content.trim().length > 0 &&
    selectedPlatforms.length > 0 &&
    content.length <= charLimit;

  return (
    <Card>
      <CardContent className="space-y-4">
        {/* Platform toggles */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-medium text-surface-500 dark:text-surface-400">
            Post to:
          </span>
          {PLATFORMS.map((p) => {
            const isConnected = connectedPlatforms.includes(p.id);
            const isSelected = selectedPlatforms.includes(p.id);
            const isThreads = p.id === "threads";

            return (
              <button
                key={p.id}
                onClick={() => isConnected && togglePlatform(p.id)}
                disabled={!isConnected}
                style={
                  isSelected && !isThreads
                    ? { borderColor: p.color, backgroundColor: `${p.color}15` }
                    : {}
                }
                className={cn(
                  "px-3 py-1 rounded-full border text-xs font-semibold transition-all",
                  isSelected && !isThreads
                    ? "text-surface-900 dark:text-surface-50"
                    : isSelected && isThreads
                    ? "border-surface-900 dark:border-surface-100 text-surface-900 dark:text-surface-100 bg-surface-100 dark:bg-dark-border"
                    : "border-surface-200 dark:border-dark-border text-surface-400 hover:border-surface-300 dark:hover:border-surface-500",
                  !isConnected && "opacity-40 cursor-not-allowed"
                )}
              >
                {p.label}
              </button>
            );
          })}
          <button
            onClick={toggleAll}
            className="px-2 py-1 text-xs text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 underline"
          >
            {selectedPlatforms.length === connectedPlatforms.length ? "None" : "All"}
          </button>
        </div>

        {/* Caption textarea */}
        <div className="relative">
          <textarea
            placeholder="What's on your mind, Vawn?"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
            className={cn(
              "w-full px-3 py-2.5 text-sm rounded-lg border resize-none",
              "border-surface-200 dark:border-dark-border",
              "bg-white dark:bg-dark-bg",
              "text-surface-900 dark:text-surface-50",
              "placeholder:text-surface-400 dark:placeholder:text-surface-600",
              "focus:outline-none focus:ring-2 focus:ring-primary-500",
              content.length > charLimit && "ring-2 ring-red-500 border-red-500"
            )}
          />
          <div className="absolute bottom-2 right-3">
            <CharCounter count={content.length} limit={charLimit} />
          </div>
        </div>

        {/* Media previews */}
        {mediaPreviews.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {mediaPreviews.map((src, i) => (
              <div
                key={i}
                className="relative w-20 h-20 rounded-lg overflow-hidden border border-surface-200 dark:border-dark-border"
              >
                <img src={src} alt="" className="w-full h-full object-cover" />
                <button
                  onClick={() => removeMedia(i)}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 flex items-center justify-center"
                >
                  <X className="w-3 h-3 text-white" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* TikTok video warning */}
        {tiktokVideoWarning && (
          <p className="text-xs text-amber-500 text-center">
            TikTok requires a video — your current media is images only.
          </p>
        )}

        {/* Toolbar + CTA */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime"
              multiple
              className="hidden"
              onChange={(e) => handleMediaChange(e.target.files)}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-surface-500 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-dark-border transition-colors"
            >
              <Image className="w-4 h-4" />
              <span className="hidden sm:inline">Media</span>
            </button>

            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-surface-500 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-dark-border transition-colors">
              <Calendar className="w-4 h-4" />
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                className="hidden sm:block bg-transparent text-xs text-surface-500 dark:text-surface-400 focus:outline-none cursor-pointer"
                min={new Date().toISOString().slice(0, 16)}
              />
              <span className="sm:hidden">Schedule</span>
            </div>
          </div>

          <Button
            onClick={() => createPost.mutate()}
            disabled={!canSubmit || createPost.isPending}
            className="gap-1.5"
          >
            {createPost.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {isScheduled ? "Schedule Post" : "Post Now"}
          </Button>
        </div>

        {connectedPlatforms.length === 0 && (
          <p className="text-xs text-surface-400 dark:text-surface-500 text-center">
            Connect your accounts in Settings to start posting.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
