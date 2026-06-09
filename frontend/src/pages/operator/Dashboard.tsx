import { useEffect, useState, useCallback } from "react";
import Plot from "react-plotly.js";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

// ── Types ─────────────────────────────────────────────────────────────────────

interface Stats {
  active_sessions:      number;
  total_sessions_today: number;
  enforcement_checks:   number;
  violations:           number;
}

interface DayCount  { date: string; count: number }
interface ZoneCount { zone: string; count: number }
interface TypeCount { type: string; count: number }
interface EnfCount  { status: string; count: number }

interface ChartData {
  sessions_per_day: {
    live:     DayCount[];
    historic: DayCount[];
  };
  sessions_by_zone:          ZoneCount[];
  user_type_distribution:    TypeCount[];
  payment_distribution:      TypeCount[];
  enforcement_distribution:  EnfCount[];
  session_type_distribution: TypeCount[];
}

const AUTO_REFRESH_MS = 10_000;

// ── Colour palette (green-themed, matches operator role) ──────────────────────

const C = {
  green:   "#15803d",
  teal:    "#0d9488",
  blue:    "#1d4ed8",
  amber:   "#d97706",
  red:     "#dc2626",
  purple:  "#7c3aed",
  gray:    "#6b7280",
  gridLine:"#f3f4f6",
};

const PLOTLY_BASE = {
  paper_bgcolor: "white",
  plot_bgcolor:  "white",
  font:          { family: "Inter, system-ui, sans-serif", size: 12, color: "#374151" },
  margin:        { l: 40, r: 16, t: 32, b: 40 },
  xaxis:         { gridcolor: C.gridLine, linecolor: C.gridLine },
  yaxis:         { gridcolor: C.gridLine, linecolor: C.gridLine },
  showlegend:    true,
  legend:        { orientation: "h" as const, x: 0, y: -0.2 },
  autosize:      true,
};

