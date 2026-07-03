import { Navigate } from "react-router-dom";
import { useAuth, UserRole } from "@/auth/AuthContext";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  roles?: UserRole[];
};

export default function ProtectedRoute({ children, roles }: Props) {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (roles && (!role || !roles.includes(role))) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}