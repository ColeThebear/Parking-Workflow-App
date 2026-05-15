import type { ReactNode, HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: "sm" | "md" | "lg";
}

const PADDING = { sm: "p-4", md: "p-6", lg: "p-8" };

export function Card({ children, padding = "md", className = "", ...props }: CardProps) {
  return (
    <div
      className={`bg-white rounded-xl shadow-md border border-gray-100 ${PADDING[padding]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardRowProps {
  label: string;
  value: ReactNode;
}

/** Horizontal label/value row used inside detail cards. */
export function CardRow({ label, value }: CardRowProps) {
  return (
    <div className="flex justify-between items-center py-2.5 text-sm border-b border-gray-100 last:border-0">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className="font-medium text-gray-900 text-right ml-4">{value}</span>
    </div>
  );
}
