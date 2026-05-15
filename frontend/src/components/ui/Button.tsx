import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "danger" | "secondary" | "success";
export type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: ReactNode;
  fullWidth?: boolean;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:   "bg-blue-600 text-white shadow-sm hover:bg-blue-700 focus-visible:ring-blue-500 disabled:bg-blue-300",
  danger:    "bg-red-600 text-white shadow-sm hover:bg-red-700 focus-visible:ring-red-500 disabled:bg-red-300",
  secondary: "bg-white text-gray-700 border border-gray-300 shadow-sm hover:bg-gray-50 focus-visible:ring-gray-400 disabled:text-gray-400",
  success:   "bg-green-600 text-white shadow-sm hover:bg-green-700 focus-visible:ring-green-500 disabled:bg-green-300",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  fullWidth = false,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium",
        "transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed disabled:opacity-60",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        fullWidth ? "w-full" : "",
        className,
      ].join(" ")}
      {...props}
    >
      {loading && (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0" />
      )}
      {children}
    </button>
  );
}
