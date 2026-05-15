import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageSpinner } from "@/components/ui/Spinner";

type Stats = {
  active_sessions:  number;
  total_users:      number;
  total_students:   number;
  total_officers:   number;
  total_citations:  number;
  unpaid_citations: number;
};

function StatCard({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <Card className="text-center py-6">
      <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
      <p className="text-sm font-medium text-gray-600 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </Card>
  );
}

export default function AdminDashboard() {
  const { showToast }         = useToast();
  const navigate              = useNavigate();
  const [stats,    setStats]  = useState<Stats | null>(null);
  const [loading,  setLoading] = useState(true);

  useEffect(() => {
    api.get<Stats>("/admin/stats")
      .then(({ data }) => setStats(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load stats.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Admin Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">System-wide overview and management.</p>
        </div>
      </div>

      {loading && <PageSpinner />}

      {!loading && stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
            <StatCard label="Active Sessions"  value={stats.active_sessions} />
            <StatCard label="Total Users"      value={stats.total_users} />
            <StatCard label="Students"         value={stats.total_students} />
            <StatCard label="Officers"         value={stats.total_officers} />
            <StatCard label="Total Citations"  value={stats.total_citations} />
            <StatCard
              label="Unpaid Citations"
              value={stats.unpaid_citations}
              sub={stats.total_citations > 0
                ? `${Math.round((stats.unpaid_citations / stats.total_citations) * 100)}% outstanding`
                : undefined}
            />
          </div>

          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Management
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { label: "Manage Users",          sub: "View all accounts",                path: "/admin/users" },
              { label: "Review Citations",       sub: "Mark paid, audit violations",      path: "/admin/citations" },
              { label: "Import Students",        sub: "Bulk upload via CSV",              path: "/admin/import" },
            ].map(({ label, sub, path }) => (
              <Card
                key={path}
                className="cursor-pointer hover:border-purple-200 hover:shadow-md transition-shadow"
                onClick={() => navigate(path)}
              >
                <p className="font-semibold text-gray-900">{label}</p>
                <p className="text-sm text-gray-500 mt-0.5">{sub}</p>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
