import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

// Exported so other files can import the role type directly
export type UserRole = "PARKER" | "OPERATOR" | "ENFORCEMENT";

type AuthState = {
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  login: (token: string, role: UserRole) => void;
  logout: () => void;
};

const STORAGE_KEYS = {
  token: "auth_token",
  role: "auth_role",
} as const;

const VALID_ROLES: UserRole[] = ["PARKER", "OPERATOR", "ENFORCEMENT"];

function parseRole(value: string | null): UserRole | null {
  if (value && (VALID_ROLES as string[]).includes(value)) {
    return value as UserRole;
  }
  return null;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Lazy initializers run once on mount — localStorage is synchronous,
  // so there is no loading flash or async gap before the state is ready.
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEYS.token)
  );
  const [role, setRole] = useState<UserRole | null>(
    () => parseRole(localStorage.getItem(STORAGE_KEYS.role))
  );

  const login = useCallback((newToken: string, newRole: UserRole) => {
    localStorage.setItem(STORAGE_KEYS.token, newToken);
    localStorage.setItem(STORAGE_KEYS.role, newRole);
    setToken(newToken);
    setRole(newRole);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.role);
    setToken(null);
    setRole(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, role, isAuthenticated: !!token, login, logout }}
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