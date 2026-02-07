"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  maxLength?: number;
  showCount?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, maxLength, showCount, value, ...props }, ref) => {
    const charCount = typeof value === "string" ? value.length : 0;

    return (
      <div className="w-full">
        <textarea
          ref={ref}
          value={value}
          maxLength={maxLength}
          className={cn(
            "w-full px-3 py-2 text-sm border rounded-lg bg-white transition-colors resize-none",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder:text-surface-400",
            error
              ? "border-red-500 focus:ring-red-500 focus:border-red-500"
              : "border-surface-300",
            className
          )}
          {...props}
        />
        <div className="flex justify-between mt-1">
          {error && <p className="text-xs text-red-500">{error}</p>}
          {showCount && maxLength && (
            <p
              className={cn(
                "text-xs ml-auto",
                charCount > maxLength * 0.9
                  ? "text-red-500"
                  : "text-surface-400"
              )}
            >
              {charCount}/{maxLength}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = "Textarea";
