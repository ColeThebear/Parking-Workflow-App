import type { ReactNode } from "react";

export type AlertVariant = "success" | "error" | "info" | "warning";

interface AlertProps {
  variant: AlertVariant;
  title?: string;
  children: ReactNode;
  className?: string;
}

const STYLES: Record<AlertVariant, { wrap: string; icon: string; title: string }> = {
  success: {
    wrap:  "bg-green-50 border border-green-200 text-green-800",
    icon:  "text-green-500",
    title: "text-green-900",
  },
  error: {
    wrap:  "bg-red-50 border border-red-200 text-red-800",
    icon:  "text-red-500",
    title: "text-red-900",
  },
  info: {
    wrap:  "bg-blue-50 border border-blue-200 text-blue-800",
    icon:  "text-blue-500",
    title: "text-blue-900",
  },
  warning: {
    wrap:  "bg-amber-50 border border-amber-200 text-amber-800",
    icon:  "text-amber-500",
    title: "text-amber-900",
  },
};

const ICONS: Record<AlertVariant, string> = {
  success: "✓",
  error:   "!",
  info:    "i",
  warning: "⚠",
};

export function Alert({ variant, title, children, className = "" }: AlertProps) {
  const s = STYLES[variant];
  return (
    <div className={`rounded-lg px-4 py-3 text-sm ${s.wrap} ${className}`} role="alert">
      <div className="flex items-start gap-2.5">
        <span className={`shrink-0 mt-0.5 font-bold w-4 text-center ${s.icon}`}>
          {ICONS[variant]}
        </span>
        <div className="flex-1 min-w-0">
          {title && <p className={`font-semibold mb-0.5 ${s.title}`}>{title}</p>}
          <div>{children}</div>
        </div>
      </div>
    </div>
  );
}
