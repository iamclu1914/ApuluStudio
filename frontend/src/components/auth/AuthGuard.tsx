"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCurrentUser, getAccessToken, AuthUser } from "@/store/auth";
import { Loader2 } from "lucide-react";

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function check() {
      const token = getAccessToken();
      if (!token) {
        router.replace("/login");
        return;
      }

      const currentUser = await fetchCurrentUser();
      if (!currentUser) {
        router.replace("/login");
        return;
      }

      setUser(currentUser);
      setChecking(false);
    }

    check();
  }, [router]);

  if (checking || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
