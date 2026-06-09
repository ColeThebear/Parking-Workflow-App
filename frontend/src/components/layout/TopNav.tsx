import { useAuth } from "../../auth/AuthContext";
import { IconMenu } from "../ui/Icons";

interface TopNavProps {
  onMenuClick: () => void;
}

export default function TopNav({ onMenuClick }: TopNavProps) {
  const { role } = useAuth();

  return (
    <header className="h-12 bg-white border-b border-gray-200 flex items-center px-4 gap-3 shrink-0 shadow-sm z-30">
      {/* Hamburger — visible on mobile, also desktop collapse toggle */}
      <button
        onClick={onMenuClick}
        className="text-gray-500 hover:text-gray-800 transition-colors"
        aria-label="Toggle sidebar"
      >
        <IconMenu />
      </button>

      {/* Brand */}
      <span className="font-bold text-gray-900 tracking-wide select-none">
        A&amp;C Parking
      </span>

      {/* Role pill */}
      {role && (
        <span className="ml-auto text-xs text-gray-400 font-medium">
          {role}
        </span>
      )}
    </header>
  );
}
