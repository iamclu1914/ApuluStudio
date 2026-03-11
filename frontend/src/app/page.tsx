"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GrowthBanner } from "@/components/analytics/GrowthBanner";
import { ComposeArea } from "@/components/posts/ComposeArea";
import { UpcomingPostsV2 } from "@/components/posts/UpcomingPostsV2";
import { RecentActivityV2 } from "@/components/inbox/RecentActivityV2";
import { Post } from "@/lib/api";
import { getAccessToken } from "@/store/auth";

export default function Dashboard() {
  const router = useRouter();
  const composeRef = useRef<HTMLDivElement>(null);
  const [composeHighlight, setComposeHighlight] = useState(false);
  const [editingPost, setEditingPost] = useState<Post | null>(null);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
    }
  }, [router]);

  const handleEditPost = useCallback((post: Post) => {
    setEditingPost(post);
    composeRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    setComposeHighlight(true);
    setTimeout(() => setComposeHighlight(false), 1500);
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Growth Banner */}
        <section>
          <GrowthBanner />
        </section>

        {/* Compose Area */}
        <section
          ref={composeRef}
          className={
            composeHighlight
              ? "ring-2 ring-primary-500 rounded-xl transition-all"
              : "transition-all"
          }
        >
          <ComposeArea
            editingPost={editingPost}
            onEditComplete={() => setEditingPost(null)}
          />
        </section>

        {/* Bottom split — Upcoming + Activity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <section>
            <UpcomingPostsV2 onEditPost={handleEditPost} />
          </section>
          <section>
            <RecentActivityV2 />
          </section>
        </div>
      </div>
    </DashboardLayout>
  );
}
