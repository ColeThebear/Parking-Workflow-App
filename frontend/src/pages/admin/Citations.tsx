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
  officer_email:  string;
  student_email:  string | null;
};

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function fmtMoney(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

export default function AdminCitations() {
  const { showToast }                     = useToast();
  const [citations,  setCitations]        = useState<Citation[]>([]);
  const [loading,    setLoading]          = useState(true);
  const [markingId,  setMarkingId]        = useState<number | null>(null);
  const [filterPaid, setFilterPaid]       = useState<"all" | "unpaid" | "paid">("all");

  useEffect(() => {
    api.get<Citation[]>("/admin/citations")
      .then(({ data }) => setCitations(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load citations.")))
      .finally(() => setLoading(false));
  }, []);

  async function markPaid(id: number) {
    setMarkingId(id);
    try {
      await api.patch(`/admin/citations/${id}/paid`);
      setCitations((prev) => prev.map((c) => c.id === id ? { ...c, paid: true } : c));
      showToast("success", "Citation marked as paid.");
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to update citation."));
    } finally {
      setMarkingId(null);
    }
  }

  const visible = citations.filter((c) => {
    if (filterPaid === "unpaid") return !c.paid;
    if (filterPaid === "paid")   return  c.paid;
    return true;
  });

  const unpaidCount = citations.filter((c) => !c.paid).length;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Citations</h1>
      <p className="text-sm text-gray-500 mb-6">
        All citations system-wide — {unpaidCount} unpaid.
      </p>

      {loading && <PageSpinner />}

      {!loading && (
        <>
          {/* Filter tabs */}
          <div className="flex gap-1 border-b border-gray-200 mb-6">
            {(["all", "unpaid", "paid"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilterPaid(f)}
                className={[
                  "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize",
                  filterPaid === f
                    ? "border-purple-600 text-purple-700"
                    : "border-transparent text-gray-500 hover:text-gray-800",
                ].join(" ")}
              >
                {f === "all" ? `All (${citations.length})` : f === "unpaid" ? `Unpaid (${unpaidCount})` : `Paid (${citations.length - unpaidCount})`}
              </button>
            ))}
          </div>

          {visible.length === 0 ? (
            <Alert variant="info">No citations in this category.</Alert>
          ) : (
            <div className="flex flex-col gap-3">
              {visible.map((c) => (
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
                      <p className="text-xs text-gray-400 mt-0.5">
                        Officer: {c.officer_email}
                        {c.student_email && ` · Student: ${c.student_email}`}
                      </p>
                      <p className="text-xs text-gray-400">{fmt(c.issued_at)}</p>
                    </div>
                    <div className="text-right shrink-0 flex flex-col items-end gap-2">
                      <p className="font-bold text-gray-900">{fmtMoney(c.fine_amount)}</p>
                      {!c.paid && (
                        <Button
                          variant="secondary"
                          size="sm"
                          loading={markingId === c.id}
                          onClick={() => markPaid(c.id)}
                        >
                          Mark Paid
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
