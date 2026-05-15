import { useState, useEffect } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { PageSpinner } from "@/components/ui/Spinner";

type Citation = {
  id:             number;
  plate:          string;
  zone:           string;
  violation_type: string;
  fine_amount:    number;
  issued_at:      string;
  paid:           boolean;
  appealed:       boolean;
};

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function GuestCitations() {
  const { showToast }                   = useToast();
  const [citations,  setCitations]      = useState<Citation[]>([]);
  const [loading,    setLoading]        = useState(true);
  const [appealingId, setAppealingId]   = useState<number | null>(null);

  useEffect(() => {
    api.get<Citation[]>("/guest/citations")
      .then(({ data }) => setCitations(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load citations.")))
      .finally(() => setLoading(false));
  }, []);

  async function appeal(id: number) {
    setAppealingId(id);
    try {
      await api.post(`/guest/citations/${id}/appeal`);
      setCitations((prev) => prev.map((c) => c.id === id ? { ...c, appealed: true } : c));
      showToast("success", "Appeal submitted.");
    } catch (err) {
      showToast("error", getErrorMessage(err, "Appeal failed."));
    } finally {
      setAppealingId(null);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">My Citations</h1>
      <p className="text-sm text-gray-500 mb-6">View and appeal parking citations issued to your vehicle.</p>

      {loading && <PageSpinner />}

      {!loading && citations.length === 0 && (
        <Alert variant="info">No citations on your account.</Alert>
      )}

      {!loading && citations.length > 0 && (
        <div className="flex flex-col gap-3">
          {citations.map((c) => (
            <Card key={c.id} padding="sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-mono font-semibold tracking-widest text-gray-900">
                      {c.plate}
                    </span>
                    <Badge variant={c.paid ? "ended" : "terminated"} label={c.paid ? "Paid" : "Unpaid"} />
                    {c.appealed && <Badge variant="neutral" label="Appealed" />}
                  </div>
                  <p className="text-sm text-gray-600">{c.violation_type} · {c.zone}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{fmt(c.issued_at)}</p>
                </div>
                <div className="text-right shrink-0 flex flex-col items-end gap-2">
                  <p className="font-bold text-gray-900">
                    ${(c.fine_amount / 100).toFixed(2)}
                  </p>
                  {!c.appealed && !c.paid && (
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={appealingId === c.id}
                      onClick={() => appeal(c.id)}
                    >
                      Appeal
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
