import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";

// Public / Auth
import Login           from "@/pages/Login";
import GuestRegister   from "@/pages/guest/Register";

// Student (PARKER / GUEST)
import StartParking    from "@/pages/student/StartParking";
import ActiveSession   from "@/pages/student/ActiveSession";
import StudentHistory  from "@/pages/student/History";
import StudentBalance  from "@/pages/student/Balance";

// Guest-specific
import GuestCitations  from "@/pages/guest/Citations";

// Enforcement
import Lookup          from "@/pages/enforcement/Lookup";
import EnforcementCitations from "@/pages/enforcement/Citations";

// Operator
import OperatorDashboard from "@/pages/operator/Dashboard";
import OperatorSearch  from "@/pages/operator/Search";
import OperatorSessions from "@/pages/operator/Sessions";
import CsvImport       from "@/pages/operator/CsvImport";

// Admin
import AdminDashboard  from "@/pages/admin/Dashboard";
import AdminUsers      from "@/pages/admin/Users";
import AdminCitations  from "@/pages/admin/Citations";
import AdminImport     from "@/pages/admin/Import";

// Shared
import ProtectedRoute  from "@/auth/ProtectedRoute";
import Layout          from "@/components/layout/Layout";

function Unauthorized() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="text-center max-w-sm">
        <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-2xl font-bold">!</span>
        </div>
        <h1 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h1>
        <p className="text-sm text-gray-500 mb-6">
          You don't have permission to view this page.
        </p>
        <button
          onClick={() => navigate("/login", { replace: true })}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Go Back
        </button>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>

        {/* ── Public (no auth required) ────────────────────────── */}
        <Route path="/login"          element={<Login />} />
        <Route path="/guest/register" element={<GuestRegister />} />
        <Route path="/unauthorized"   element={<Unauthorized />} />
        <Route path="/"               element={<Navigate to="/login" replace />} />
        <Route path="*"               element={<Navigate to="/login" replace />} />

        {/* ── Authenticated — Layout shell ─────────────────────── */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          {/* Student / Guest shared */}
          <Route
            path="/student/start"
            element={
              <ProtectedRoute roles={["PARKER", "GUEST"]}>
                <StartParking />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/active"
            element={
              <ProtectedRoute roles={["PARKER", "GUEST"]}>
                <ActiveSession />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/history"
            element={
              <ProtectedRoute roles={["PARKER", "GUEST"]}>
                <StudentHistory />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/balance"
            element={
              <ProtectedRoute roles={["PARKER", "GUEST"]}>
                <StudentBalance />
              </ProtectedRoute>
            }
          />

          {/* Guest-only */}
          <Route
            path="/guest/citations"
            element={
              <ProtectedRoute roles={["GUEST"]}>
                <GuestCitations />
              </ProtectedRoute>
            }
          />

          {/* Enforcement */}
          <Route
            path="/enforcement"
            element={
              <ProtectedRoute roles={["ENFORCEMENT"]}>
                <Lookup />
              </ProtectedRoute>
            }
          />
          <Route
            path="/enforcement/citations"
            element={
              <ProtectedRoute roles={["ENFORCEMENT"]}>
                <EnforcementCitations />
              </ProtectedRoute>
            }
          />

          {/* Operator */}
          <Route
            path="/operator"
            element={
              <ProtectedRoute roles={["OPERATOR"]}>
                <OperatorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operator/search"
            element={
              <ProtectedRoute roles={["OPERATOR"]}>
                <OperatorSearch />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operator/sessions"
            element={
              <ProtectedRoute roles={["OPERATOR"]}>
                <OperatorSessions />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operator/import"
            element={
              <ProtectedRoute roles={["OPERATOR"]}>
                <CsvImport />
              </ProtectedRoute>
            }
          />

          {/* Admin */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={["ADMIN"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute roles={["ADMIN"]}>
                <AdminUsers />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/citations"
            element={
              <ProtectedRoute roles={["ADMIN"]}>
                <AdminCitations />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/import"
            element={
              <ProtectedRoute roles={["ADMIN"]}>
                <AdminImport />
              </ProtectedRoute>
            }
          />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}
