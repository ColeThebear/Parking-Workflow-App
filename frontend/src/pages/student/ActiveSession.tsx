import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card, CardRow } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { PageSpinner } from "@/components/ui/Spinner";

type Session = {
  session_id: number;
  plate:      string;
  zone:       string;
  start_time: string;
  expires_at: string | null;
};

function useElapsed(startIso: string) {
  const [elapsed, setElapsed] = useState("");

  useEffect(() => {
    function update() {
      const secs = Math.max(0, Math.floor((Date.now() - new Date(startIso).getTime()) / 1000));
      const h = Math.floor(secs / 3600);
      const m = Math.floor((secs % 3600) / 60);
      const s = secs % 60;
      setElapsed(
        h > 0
          ? `${h}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`
          : `${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`
      );
    }
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [startIso]);

  return elapsed;
}

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

// ── Active session view ───────────────────────────────────────────────────────

function SessionView({ session, onEnd }: { session: Session; onEnd: () => void }) {
  const { showToast } = useToast();
  const navigate = useNavigate();
  const elapsed  = useElapsed(session.start_time);

  const [ending,    setEnding]    = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  async function endSession() {
    if (!confirmed) { setConfirmed(true); return; }
    setEnding(true);
    try {
      await api.post("/student/end");
      showToast("success", "Parking session ended.");
      navigate("/student/start", { replace: true });
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to end session."));
      setEnding(false);
      setConfirmed(false);
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 py-10">
      <Card>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900">Active Session</h1>
          <Badge variant="active" />
        </div>

        {/* Elapsed timer */}
        <div className="text-center py-5 mb-4 rounded-xl bg-blue-50 border border-blue-100">
          <p className="text-xs text-blue-500 font-medium uppercase tracking-wide mb-1">
            Time Parked
          </p>
          <p className="text-4xl font-bold text-blue-700 tabular-nums">{elapsed}</p>
        </div>

        {/* Details */}
        <div className="mb-6">
          <CardRow label="License Plate" value={<span className="font-mono tracking-widest">{session.plate}</span>} />
          <CardRow label="Zone"          value={session.zone} />
          <CardRow label="Started"       value={fmt(session.start_time)} />
          {session.expires_at && (
            <CardRow label="Expires"     value={fmt(session.expires_at)} />
          )}
        </div>

        {/* End session — two-step confirm */}
        {confirmed ? (
          <div className="flex flex-col gap-2">
            <Alert variant="warning">
              Are you sure you want to end your parking session?
            </Alert>
            <div className="flex gap-2 mt-1">
              <Button variant="danger" loading={ending} onClick={endSession} fullWidth>
                Yes, End Session
              </Button>
              <Button variant="secondary" onClick={() => setConfirmed(false)} disabled={ending} fullWidth>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button variant="danger" onClick={endSession} fullWidth>
            End Session
          </Button>
        )}
      </Card>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ActiveSession() {
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ data: Session }>("/student/active")
      .then(({ data }) => setSession(data.data))
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageSpinner />;

  if (!session) {
    return (
      <div className="max-w-md mx-auto px-4 py-10">
        <Card>
          <Alert variant="info" title="No Active Session">
            You don't have an active parking session.
          </Alert>
          <Button
            onClick={() => navigate("/student/start")}
            fullWidth
            className="mt-4"
          >
            Start Parking
          </Button>
        </Card>
      </div>
    );
  }

  return <SessionView session={session} onEnd={() => setSession(null)} />;
}
