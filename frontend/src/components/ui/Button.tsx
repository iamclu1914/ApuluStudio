"use client";

import { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline" | "glow";
  size?: "sm" | "md" | "lg" | "icon";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          // Base styles
          "relative inline-flex items-center justify-center font-semibold",
          "transition-all duration-300 ease-out",
          "rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none",
          "active:scale-[0.98]",

          // Variants
          variant === "primary" && [
            "gradient-primary text-white",
            "shadow-lg shadow-amber-500/30",
            "hover:shadow-xl hover:shadow-amber-500/40",
            "hover:scale-[1.02] hover:brightness-110",
            "focus-visible:ring-amber-500",
          ],

          variant === "glow" && [
            "gradient-primary text-white btn-glow",
            "shadow-lg shadow-amber-500/40",
            "hover:shadow-2xl hover:shadow-amber-500/50",
            "hover:scale-[1.03]",
            "focus-visible:ring-amber-500",
          ],

          variant === "secondary" && [
            "bg-white/80 backdrop-blur-sm text-gray-800",
            "border border-gray-200/80",
            "shadow-sm",
            "hover:bg-white hover:border-gray-300 hover:shadow-md",
            "focus-visible:ring-gray-400",
          ],

          variant === "ghost" && [
            "bg-transparent text-gray-600",
            "hover:bg-gray-100/80 hover:text-gray-900",
            "focus-visible:ring-gray-400",
          ],

          variant === "danger" && [
            "bg-gradient-to-br from-red-500 via-red-600 to-rose-600 text-white",
            "shadow-lg shadow-red-500/30",
            "hover:shadow-xl hover:shadow-red-500/40",
            "hover:scale-[1.02] hover:brightness-110",
            "focus-visible:ring-red-500",
          ],

          variant === "outline" && [
            "bg-transparent",
            "border-2 border-gray-200 text-gray-700",
            "hover:border-amber-500 hover:text-amber-600",
            "hover:bg-amber-50/50",
            "focus-visible:ring-amber-500",
          ],

          // Sizes
          size === "sm" && "px-3.5 py-2 text-sm gap-1.5",
          size === "md" && "px-5 py-2.5 text-sm gap-2",
          size === "lg" && "px-7 py-3.5 text-base gap-2.5",
          size === "icon" && "p-2.5 aspect-square",

          className
        )}
        {...props}
      >
        {/* Shimmer effect on hover for primary/glow */}
        {(variant === "primary" || variant === "glow") && (
          <span
            className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none"
            aria-hidden="true"
          >
            <span className="absolute inset-0 -translate-x-full hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          </span>
        )}

        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="opacity-0">{children}</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