const PLOTLY_CONFIG = { displayModeBar: false, responsive: true };

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({
  label, value, accent = "text-green-700", subLabel,
}: {
  label: string; value: number | undefined; accent?: string; subLabel?: string;
}) {
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

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card padding="md">
      <p className="text-sm font-semibold text-gray-700 mb-3">{title}</p>
      {children}
    </Card>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function OperatorDashboard() {
  const { showToast } = useToast();

  const [stats,       setStats]       = useState<Stats | null>(null);
  const [chartData,   setChartData]   = useState<ChartData | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [hasError,    setHasError]    = useState(false);

  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, chartRes] = await Promise.all([
        api.get<Stats>("/operator/stats"),
        api.get<ChartData>("/operator/chart-data"),
      ]);
      setStats(statsRes.data);
      setChartData(chartRes.data);
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

  // ── Chart traces ────────────────────────────────────────────────────────────

  const sessionsPerDayTraces = chartData ? [
    {
      x:    chartData.sessions_per_day.live.map((d) => d.date),
      y:    chartData.sessions_per_day.live.map((d) => d.count),
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Live",
      line: { color: C.green, width: 2 },
      marker: { color: C.green, size: 5 },
    },
    {
      x:    chartData.sessions_per_day.historic.map((d) => d.date),
      y:    chartData.sessions_per_day.historic.map((d) => d.count),
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "Historic",
      line: { color: C.blue, width: 2, dash: "dot" as const },
      marker: { color: C.blue, size: 5 },
    },
  ] : [];

  const zoneTraces = chartData ? [{
    x:           chartData.sessions_by_zone.map((z) => z.zone),
    y:           chartData.sessions_by_zone.map((z) => z.count),
    type:        "bar" as const,
    name:        "Sessions",
    marker:      { color: C.teal },
    showlegend:  false,
  }] : [];

  const userTypePie = chartData ? [{
    labels:   chartData.user_type_distribution.map((u) => u.type.charAt(0) + u.type.slice(1).toLowerCase()),
    values:   chartData.user_type_distribution.map((u) => u.count),
    type:     "pie" as const,
    hole:     0.45,
    marker:   { colors: [C.green, C.blue, C.gray] },
  }] : [];

  const paymentPie = chartData ? [{
    labels:   chartData.payment_distribution.map((p) => p.type.charAt(0) + p.type.slice(1).toLowerCase()),
    values:   chartData.payment_distribution.map((p) => p.count),
    type:     "pie" as const,
    hole:     0.45,
    marker:   { colors: [C.green, C.amber, C.teal, C.gray] },
  }] : [];

  const enforcementBar = chartData ? [{
    x:          chartData.enforcement_distribution.map((e) => e.status.charAt(0) + e.status.slice(1).toLowerCase()),
    y:          chartData.enforcement_distribution.map((e) => e.count),
    type:       "bar" as const,
    name:       "Count",
    marker:     { color: [C.gray, C.amber, C.red] },
    showlegend: false,
  }] : [];

  const sessionTypePie = chartData ? [{
    labels:   chartData.session_type_distribution.map((s) => s.type.charAt(0) + s.type.slice(1).toLowerCase()),
    values:   chartData.session_type_distribution.map((s) => s.count),
    type:     "pie" as const,
    hole:     0.45,
    marker:   { colors: [C.green, C.purple, C.amber] },
  }] : [];

  const noData = (arr: unknown[]) => arr.length === 0;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
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
        <Button variant="secondary" size="sm" onClick={loadStats} disabled={loading}>
          {loading
            ? <><Spinner size="sm" color="border-gray-500" /> Refreshing…</>
            : "Refresh"}
        </Button>
      </div>

      {hasError && !loading && stats === null && (
        <Alert variant="error" className="mb-6">
          Could not load dashboard data.{" "}
          <button onClick={loadStats} className="underline font-medium">Try again</button>
        </Alert>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {isFirstLoad ? (
          Array.from({ length: 4 }, (_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="Active Sessions"     value={stats?.active_sessions}      accent="text-green-700" />
            <StatCard label="Sessions Today"      value={stats?.total_sessions_today} accent="text-blue-700" />
            <StatCard label="Enforcement Checks"  value={stats?.enforcement_checks}   accent="text-gray-700" />
            <StatCard label="Violations"          value={stats?.violations}            accent="text-red-600" />
          </>
        )}
      </div>

      <p className="mt-2 text-xs text-gray-400 text-right">
        Auto-refreshes every {AUTO_REFRESH_MS / 1000}s
      </p>

      {/* Charts */}
      <div className="mt-8">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Activity Overview</h2>

        {/* Row 1 — line chart full width */}
        <div className="mb-4">
          <ChartCard title="Sessions per Day — Last 30 Days">
            {noData(sessionsPerDayTraces[0]?.x ?? []) && noData(sessionsPerDayTraces[1]?.x ?? []) ? (
              <p className="text-sm text-gray-400 py-8 text-center">No data yet.</p>
            ) : (
              <Plot
                data={sessionsPerDayTraces}
                layout={{
                  ...PLOTLY_BASE,
                  height: 240,
                  xaxis: { ...PLOTLY_BASE.xaxis, type: "date" as const },
                }}
                config={PLOTLY_CONFIG}
                style={{ width: "100%" }}
              />
            )}
          </ChartCard>
        </div>

        {/* Row 2 — bar + pie */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <ChartCard title="Sessions by Zone (All Time)">
            {noData(zoneTraces[0]?.x ?? []) ? (
              <p className="text-sm text-gray-400 py-8 text-center">No data yet.</p>
            ) : (
              <Plot
                data={zoneTraces}
                layout={{ ...PLOTLY_BASE, height: 220, showlegend: false }}
                config={PLOTLY_CONFIG}
                style={{ width: "100%" }}
              />
            )}
          </ChartCard>

          <ChartCard title="User Type Distribution (Historic)">
            {noData(userTypePie[0]?.values ?? []) ? (
              <p className="text-sm text-gray-400 py-8 text-center">No historic data imported yet.</p>
            ) : (
              <Plot
                data={userTypePie}
                layout={{ ...PLOTLY_BASE, height: 220, showlegend: true, margin: { l: 16, r: 16, t: 16, b: 16 } }}
                config={PLOTLY_CONFIG}
                style={{ width: "100%" }}
              />
            )}
          </ChartCard>
        </div>

        {/* Row 3 — three smaller cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ChartCard title="Payment Type (Historic)">
            {noData(paymentPie[0]?.values ?? []) ? (
              <p className="text-sm text-gray-400 py-6 text-center">No historic data.</p>
            ) : (
              <Plot
                data={paymentPie}
                layout={{ ...PLOTLY_BASE, height: 200, showlegend: true, margin: { l: 8, r: 8, t: 8, b: 8 } }}
                config={PLOTLY_CONFIG}
                style={{ width: "100%" }}
              />
            )}
          </ChartCard>

          <ChartCard title="Enforcement Status (Historic)">
            {noData(enforcementBar[0]?.x ?? []) ? (
              <p className="text-sm text-gray-400 py-6 text-center">No historic data.</p>
            ) : (
              <Plot
                data={enforcementBar}
                layout={{ ...PLOTLY_BASE, height: 200, showlegend: false, margin: { l: 32, r: 8, t: 8, b: 32 } }}
                config={PLOTLY_CONFIG}
                style={{ width: "100%" }}
              />
            )}
          </ChartCard>

          <ChartCard title="Session Type (Historic)">
            {noData(sessionTypePie[0]?.values ?? []) ? (
              <p className="text-sm text-gray-400 py-6 text-center">No historic data.</p>
            ) : (
              <Plot
                data={sessionTypePie}
                layout={{ ...PLOTLY_BASE, height: 200, showlegend: true, margin: { l: 8, r: 8, t: 8, b: 8 } }}
                config={PLOTLY_CONFIG}
                style={{ width: "100%" }}
              />
            )}
          </ChartCard>
        </div>
      </div>
    </div>
  );
}
