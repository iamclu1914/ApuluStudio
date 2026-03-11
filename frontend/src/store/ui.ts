import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIStore {
  upcomingView: "calendar" | "queue";
  setUpcomingView: (v: "calendar" | "queue") => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      upcomingView: "queue",
      setUpcomingView: (v) => set({ upcomingView: v }),
    }),
    { name: "apulu-ui" }
  )
);
