import { useEffect, useState, useCallback } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

interface Stats {
  active_sessions:      number;
  total_sessions_today: number;
  enforcement_checks:   number;
  violations:           number;
}

const AUTO_REFRESH_MS = 10_000;

// ── Stat card ─────────────────────────────────────────────────────────────────

interface StatCardProps {
  label:       string;
  value:       number | undefined;
  accent?:     string;
  subLabel?:   string;
}

function StatCard({ label, value, accent = "text-green-700", subLabel }: StatCardProps) {
  return (
    <Card padding="md">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-4xl font-bold tabular-nums ${accent}`}>{value ?? "—"}</p>
      {subLabel && <p className="text-xs text-gray-400 mt-1">{subLabel}</p>}
    </Card>
  );
}

function StatCardSkeleton() {
  return <div className="bg-white rounded-xl border border-gray-100 shadow-md h-[104px] animate-pulse" />;
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function OperatorDashboard() {
  const { showToast } = useToast();

  const [stats,       setStats]       = useState<Stats | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [hasError,    setHasError]    = useState(false);

  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<Stats>("/operator/stats");
      setStats(data);
      setLastUpdated(new Date());
      setHasError(false);
    } catch (err) {
      setHasError(true);
      showToast("error", getErrorMessage(err, "Failed to load dashboard data."));
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadStats();
    const id = setInterval(loadStats, AUTO_REFRESH_MS);
    return () => clearInterval(id);
  }, [loadStats]);

  const isFirstLoad = loading && stats === null;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          {lastUpdated && (
            <p className="text-xs text-gray-400 mt-0.5">
              Updated {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={loadStats}
          disabled={loading}
        >
          {loading
            ? <><Spinner size="sm" color="border-gray-500" /> Refreshing…</>
            : "Refresh"}
        </Button>
      </div>

      {/* Error banner */}
      {hasError && !loading && stats === null && (
        <Alert variant="error" className="mb-6">
          Could not load dashboard data.{" "}
          <button onClick={loadStats} className="underline font-medium">
            Try again
          </button>
        </Alert>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {isFirstLoad ? (
          Array.from({ length: 4 }, (_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard
              label="Active Sessions"
              value={stats?.active_sessions}
              accent="text-green-700"
            />
            <StatCard
              label="Sessions Today"
              value={stats?.total_sessions_today}
              accent="text-blue-700"
            />
            <StatCard
              label="Enforcement Checks"
              value={stats?.enforcement_checks}
              accent="text-gray-700"
            />
            <StatCard
              label="Violations"
              value={stats?.violations}
              accent="text-red-600"
            />
          </>
        )}
      </div>

      <p className="mt-4 text-xs text-gray-400 text-right">
        Auto-refreshes every {AUTO_REFRESH_MS / 1000}s
      </p>
    </div>
  );
}
