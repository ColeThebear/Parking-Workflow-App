import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

export type UserRole = "PARKER" | "OPERATOR" | "ENFORCEMENT" | "ADMIN" | "GUEST";

/** Admin sub-permission — only defined when role === "ADMIN". */
export type AdminPermission =
  | "full_admin"
  | "events_admin"
  | "citations_admin"
  | "reporting_admin";

type AuthState = {
  token:           string | null;
  role:            UserRole | null;
  adminPermission: AdminPermission | null;
  isAuthenticated: boolean;
  login: (token: string, role: UserRole, adminPermission?: string | null) => void;
  logout: () => void;
};

// Keys must match what api/client.ts reads from localStorage
const STORAGE_KEYS = {
  token:           "auth_token",
  role:            "auth_role",
  adminPermission: "auth_admin_permission",
} as const;

const VALID_ROLES: UserRole[] = ["PARKER", "OPERATOR", "ENFORCEMENT", "ADMIN", "GUEST"];
const VALID_ADMIN_PERMS: AdminPermission[] = [
  "full_admin", "events_admin", "citations_admin", "reporting_admin",
];

function parseRole(value: string | null): UserRole | null {
  if (value && (VALID_ROLES as string[]).includes(value)) {
    return value as UserRole;
  }
  return null;
}

function parseAdminPerm(value: string | null): AdminPermission | null {
  if (value && (VALID_ADMIN_PERMS as string[]).includes(value)) {
    return value as AdminPermission;
  }
  return null;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEYS.token)
  );
  const [role, setRole] = useState<UserRole | null>(
    () => parseRole(localStorage.getItem(STORAGE_KEYS.role))
  );
  const [adminPermission, setAdminPermission] = useState<AdminPermission | null>(
    () => parseAdminPerm(localStorage.getItem(STORAGE_KEYS.adminPermission))
  );

  const login = useCallback((newToken: string, newRole: UserRole, newAdminPerm?: string | null) => {
    localStorage.setItem(STORAGE_KEYS.token, newToken);
    localStorage.setItem(STORAGE_KEYS.role, newRole);
    const perm = parseAdminPerm(newAdminPerm ?? null);
    if (perm) {
      localStorage.setItem(STORAGE_KEYS.adminPermission, perm);
    } else {
      localStorage.removeItem(STORAGE_KEYS.adminPermission);
    }
    setToken(newToken);
    setRole(newRole);
    setAdminPermission(perm);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.role);
    localStorage.removeItem(STORAGE_KEYS.adminPermission);
    setToken(null);
    setRole(null);
    setAdminPermission(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, role, adminPermission, isAuthenticated: !!token, login, logout }}
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
