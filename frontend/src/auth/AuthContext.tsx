import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from "react";
import axios from "axios";

function getCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

export type UserRole = "PARKER" | "OPERATOR" | "ENFORCEMENT" | "ADMIN" | "GUEST";

export type AdminPermission =
  | "full_admin"
  | "events_admin"
  | "citations_admin"
  | "reporting_admin";

type AuthState = {
  role:            UserRole | null;
  adminPermission: AdminPermission | null;
  isAuthenticated: boolean;
  login: (role: UserRole, adminPermission?: string | null) => void;
  logout: () => void;
};

// Only non-sensitive metadata lives in localStorage.
// Tokens are in HttpOnly cookies — JS never reads them.
const STORAGE_KEYS = {
  role:            "auth_role",
  adminPermission: "auth_admin_permission",
} as const;

const VALID_ROLES: UserRole[] = ["PARKER", "OPERATOR", "ENFORCEMENT", "ADMIN", "GUEST"];
const VALID_ADMIN_PERMS: AdminPermission[] = [
  "full_admin", "events_admin", "citations_admin", "reporting_admin",
];

function parseRole(value: string | null): UserRole | null {
  if (value && (VALID_ROLES as string[]).includes(value)) return value as UserRole;
  return null;
}

function parseAdminPerm(value: string | null): AdminPermission | null {
  if (value && (VALID_ADMIN_PERMS as string[]).includes(value)) return value as AdminPermission;
  return null;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole | null>(
    () => parseRole(localStorage.getItem(STORAGE_KEYS.role))
  );
  const [adminPermission, setAdminPermission] = useState<AdminPermission | null>(
    () => parseAdminPerm(localStorage.getItem(STORAGE_KEYS.adminPermission))
  );

  const login = useCallback((newRole: UserRole, newAdminPerm?: string | null) => {
    localStorage.setItem(STORAGE_KEYS.role, newRole);
    const perm = parseAdminPerm(newAdminPerm ?? null);
    if (perm) {
      localStorage.setItem(STORAGE_KEYS.adminPermission, perm);
    } else {
      localStorage.removeItem(STORAGE_KEYS.adminPermission);
    }
    setRole(newRole);
    setAdminPermission(perm);
  }, []);

  // Ensure the CSRF cookie exists whenever the user is authenticated.
  // The backend sets it on any response, but if the user has a session from
  // a previous visit (role in localStorage) there may have been no backend
  // request yet in this browser session.
  useEffect(() => {
    if (role) {
      axios
        .get("/api/v1/auth/csrf-token", { withCredentials: true })
        .catch(() => {});
    }
  }, [role]);

  const logout = useCallback(async () => {
    try {
      await axios.post("/api/v1/auth/logout", {}, {
        withCredentials: true,
        headers: { "X-CSRF-Token": getCsrfToken() },
      });
    } catch {
      // Even if the request fails, clear local state so the UI shows logged-out.
    }
    localStorage.removeItem(STORAGE_KEYS.role);
    localStorage.removeItem(STORAGE_KEYS.adminPermission);
    setRole(null);
    setAdminPermission(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ role, adminPermission, isAuthenticated: !!role, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
