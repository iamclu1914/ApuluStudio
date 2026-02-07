"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className="w-full">
        <input
          ref={ref}
          className={cn(
            "w-full px-3 py-2 text-sm border rounded-lg bg-white transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
            "placeholder:text-surface-400",
            error
              ? "border-red-500 focus:ring-red-500 focus:border-red-500"
              : "border-surface-300",
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
