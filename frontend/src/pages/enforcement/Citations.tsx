import { useState, useEffect } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TextInput, SelectInput } from "@/components/ui/Input";
import { PageSpinner } from "@/components/ui/Spinner";

const FINE_OPTIONS = [
  { label: "$25.00",  value: 2500 },
  { label: "$50.00",  value: 5000 },
  { label: "$75.00",  value: 7500 },
  { label: "$100.00", value: 10000 },
];

const ZONES = ["Lot A", "Lot B", "Lot C", "Lot D", "Visitor Lot", "Faculty Lot", "Other"];

type Citation = {
  id:             number;
  vehicle_plate:  string;
  zone:           string;
  violation_type: string;
  fine_amount:    number;
  notes:          string | null;
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

// ── Issue citation form ───────────────────────────────────────────────────────

function IssueCitationForm({ onIssued }: { onIssued: (c: Citation) => void }) {
  const { showToast } = useToast();
  const [violationTypes, setViolationTypes] = useState<string[]>([]);
  const [plate,     setPlate]     = useState("");
  const [zone,      setZone]      = useState("");
  const [violation, setViolation] = useState("");
  const [fine,      setFine]      = useState(5000);
  const [notes,     setNotes]     = useState("");
  const [loading,   setLoading]   = useState(false);

  useEffect(() => {
    api.get<string[]>("/enforcement/violation-types")
      .then(({ data }) => { setViolationTypes(data); setViolation(data[0] ?? ""); })
      .catch(() => {});
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!plate.trim() || !zone || !violation) {
      showToast("error", "Please fill all required fields.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post<Citation>("/enforcement/citations", {
        vehicle_plate:  plate.trim().toUpperCase(),
        zone,
        violation_type: violation,
        fine_amount:    fine,
        notes:          notes.trim() || null,
      });
      showToast("success", `Citation issued for ${data.vehicle_plate}.`);
      onIssued(data);
      setPlate(""); setZone(""); setNotes("");
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to issue citation."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="mb-8">
      <h2 className="text-base font-semibold text-gray-800 mb-4">Issue Citation</h2>
      <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <TextInput
          label="Plate *"
          placeholder="ABC1234"
          value={plate}
          onChange={(e) => setPlate(e.target.value.toUpperCase())}
          className="uppercase tracking-widest"
          disabled={loading}
        />
        <SelectInput label="Zone *" value={zone} onChange={(e) => setZone(e.target.value)} disabled={loading}>
          <option value="">Select zone…</option>
          {ZONES.map((z) => <option key={z} value={z}>{z}</option>)}
        </SelectInput>
        <SelectInput label="Violation *" value={violation} onChange={(e) => setViolation(e.target.value)} disabled={loading}>
          {violationTypes.map((v) => <option key={v} value={v}>{v}</option>)}
        </SelectInput>
        <SelectInput label="Fine" value={fine} onChange={(e) => setFine(Number(e.target.value))} disabled={loading}>
          {FINE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </SelectInput>
        <div className="sm:col-span-2">
          <TextInput
            label="Notes (optional)"
            placeholder="Additional details…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="sm:col-span-2">
          <Button type="submit" loading={loading} variant="danger" fullWidth>
            Issue Citation
          </Button>
        </div>
      </form>
    </Card>
  );
}

// ── Citations list ────────────────────────────────────────────────────────────

function CitationTable({ citations }: { citations: Citation[] }) {
  if (!citations.length) {
    return <Alert variant="info">You have not issued any citations yet.</Alert>;
  }
  return (
    <div className="flex flex-col gap-3">
      {citations.map((c) => (
        <Card key={c.id} padding="sm">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono font-semibold tracking-widest text-gray-900">{c.vehicle_plate}</span>
                <Badge variant={c.paid ? "ended" : "terminated"} label={c.paid ? "Paid" : "Unpaid"} />
                {c.appealed && <Badge variant="neutral" label="Appealed" />}
              </div>
              <p className="text-sm text-gray-600">{c.violation_type} · {c.zone}</p>
              {c.student_email && <p className="text-xs text-gray-400 mt-0.5">{c.student_email}</p>}
              {c.notes && <p className="text-xs text-gray-500 mt-1 italic">"{c.notes}"</p>}
            </div>
            <div className="text-right shrink-0">
              <p className="font-bold text-gray-900">{fmtMoney(c.fine_amount)}</p>
              <p className="text-xs text-gray-400 mt-1">{fmt(c.issued_at)}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function EnforcementCitations() {
  const { showToast }             = useToast();
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    api.get<Citation[]>("/enforcement/citations")
      .then(({ data }) => setCitations(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load citations.")))
      .finally(() => setLoading(false));
  }, []);

  function handleIssued(c: Citation) {
    setCitations((prev) => [c, ...prev]);
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Citations</h1>
      <p className="text-sm text-gray-500 mb-6">Issue and review parking citations.</p>

      <IssueCitationForm onIssued={handleIssued} />

      <h2 className="text-base font-semibold text-gray-700 mb-3">
        My Citations ({citations.length})
      </h2>

      {loading ? <PageSpinner /> : <CitationTable citations={citations} />}
    </div>
  );
}
