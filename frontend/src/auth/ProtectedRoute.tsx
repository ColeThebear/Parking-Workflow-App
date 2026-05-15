// This file defines the ProtectedRoute component, which is used to protect routes that require authentication and specific user roles.
import { Navigate } from "react-router-dom";
import { useAuth, UserRole } from "@/auth/AuthContext";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  roles?: UserRole[];
};

export default function ProtectedRoute({ children, roles }: Props) {
  const { token, role } = useAuth();

  if (!token) return <Navigate to="/login" replace />;

  // If a role allowlist is specified, the user's role must be present and valid.
  // Handles the edge case where token exists but role failed to hydrate.
  if (roles && (!role || !roles.includes(role))) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}