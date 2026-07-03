import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export const PrivateRoute = ({
  children,
  roles,
}: {
  children: React.ReactElement;
  roles?: string[];
}) => {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (roles && role && !roles.includes(role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};