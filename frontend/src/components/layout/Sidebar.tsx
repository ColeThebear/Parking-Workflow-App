import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import type { UserRole, AdminPermission } from "../../auth/AuthContext";
import type { ReactNode } from "react";
import {
  IconDashboard, IconCar, IconClock, IconSearch, IconTicket,
  IconUpload, IconUsers, IconSessions, IconWallet, IconShield,
  IconChevronLeft, IconLogout,
} from "../ui/Icons";

// ── Types ────────────────────────────────────────────────────────────────────

interface NavItem {
  to:    string;
  label: string;
  icon:  ReactNode;
}

// ── Role config ───────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<UserRole, string> = {
  PARKER:      "Student",
  ENFORCEMENT: "Officer",
  OPERATOR:    "Operator",
  ADMIN:       "Admin",
  GUEST:       "Guest",
};

const ROLE_ACCENT: Record<UserRole, string> = {
  PARKER:      "bg-blue-600",
  ENFORCEMENT: "bg-red-600",
  OPERATOR:    "bg-green-700",
  ADMIN:       "bg-purple-700",
  GUEST:       "bg-gray-500",
};

const ROLE_ACTIVE: Record<UserRole, string> = {
  PARKER:      "bg-blue-50 text-blue-700 border-r-2 border-blue-600",
  ENFORCEMENT: "bg-red-50 text-red-700 border-r-2 border-red-600",
  OPERATOR:    "bg-green-50 text-green-800 border-r-2 border-green-700",
  ADMIN:       "bg-purple-50 text-purple-800 border-r-2 border-purple-700",
  GUEST:       "bg-gray-100 text-gray-700 border-r-2 border-gray-500",
};

const PARKER_LINKS: NavItem[] = [
  { to: "/student/start",   label: "Start Parking",   icon: <IconCar /> },
  { to: "/student/active",  label: "Active Session",  icon: <IconClock /> },
  { to: "/student/history", label: "My Sessions",     icon: <IconSessions /> },
  { to: "/student/balance", label: "Balance",         icon: <IconWallet /> },
];

const ENFORCEMENT_LINKS: NavItem[] = [
  { to: "/enforcement",           label: "Plate Lookup", icon: <IconSearch /> },
  { to: "/enforcement/citations", label: "My Citations", icon: <IconTicket /> },
];

const OPERATOR_LINKS: NavItem[] = [
  { to: "/operator",          label: "Dashboard",       icon: <IconDashboard /> },
  { to: "/operator/search",   label: "Student Search",  icon: <IconSearch /> },
  { to: "/operator/sessions", label: "All Sessions",    icon: <IconSessions /> },
  { to: "/operator/import",   label: "Import Students", icon: <IconUpload /> },
];

const GUEST_LINKS: NavItem[] = [
  { to: "/student/start",   label: "Start Parking",   icon: <IconCar /> },
  { to: "/student/active",  label: "Active Session",  icon: <IconClock /> },
  { to: "/student/history", label: "My Sessions",     icon: <IconSessions /> },
  { to: "/student/balance", label: "Balance",         icon: <IconWallet /> },
  { to: "/guest/citations", label: "My Citations",    icon: <IconTicket /> },
];

// Admin nav varies by permission type
const ALL_ADMIN_LINKS: NavItem[] = [
  { to: "/admin",           label: "Dashboard",    icon: <IconDashboard /> },
  { to: "/admin/users",     label: "Users",        icon: <IconUsers /> },
  { to: "/admin/citations", label: "Citations",    icon: <IconTicket /> },
  { to: "/admin/import",    label: "Import",       icon: <IconUpload /> },
];

const ADMIN_PERM_LINKS: Record<AdminPermission, NavItem[]> = {
  full_admin: ALL_ADMIN_LINKS,
  events_admin: [
    { to: "/admin",         label: "Dashboard", icon: <IconDashboard /> },
    { to: "/admin/import",  label: "Import",    icon: <IconUpload /> },
  ],
  citations_admin: [
    { to: "/admin",           label: "Dashboard", icon: <IconDashboard /> },
    { to: "/admin/citations", label: "Citations", icon: <IconTicket /> },
  ],
  reporting_admin: [
    { to: "/admin",       label: "Dashboard", icon: <IconDashboard /> },
    { to: "/admin/users", label: "Users",     icon: <IconUsers /> },
  ],
};

function getLinks(role: UserRole, adminPermission: AdminPermission | null): NavItem[] {
  switch (role) {
    case "PARKER":      return PARKER_LINKS;
    case "ENFORCEMENT": return ENFORCEMENT_LINKS;
    case "OPERATOR":    return OPERATOR_LINKS;
    case "GUEST":       return GUEST_LINKS;
    case "ADMIN":
      return adminPermission
        ? (ADMIN_PERM_LINKS[adminPermission] ?? ALL_ADMIN_LINKS)
        : ALL_ADMIN_LINKS;
    default:            return [];
  }
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

interface SidebarProps {
  collapsed: boolean;
  onToggle:  () => void;
  mobile:    boolean;
  onClose:   () => void;
}

export default function Sidebar({ collapsed, onToggle, mobile, onClose }: SidebarProps) {
  const { role, adminPermission, logout } = useAuth();

  if (!role) return null;

  const links  = getLinks(role, adminPermission);
  const accent = ROLE_ACCENT[role] ?? "bg-gray-600";
  const active = ROLE_ACTIVE[role] ?? "bg-gray-100 text-gray-700";

  const width = collapsed ? "w-[72px]" : "w-60";

  return (
    <>
      {/* Mobile backdrop */}
      {mobile && !collapsed && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      <aside
        className={[
          "flex flex-col bg-white border-r border-gray-200 shadow-sm",
          "transition-all duration-200 ease-in-out",
          "z-50 h-full",
          width,
          mobile ? "fixed inset-y-0 left-0" : "relative",
          mobile && collapsed ? "-translate-x-full" : "translate-x-0",
        ].join(" ")}
      >
        {/* Role badge */}
        <div className={`flex items-center gap-2.5 px-3 py-3.5 ${accent} text-white`}>
          <IconShield className="w-5 h-5 shrink-0" />
          {!collapsed && (
            <span className="text-sm font-semibold truncate">
              {ROLE_LABELS[role]}
              {adminPermission && (
                <span className="block text-xs font-normal text-white/70 capitalize">
                  {adminPermission.replace("_", " ")}
                </span>
              )}
            </span>
          )}
          {/* Collapse toggle — desktop only */}
          <button
            onClick={onToggle}
            className="ml-auto text-white/70 hover:text-white transition-colors hidden md:block"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <IconChevronLeft
              className={`w-4 h-4 transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`}
            />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto py-2">
          {links.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/operator" || to === "/admin" || to === "/enforcement"}
              onClick={mobile ? onClose : undefined}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 px-4 py-2.5 text-sm font-medium",
                  "transition-colors duration-100 relative",
                  isActive
                    ? active
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                ].join(" ")
              }
            >
              <span className="shrink-0">{icon}</span>
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Logout — smaller, tighter */}
        <div className="border-t border-gray-100 p-2">
          <button
            onClick={logout}
            title="Logout"
            className="flex items-center gap-2 w-full px-2 py-1.5 text-xs text-gray-400 hover:text-red-600 transition-colors rounded-md hover:bg-red-50"
          >
            <IconLogout className="w-4 h-4 shrink-0" />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
