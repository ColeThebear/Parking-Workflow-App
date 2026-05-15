import { useState } from "react";
import type { KeyboardEvent } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card, CardRow } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TextInput } from "@/components/ui/Input";
import { PageSpinner } from "@/components/ui/Spinner";

// ── Types ─────────────────────────────────────────────────────────────────────

type Session = {
  session_id: number;
  plate:      string;
  zone:       string;
  start_time: string;
  expires_at: string | null;
};

type StudentResult = {
  user_id:         number;
  email:           string;
  active_session:  Session | null;
  recent_sessions: Session[];
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

// ── Session history list ──────────────────────────────────────────────────────

function SessionHistory({ sessions, activeId }: { sessions: Session[]; activeId?: number }) {
  if (!sessions.length) {
    return <p className="text-sm text-gray-400 py-2">No session history.</p>;
  }
  return (
    <div className="flex flex-col gap-1.5">
      {sessions.map((s) => (
        <div
          key={s.session_id}
          className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-sm"
        >
          <div>
            <span className="font-mono font-medium tracking-widest">{s.plate}</span>
            <span className="text-gray-400 mx-1.5">·</span>
            <span className="text-gray-600">{s.zone}</span>
            <p className="text-xs text-gray-400 mt-0.5">{fmt(s.start_time)}</p>
          </div>
          <Badge variant={s.session_id === activeId ? "active" : "ended"} />
        </div>
      ))}
    </div>
  );
}

// ── Student result card ───────────────────────────────────────────────────────

function StudentCard({ student, onSessionEnded }: {
  student:        StudentResult;
  onSessionEnded: (userId: number) => void;
}) {
  const { showToast }                    = useToast();
  const [ending,    setEnding]           = useState(false);
  const [confirmed, setConfirmed]        = useState(false);
  const [expanded,  setExpanded]         = useState(true);

  const s = student.active_session;

  async function endSession() {
    if (!s) return;
    if (!confirmed) { setConfirmed(true); return; }
    setEnding(true);
    try {
      await api.post("/operator/end-session", { session_id: s.session_id });
      showToast("success", `Session for ${student.email} ended.`);
      onSessionEnded(student.user_id);
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to end session."));
    } finally {
      setEnding(false);
      setConfirmed(false);
    }
  }

  return (
    <Card padding="sm">
      {/* ── Collapsible header ── */}
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex items-center justify-between w-full gap-3 px-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <Badge variant={s ? "active" : "ended"} label={s ? "Parked" : "Not Parked"} />
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 text-sm truncate">{student.email}</p>
            <p className="text-xs text-gray-400">ID #{student.user_id}</p>
          </div>
        </div>
        <span className={`text-gray-400 text-xs transition-transform duration-150 ${expanded ? "" : "-rotate-180"}`}>
          ▲
        </span>
      </button>

      {/* ── Expanded body ── */}
      {expanded && (
        <div className="mt-3 px-2 flex flex-col gap-4">

          {/* Active session */}
          {s ? (
            <div className="rounded-lg bg-green-50 border border-green-200 p-3">
              <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">
                Active Session
              </p>
              <CardRow label="Plate"   value={<span className="font-mono tracking-widest">{s.plate}</span>} />
              <CardRow label="Zone"    value={s.zone} />
              <CardRow label="Started" value={fmt(s.start_time)} />
              {s.expires_at && <CardRow label="Expires" value={fmt(s.expires_at)} />}

              <div className="mt-3 flex gap-2">
                {confirmed ? (
                  <>
                    <Button variant="danger" size="sm" loading={ending} onClick={endSession} className="flex-1">
                      Confirm End Session
                    </Button>
                    <Button variant="secondary" size="sm" onClick={() => setConfirmed(false)} disabled={ending}>
                      Cancel
                    </Button>
                  </>
                ) : (
                  <Button variant="danger" size="sm" onClick={endSession} className="flex-1">
                    End Session
                  </Button>
                )}
              </div>
              {confirmed && !ending && (
                <p className="text-xs text-red-600 mt-2 text-center">
                  The student will be notified on their next login.
                </p>
              )}
            </div>
          ) : (
            <Alert variant="info">No active parking session.</Alert>
          )}

          {/* Session history */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Session History
            </p>
            <SessionHistory
              sessions={student.recent_sessions}
              activeId={s?.session_id}
            />
          </div>
        </div>
      )}
    </Card>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OperatorSearch() {
  const { showToast } = useToast();

  const [query,       setQuery]       = useState("");
  const [loading,     setLoading]     = useState(false);
  const [results,     setResults]     = useState<StudentResult[] | null>(null);
  const [searchedFor, setSearchedFor] = useState("");

  async function search() {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setResults(null);
    try {
      const { data } = await api.get<StudentResult[]>("/operator/search", { params: { query: q } });
      setResults(data);
      setSearchedFor(q);
    } catch (err) {
      showToast("error", getErrorMessage(err, "Search failed."));
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") search();
  }

  function handleSessionEnded(userId: number) {
    setResults((prev) =>
      prev ? prev.map((r) => r.user_id === userId ? { ...r, active_session: null } : r) : prev
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Student Search</h1>
      <p className="text-sm text-gray-500 mb-6">Search by email address or vehicle plate number.</p>

      <div className="flex gap-2 mb-8">
        <TextInput
          className="flex-1"
          placeholder="student@suny.edu or ABC1234"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <Button onClick={search} disabled={!query.trim() || loading} loading={loading}>
          Search
        </Button>
      </div>

      {loading && <PageSpinner />}

      {!loading && results !== null && results.length === 0 && (
        <Alert variant="info">
          No students found matching <strong>"{searchedFor}"</strong>.
        </Alert>
      )}

      {!loading && results && results.length > 0 && (
        <div className="flex flex-col gap-3">
          <p className="text-xs text-gray-400">
            {results.length} result{results.length !== 1 ? "s" : ""} for "{searchedFor}"
          </p>
          {results.map((student) => (
            <StudentCard key={student.user_id} student={student} onSessionEnded={handleSessionEnded} />
          ))}
        </div>
      )}
    </div>
  );
}
