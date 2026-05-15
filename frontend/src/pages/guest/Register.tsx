import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { useToast } from "@/components/ToastProvider";
import api, { getErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/Input";
import type { UserRole } from "@/auth/AuthContext";

type GuestRegisterResponse = {
  access_token: string;
  role:         UserRole;
};

export default function GuestRegister() {
  const { login }      = useAuth();
  const { showToast }  = useToast();
  const navigate       = useNavigate();

  const [name,    setName]    = useState("");
  const [email,   setEmail]   = useState("");
  const [plate,   setPlate]   = useState("");
  const [pass,    setPass]    = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !pass) {
      showToast("error", "Name, email, and password are required.");
      return;
    }
    if (pass !== confirm) {
      showToast("error", "Passwords do not match.");
      return;
    }
    if (pass.length < 6) {
      showToast("error", "Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post<GuestRegisterResponse>("/auth/guest-register", {
        name:          name.trim(),
        email:         email.trim().toLowerCase(),
        password:      pass,
        license_plate: plate.trim().toUpperCase() || null,
      });
      login(data.access_token, data.role);
      showToast("success", "Guest account created. Welcome!");
      navigate("/student/start", { replace: true });
    } catch (err) {
      showToast("error", getErrorMessage(err, "Registration failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gray-500 mb-4">
            <span className="text-white text-2xl font-bold">G</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Guest Account</h1>
          <p className="text-sm text-gray-500 mt-1">
            Create a guest account to start parking.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <TextInput
              label="Full Name *"
              placeholder="Jane Smith"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
              autoFocus
            />
            <TextInput
              label="Email *"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
            />
            <TextInput
              label="License Plate"
              placeholder="ABC1234"
              value={plate}
              onChange={(e) => setPlate(e.target.value.toUpperCase())}
              disabled={loading}
              className="uppercase tracking-widest"
              hint="Optional — required to start a parking session"
            />
            <TextInput
              label="Password *"
              type="password"
              placeholder="Min. 6 characters"
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              disabled={loading}
              autoComplete="new-password"
            />
            <TextInput
              label="Confirm Password *"
              type="password"
              placeholder="Repeat password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              disabled={loading}
              autoComplete="new-password"
            />

            <Button type="submit" loading={loading} fullWidth className="mt-1">
              {loading ? "Creating account…" : "Create Guest Account"}
            </Button>
          </form>

          {/* Back to login */}
          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{" "}
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="text-blue-600 hover:underline font-medium"
              disabled={loading}
            >
              Sign in
            </button>
          </p>

          {/* Expiry notice */}
          <p className="text-xs text-gray-400 text-center mt-3">
            Guest accounts expire each August. Contact the parking office to renew.
          </p>
        </div>
      </div>
    </div>
  );
}
