import { useState, useEffect } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { PageSpinner } from "@/components/ui/Spinner";

type Session = {
  session_id: number;
  plate:      string;
  zone:       string;
  start_time: string;
  expires_at: string | null;
};

function fmt(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function StudentHistory() {
  const { showToast }               = useToast();
  const [sessions, setSessions]     = useState<Session[]>([]);
  const [loading,  setLoading]      = useState(true);

  useEffect(() => {
    api.get<Session[]>("/student/my-sessions")
      .then(({ data }) => setSessions(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load sessions.")))
      .finally(() => setLoading(false));
  }, []);

  const now = new Date();

  function isActive(s: Session) {
    if (!s.expires_at) return false;
    return new Date(s.expires_at) > now;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">My Sessions</h1>
      <p className="text-sm text-gray-500 mb-6">Your full parking session history.</p>

      {loading && <PageSpinner />}

      {!loading && sessions.length === 0 && (
        <Alert variant="info">You have no parking sessions yet.</Alert>
      )}

      {!loading && sessions.length > 0 && (
        <>
          <p className="text-xs text-gray-400 mb-3">
            {sessions.length} session{sessions.length !== 1 ? "s" : ""} total
          </p>
          <div className="flex flex-col gap-2">
            {sessions.map((s) => {
              const active = isActive(s);
              return (
                <Card key={s.session_id} padding="sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-mono font-semibold tracking-widest text-gray-900">
                          {s.plate}
                        </span>
                        <Badge variant={active ? "active" : "ended"} />
                      </div>
                      <p className="text-sm text-gray-600">{s.zone}</p>
                    </div>
                    <div className="text-right shrink-0 text-xs text-gray-400">
                      <p>Started {fmt(s.start_time)}</p>
                      {s.expires_at && (
                        <p className="mt-0.5">
                          {active ? "Expires" : "Expired"} {fmt(s.expires_at)}
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
