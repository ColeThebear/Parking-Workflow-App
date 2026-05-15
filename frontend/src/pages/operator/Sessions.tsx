import { useState, useEffect, useCallback } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TextInput, SelectInput } from "@/components/ui/Input";
import { PageSpinner, Spinner } from "@/components/ui/Spinner";

type Tab = "active" | "today" | "checks" | "violations";

type ActiveSession = {
  session_id:    number;
  plate:         string;
  zone:          string;
  start_time:    string;
  expires_at:    string | null;
  student_email: string | null;
};

type TodaySession = ActiveSession & { ended_at: string | null; active: boolean };

type Check = {
  id:            number;
  plate:         string;
  session_found: boolean;
  checked_at:    string;
  officer:       string;
};

type Violation = {
  id:             number;
  plate:          string;
  zone:           string;
  violation_type: string;
  fine_amount:    number;
  issued_at:      string;
  paid:           boolean;
  officer:        string;
  student_email:  string | null;
};

function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
}

const TAB_LABELS: Record<Tab, string> = {
  active:     "Active Now",
  today:      "Today's Sessions",
  checks:     "Enforcement Checks",
  violations: "Violations",
};

// ── Table helpers ──────────────────────────────────────────────────────────────

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-2.5 bg-gray-50 first:rounded-tl-lg last:rounded-tr-lg">
      {children}
    </th>
  );
}

