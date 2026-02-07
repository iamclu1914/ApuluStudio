"use client";

import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "glass" | "gradient" | "elevated" | "outline" | "glow";
  hover?: boolean;
  interactive?: boolean;
}

export function Card({
  className,
  variant = "default",
  hover = false,
  interactive = false,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        // Base styles
        "rounded-2xl transition-all duration-300 overflow-hidden",

        // Variants
        variant === "default" && [
          "bg-white/90 backdrop-blur-sm",
          "border border-gray-100/80",
          "shadow-lg shadow-black/[0.03]",
        ],

        variant === "glass" && [
          "glass-card",
        ],

        variant === "elevated" && [
          "bg-white",
          "border border-gray-100/60",
          "shadow-xl shadow-black/[0.06]",
        ],

        variant === "gradient" && [
          "gradient-primary border-0 text-white",
          "shadow-lg shadow-amber-500/20",
        ],

        variant === "outline" && [
          "bg-transparent",
          "border-2 border-dashed border-gray-200",
          "hover:border-amber-400 hover:bg-amber-50/30",
        ],

        variant === "glow" && [
          "bg-white/95 backdrop-blur-sm",
          "border border-amber-200/50",
          "shadow-lg shadow-amber-500/10",
          "hover:shadow-xl hover:shadow-amber-500/20",
          "hover:border-amber-300/70",
        ],

        // Hover effect
        hover && "card-hover",

        // Interactive (clickable) style
        interactive && "card-interactive cursor-pointer",

        className
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-4 py-4 sm:px-6 sm:py-5",
        "border-b border-gray-100/60",
        className
      )}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-lg font-semibold text-gray-900",
        "font-display tracking-tight",
        className
      )}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        "text-sm text-gray-500 mt-1.5",
        "leading-relaxed",
        className
      )}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("px-4 py-4 sm:px-6 sm:py-5", className)}
      {...props}
    />
  );
}


