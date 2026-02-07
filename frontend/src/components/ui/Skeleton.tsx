"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  variant?: "text" | "circular" | "rectangular" | "card";
  width?: string | number;
  height?: string | number;
  className?: string;
}

export function Skeleton({
  variant = "text",
  width,
  height,
  className,
}: SkeletonProps) {
  const style: React.CSSProperties = {};

  if (width) {
    style.width = typeof width === "number" ? `${width}px` : width;
  }
  if (height) {
    style.height = typeof height === "number" ? `${height}px` : height;
  }

  return (
    <div
      className={cn(
        "animate-pulse bg-gray-200",
        variant === "text" && "h-4 rounded",
        variant === "circular" && "rounded-full aspect-square",
        variant === "rectangular" && "rounded-lg",
        variant === "card" && "rounded-2xl h-32",
        variant === "text" && !width && "w-full",
        className
      )}
      style={style}
      aria-hidden="true"
    />
  );
}
