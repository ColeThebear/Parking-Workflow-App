export type BadgeVariant = "active" | "ended" | "terminated" | "neutral";

interface BadgeProps {
  variant: BadgeVariant;
  label?: string;
  className?: string;
}

const STYLES: Record<BadgeVariant, string> = {
  active:     "bg-green-100 text-green-800 border border-green-200",
  ended:      "bg-gray-100  text-gray-600  border border-gray-200",
  terminated: "bg-red-100   text-red-700   border border-red-200",
  neutral:    "bg-blue-100  text-blue-800  border border-blue-200",
};

const LABELS: Record<BadgeVariant, string> = {
  active:     "Active",
  ended:      "Ended",
  terminated: "Terminated",
  neutral:    "Info",
};

const DOTS: Record<BadgeVariant, string> = {
  active:     "bg-green-500",
  ended:      "bg-gray-400",
  terminated: "bg-red-500",
  neutral:    "bg-blue-500",
};

export function Badge({ variant, label, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${STYLES[variant]} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${DOTS[variant]}`} />
      {label ?? LABELS[variant]}
    </span>
  );
}
