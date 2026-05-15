import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { useToast } from "@/components/ToastProvider";
import api, { getErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/Input";
import type { UserRole } from "@/auth/AuthContext";

const ROLE_REDIRECTS: Record<UserRole, string> = {
  PARKER:      "/student/start",
  ENFORCEMENT: "/enforcement",
  OPERATOR:    "/operator",
  ADMIN:       "/admin",
  GUEST:       "/student/start",
};

type LoginResponse = {
  access_token:           string;
  role:                   UserRole;
  terminated_by_operator: boolean;
  admin_permission:       string | null;
};

export default function Login() {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!email || !password) {
      showToast("error", "Please enter both email and password.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post<LoginResponse>("/auth/login", { email, password });

      login(data.access_token, data.role, data.admin_permission);

      const destination = ROLE_REDIRECTS[data.role];
      if (!destination) {
        showToast("error", `Unrecognized role: ${data.role}`);
        return;
      }

      showToast("success", "Login successful.");

      navigate(destination, {
        replace: true,
        state: data.terminated_by_operator ? { terminatedByOperator: true } : undefined,
      });
    } catch (err) {
      showToast("error", getErrorMessage(err, "Login failed. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-700 mb-4">
            <span className="text-white text-2xl font-bold">P</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">SUNY Parking</h1>
          <p className="text-sm text-gray-500 mt-1">
            Sign in to manage parking, enforcement, or operations.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <TextInput
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              placeholder="you@suny.edu"
            />

            <TextInput
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              placeholder="••••••••"
            />

            <Button
              type="submit"
              loading={loading}
              fullWidth
              className="mt-1"
            >
              {loading ? "Signing in…" : "Sign In"}
            </Button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400">or</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Guest sign-in */}
          <Button
            variant="secondary"
            fullWidth
            onClick={() => navigate("/guest/register")}
            disabled={loading}
          >
            Sign in as Guest
          </Button>
        </div>
      </div>
    </div>
  );
}
