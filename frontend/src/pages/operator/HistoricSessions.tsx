import { useState, useCallback } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TextInput, SelectInput } from "@/components/ui/Input";
import { PageSpinner, Spinner } from "@/components/ui/Spinner";

type HistoricSession = {
  id:                 number;
  vehicle_plate:      string;
  zone:               string;
  started_at:         string;
  ended_at:           string | null;
  duration_minutes:   number | null;
  user_type:          string;
  session_type:       string;
  payment_type:       string;
  enforcement_status: string;
  notes:              string | null;
  imported_at:        string;
};

const ZONES = ["Lot A", "Lot B", "Lot C", "Lot D", "Visitor Lot"];

const ENF_VARIANT: Record<string, "active" | "ended" | "terminated" | "neutral"> = {
  NONE:    "ended",
  CHECKED: "neutral",
  CITED:   "terminated",
};

const PAY_VARIANT: Record<string, "active" | "ended" | "terminated" | "neutral"> = {
  TOKEN: "active",
  CASH:  "neutral",
  CARD:  "neutral",
  FREE:  "ended",
};

function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
}

function fmtDuration(mins: number | null) {
  if (mins === null || mins === undefined) return "—";
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

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

const PAGE_SIZE = 50;

export default function HistoricSessions() {
  const { showToast } = useToast();

  const [sessions, setSessions]     = useState<HistoricSession[]>([]);
  const [loading,  setLoading]      = useState(false);
  const [searched, setSearched]     = useState(false);
  const [offset,   setOffset]       = useState(0);
  const [hasMore,  setHasMore]      = useState(false);

  // Filters
  const [dateFrom,   setDateFrom]   = useState("");
  const [dateTo,     setDateTo]     = useState("");
  const [plate,      setPlate]      = useState("");
  const [userType,   setUserType]   = useState("");
  const [zone,       setZone]       = useState("");
  const [sessType,   setSessType]   = useState("");
  const [payType,    setPayType]    = useState("");
  const [enfStatus,  setEnfStatus]  = useState("");
  const [durMin,     setDurMin]     = useState("");
  const [durMax,     setDurMax]     = useState("");

  const buildParams = (pageOffset: number) => {
    const p: Record<string, string> = {
      limit:  String(PAGE_SIZE + 1),
      offset: String(pageOffset),
    };
    if (dateFrom)  p.date_from          = dateFrom;
    if (dateTo)    p.date_to            = dateTo;
    if (plate)     p.plate              = plate;
    if (userType)  p.user_type          = userType;
    if (zone)      p.zone               = zone;
    if (sessType)  p.session_type       = sessType;
    if (payType)   p.payment_type       = payType;
    if (enfStatus) p.enforcement_status = enfStatus;
    if (durMin)    p.duration_min       = durMin;
    if (durMax)    p.duration_max       = durMax;
    return p;
  };

  const load = useCallback(async (pageOffset: number) => {
    setLoading(true);
    try {
      const { data } = await api.get<HistoricSession[]>("/operator/historic-sessions", {
        params: buildParams(pageOffset),
      });
      const page = data.slice(0, PAGE_SIZE);
      setHasMore(data.length > PAGE_SIZE);
      if (pageOffset === 0) {
        setSessions(page);
      } else {
        setSessions((prev) => [...prev, ...page]);
      }
      setOffset(pageOffset);
      setSearched(true);
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to load historic sessions."));
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showToast, dateFrom, dateTo, plate, userType, zone, sessType, payType, enfStatus, durMin, durMax]);

  function handleSearch() {
    load(0);
  }

  function handleReset() {
    setDateFrom(""); setDateTo(""); setPlate(""); setUserType("");
    setZone(""); setSessType(""); setPayType(""); setEnfStatus("");
    setDurMin(""); setDurMax("");
    setSessions([]); setSearched(false); setOffset(0); setHasMore(false);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Historic Sessions</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Browse and filter imported historic parking session data.
        </p>
      </div>

      {/* Filter panel */}
      <Card padding="md" className="mb-6">
        <p className="text-sm font-semibold text-gray-700 mb-4">Filters</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          <TextInput
            label="Date from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
          <TextInput
            label="Date to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
          <TextInput
            label="License plate"
            placeholder="ABC1234"
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
            className="uppercase tracking-widest"
          />
          <SelectInput
            label="User type"
            value={userType}
            onChange={(e) => setUserType(e.target.value)}
          >
            <option value="">All</option>
            <option value="STUDENT">Student</option>
            <option value="GUEST">Guest</option>
            <option value="UNREGISTERED">Unregistered</option>
          </SelectInput>

          <SelectInput
            label="Zone"
            value={zone}
            onChange={(e) => setZone(e.target.value)}
          >
            <option value="">All zones</option>
            {ZONES.map((z) => <option key={z} value={z}>{z}</option>)}
          </SelectInput>
          <SelectInput
            label="Session type"
            value={sessType}
            onChange={(e) => setSessType(e.target.value)}
          >
            <option value="">All</option>
            <option value="STANDARD">Standard</option>
            <option value="PERMIT">Permit</option>
            <option value="EVENT">Event</option>
          </SelectInput>
          <SelectInput
            label="Payment type"
            value={payType}
            onChange={(e) => setPayType(e.target.value)}
          >
            <option value="">All</option>
            <option value="TOKEN">Token</option>
            <option value="CASH">Cash</option>
            <option value="CARD">Card</option>
            <option value="FREE">Free</option>
          </SelectInput>
          <SelectInput
            label="Enforcement status"
            value={enfStatus}
            onChange={(e) => setEnfStatus(e.target.value)}
          >
            <option value="">All</option>
            <option value="NONE">None</option>
            <option value="CHECKED">Checked</option>
            <option value="CITED">Cited</option>
          </SelectInput>

          <TextInput
            label="Min duration (mins)"
            type="number"
            placeholder="0"
            value={durMin}
            onChange={(e) => setDurMin(e.target.value)}
          />
          <TextInput
            label="Max duration (mins)"
            type="number"
            placeholder="480"
            value={durMax}
            onChange={(e) => setDurMax(e.target.value)}
          />
        </div>

        <div className="flex gap-3 mt-4">
          <Button onClick={handleSearch} disabled={loading} loading={loading}>
            Search
          </Button>
          <Button variant="secondary" onClick={handleReset} disabled={loading}>
            Reset
          </Button>
        </div>
      </Card>

      {/* Results */}
      {loading && sessions.length === 0 && <PageSpinner />}

      {!loading && searched && sessions.length === 0 && (
        <Alert variant="info">No historic sessions match your filters.</Alert>
      )}

      {sessions.length > 0 && (
        <>
          <Card padding="sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px]">
                <thead>
                  <tr>
                    <Th>Plate</Th>
                    <Th>Zone</Th>
                    <Th>Started</Th>
                    <Th>Ended</Th>
                    <Th>Duration</Th>
                    <Th>User type</Th>
                    <Th>Session type</Th>
                    <Th>Payment</Th>
                    <Th>Enforcement</Th>
                    <Th>Notes</Th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s) => (
                    <tr key={s.id} className="hover:bg-gray-50">
                      <Td mono>{s.vehicle_plate}</Td>
                      <Td>{s.zone}</Td>
                      <Td>{fmt(s.started_at)}</Td>
                      <Td>{fmt(s.ended_at)}</Td>
                      <Td>{fmtDuration(s.duration_minutes)}</Td>
                      <Td>
                        <span className="text-xs text-gray-600 capitalize">
                          {s.user_type.toLowerCase()}
                        </span>
                      </Td>
                      <Td>
                        <span className="text-xs text-gray-600 capitalize">
                          {s.session_type.toLowerCase()}
                        </span>
                      </Td>
                      <Td>
                        <Badge
                          variant={PAY_VARIANT[s.payment_type] ?? "neutral"}
                          label={s.payment_type.charAt(0) + s.payment_type.slice(1).toLowerCase()}
                        />
                      </Td>
                      <Td>
                        <Badge
                          variant={ENF_VARIANT[s.enforcement_status] ?? "neutral"}
                          label={s.enforcement_status.charAt(0) + s.enforcement_status.slice(1).toLowerCase()}
                        />
                      </Td>
                      <Td>
                        {s.notes
                          ? <span className="text-xs text-gray-500">{s.notes}</span>
                          : <span className="text-gray-300">—</span>}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-400">
                Showing {sessions.length} record{sessions.length !== 1 ? "s" : ""}
              </p>
              {hasMore && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => load(offset + PAGE_SIZE)}
                  disabled={loading}
                >
                  {loading ? <><Spinner size="sm" color="border-gray-500" /> Loading…</> : "Load more"}
                </Button>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
