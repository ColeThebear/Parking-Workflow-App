interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  color?: string;
  className?: string;
}

const SIZES = { sm: "w-4 h-4 border-2", md: "w-6 h-6 border-2", lg: "w-10 h-10 border-[3px]" };

export function Spinner({ size = "md", color = "border-blue-600", className = "" }: SpinnerProps) {
  return (
    <span
      className={`inline-block rounded-full border-t-transparent animate-spin ${SIZES[size]} ${color} ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
}

export function PageSpinner() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
}