function Td({ children, mono }: { children: React.ReactNode; mono?: boolean }) {
  return (
    <td className={`px-3 py-2.5 text-sm border-b border-gray-100 ${mono ? "font-mono tracking-widest" : ""}`}>
      {children}
    </td>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OperatorSessions() {
  const { showToast } = useToast();
  const [tab,        setTab]       = useState<Tab>("active");
  const [loading,    setLoading]   = useState(false);
  const [active,     setActive]    = useState<ActiveSession[]>([]);
  const [today,      setToday]     = useState<TodaySession[]>([]);
  const [checks,     setChecks]    = useState<Check[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [zoneFilter, setZoneFilter] = useState("");
  const [plateFilter, setPlateFilter] = useState("");

  const load = useCallback(async (t: Tab) => {
    setLoading(true);
    try {
      if (t === "active") {
        const { data } = await api.get<ActiveSession[]>("/operator/sessions/active");
        setActive(data);
      } else if (t === "today") {
        const params: Record<string, string> = {};
        if (zoneFilter)  params.zone  = zoneFilter;
        if (plateFilter) params.plate = plateFilter;
        const { data } = await api.get<TodaySession[]>("/operator/sessions/today", { params });
        setToday(data);
      } else if (t === "checks") {
        const { data } = await api.get<Check[]>("/operator/enforcement/checks");
        setChecks(data);
      } else {
        const { data } = await api.get<Violation[]>("/operator/enforcement/violations");
        setViolations(data);
      }
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to load data."));
    } finally {
      setLoading(false);
    }
  }, [showToast, zoneFilter, plateFilter]);

  useEffect(() => { load(tab); }, [tab]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Sessions &amp; Activity</h1>
          <p className="text-sm text-gray-500 mt-0.5">Real-time parking and enforcement data.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => load(tab)} disabled={loading}>
          {loading ? <><Spinner size="sm" color="border-gray-500" /> Refreshing…</> : "Refresh"}
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {(["active", "today", "checks", "violations"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={[
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              tab === t
                ? "border-green-600 text-green-700"
                : "border-transparent text-gray-500 hover:text-gray-800",
            ].join(" ")}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* Filters for today */}
      {tab === "today" && (
        <div className="flex gap-3 mb-4">
          <TextInput
            placeholder="Filter by plate…"
            value={plateFilter}
            onChange={(e) => setPlateFilter(e.target.value.toUpperCase())}
            className="w-40 uppercase tracking-widest"
          />
          <SelectInput value={zoneFilter} onChange={(e) => setZoneFilter(e.target.value)} className="w-44">
            <option value="">All zones</option>
            {["Lot A","Lot B","Lot C","Lot D","Visitor Lot"].map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </SelectInput>
          <Button size="sm" onClick={() => load("today")} disabled={loading}>Apply</Button>
        </div>
      )}

      {loading && <PageSpinner />}

      {/* Active sessions */}
      {!loading && tab === "active" && (
        active.length === 0
          ? <Alert variant="info">No active sessions right now.</Alert>
          : (
            <Card padding="sm">
              <table className="w-full">
                <thead>
                  <tr><Th>Plate</Th><Th>Zone</Th><Th>Student</Th><Th>Started</Th><Th>Expires</Th></tr>
                </thead>
                <tbody>
                  {active.map((s) => (
                    <tr key={s.session_id} className="hover:bg-gray-50">
                      <Td mono>{s.plate}</Td>
                      <Td>{s.zone}</Td>
                      <Td>{s.student_email ?? <span className="text-gray-400 italic">Guest</span>}</Td>
                      <Td>{fmt(s.start_time)}</Td>
                      <Td>{fmt(s.expires_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-400 mt-2 text-right">{active.length} session{active.length !== 1 ? "s" : ""}</p>
            </Card>
          )
      )}

      {/* Today's sessions */}
      {!loading && tab === "today" && (
        today.length === 0
          ? <Alert variant="info">No sessions today matching your filters.</Alert>
          : (
            <Card padding="sm">
              <table className="w-full">
                <thead>
                  <tr><Th>Plate</Th><Th>Zone</Th><Th>Student</Th><Th>Started</Th><Th>Ended</Th><Th>Status</Th></tr>
                </thead>
                <tbody>
                  {today.map((s) => (
                    <tr key={s.session_id} className="hover:bg-gray-50">
                      <Td mono>{s.plate}</Td>
                      <Td>{s.zone}</Td>
                      <Td>{s.student_email ?? <span className="text-gray-400 italic">Guest</span>}</Td>
                      <Td>{fmt(s.start_time)}</Td>
                      <Td>{fmt(s.ended_at)}</Td>
                      <Td><Badge variant={s.active ? "active" : "ended"} /></Td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-400 mt-2 text-right">{today.length} session{today.length !== 1 ? "s" : ""}</p>
            </Card>
          )
      )}

      {/* Enforcement checks */}
      {!loading && tab === "checks" && (
        checks.length === 0
          ? <Alert variant="info">No enforcement checks today.</Alert>
          : (
            <Card padding="sm">
              <table className="w-full">
                <thead>
                  <tr><Th>Plate</Th><Th>Officer</Th><Th>Result</Th><Th>Time</Th></tr>
                </thead>
                <tbody>
                  {checks.map((c) => (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <Td mono>{c.plate}</Td>
                      <Td>{c.officer}</Td>
                      <Td>
                        <Badge
                          variant={c.session_found ? "active" : "ended"}
                          label={c.session_found ? "Valid Session" : "No Session"}
                        />
                      </Td>
                      <Td>{fmt(c.checked_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-400 mt-2 text-right">{checks.length} check{checks.length !== 1 ? "s" : ""}</p>
            </Card>
          )
      )}

      {/* Violations */}
      {!loading && tab === "violations" && (
        violations.length === 0
          ? <Alert variant="info">No violations issued today.</Alert>
          : (
            <Card padding="sm">
              <table className="w-full">
                <thead>
                  <tr><Th>Plate</Th><Th>Zone</Th><Th>Violation</Th><Th>Fine</Th><Th>Status</Th><Th>Officer</Th><Th>Time</Th></tr>
                </thead>
                <tbody>
                  {violations.map((v) => (
                    <tr key={v.id} className="hover:bg-gray-50">
                      <Td mono>{v.plate}</Td>
                      <Td>{v.zone}</Td>
                      <Td>{v.violation_type}</Td>
                      <Td>${(v.fine_amount / 100).toFixed(2)}</Td>
                      <Td><Badge variant={v.paid ? "ended" : "terminated"} label={v.paid ? "Paid" : "Unpaid"} /></Td>
                      <Td>{v.officer}</Td>
                      <Td>{fmt(v.issued_at)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-400 mt-2 text-right">{violations.length} violation{violations.length !== 1 ? "s" : ""}</p>
            </Card>
          )
      )}
    </div>
  );
}
