import { useState, useRef } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

// ── Student import types ───────────────────────────────────────────────────

type StudentImportRow    = { row: number; email: string; plate: string | null; reason: string };
type StudentImportResult = { added: number; duplicates: StudentImportRow[]; errors: StudentImportRow[] };

// ── Historic import types ──────────────────────────────────────────────────

type HistoricImportRow    = { row: number; plate: string; started_at: string; reason: string };
type HistoricImportResult = { added: number; duplicates: HistoricImportRow[]; errors: HistoricImportRow[] };

// ── Mode ───────────────────────────────────────────────────────────────────

type Mode = "students" | "historic";

const MODE_LABELS: Record<Mode, string> = {
  students: "Import Students",
  historic: "Import Historic Sessions",
};

// ── Drop zone (shared) ─────────────────────────────────────────────────────

function DropZone({
  file,
  onFile,
}: {
  file: File | null;
  onFile: (f: File) => void;
}) {
  const inputRef              = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) onFile(f);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={[
        "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
        dragging
          ? "border-green-400 bg-green-50"
          : "border-gray-300 bg-white hover:border-green-400 hover:bg-green-50",
      ].join(" ")}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
      />
      <p className="text-2xl mb-2">📤</p>
      <p className="text-sm font-medium text-gray-700">
        {file ? file.name : "Drop CSV here or click to browse"}
      </p>
      {file && (
        <p className="text-xs text-gray-400 mt-1">
          {(file.size / 1024).toFixed(1)} KB
        </p>
      )}
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function CsvImport() {
  const { showToast } = useToast();

  const [mode,      setMode]      = useState<Mode>("students");
  const [file,      setFile]      = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [studentResult, setStudentResult] = useState<StudentImportResult | null>(null);
  const [historicResult, setHistoricResult] = useState<HistoricImportResult | null>(null);

  function handleFile(f: File) {
    if (!f.name.toLowerCase().endsWith(".csv")) {
      showToast("error", "Only CSV files are accepted.");
      return;
    }
    setFile(f);
    setStudentResult(null);
    setHistoricResult(null);
  }

  function switchMode(m: Mode) {
    setMode(m);
    setFile(null);
    setStudentResult(null);
    setHistoricResult(null);
  }

  async function upload() {
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);

      if (mode === "students") {
        const { data } = await api.post<StudentImportResult>("/operator/import-students", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setStudentResult(data);
        if (data.added > 0)
          showToast("success", `${data.added} student${data.added !== 1 ? "s" : ""} imported.`);
      } else {
        const { data } = await api.post<HistoricImportResult>("/operator/import-historic", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setHistoricResult(data);
        if (data.added > 0)
          showToast("success", `${data.added} historic session${data.added !== 1 ? "s" : ""} imported.`);
      }
    } catch (err) {
      showToast("error", getErrorMessage(err, "Import failed."));
    } finally {
      setUploading(false);
    }
  }

  const result = mode === "students" ? studentResult : historicResult;
  const addedCount  = result?.added ?? 0;
  const dupCount    = result?.duplicates.length ?? 0;
  const errCount    = result?.errors.length ?? 0;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">CSV Import</h1>
      <p className="text-sm text-gray-500 mb-6">
        Bulk-import student accounts or historic parking session data.
      </p>

      {/* Mode tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {(["students", "historic"] as Mode[]).map((m) => (
          <button
            key={m}
            onClick={() => switchMode(m)}
            className={[
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              mode === m
                ? "border-green-600 text-green-700"
                : "border-transparent text-gray-500 hover:text-gray-800",
            ].join(" ")}
          >
            {MODE_LABELS[m]}
          </button>
        ))}
      </div>

      {/* Format guide */}
      {mode === "students" && (
        <Card padding="sm" className="mb-6 bg-blue-50 border-blue-100">
          <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">Expected CSV Format</p>
          <pre className="text-xs text-blue-900 font-mono bg-white rounded p-2 border border-blue-100">
{`email,plate,password
student@suny.edu,ABC1234,Temp123!
another@suny.edu,XYZ9876`}
          </pre>
          <p className="text-xs text-blue-600 mt-2">
            <strong>plate</strong> and <strong>password</strong> are optional.
            Default password: <code>Temp123!</code>
          </p>
        </Card>
      )}

      {mode === "historic" && (
        <Card padding="sm" className="mb-6 bg-amber-50 border-amber-100">
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-2">Expected CSV Format</p>
          <pre className="text-xs text-amber-900 font-mono bg-white rounded p-2 border border-amber-100 overflow-x-auto">
{`plate,zone,started_at,ended_at,user_type,session_type,payment_type,enforcement_status,notes
ABC1234,Lot A,2024-01-15 08:00,2024-01-15 09:30,STUDENT,STANDARD,TOKEN,NONE,
XYZ9876,Lot B,2024-01-15 10:00,,GUEST,EVENT,FREE,CHECKED,Event parking`}
          </pre>
          <div className="text-xs text-amber-700 mt-2 space-y-1">
            <p><strong>Required:</strong> plate, zone, started_at</p>
            <p><strong>Optional:</strong> ended_at, notes</p>
            <p><strong>user_type:</strong> STUDENT · GUEST · UNREGISTERED</p>
            <p><strong>session_type:</strong> STANDARD · PERMIT · EVENT</p>
            <p><strong>payment_type:</strong> TOKEN · CASH · CARD · FREE</p>
            <p><strong>enforcement_status:</strong> NONE · CHECKED · CITED</p>
            <p><strong>Date format:</strong> YYYY-MM-DD HH:MM</p>
            <p className="text-amber-600">Duplicate detection: same plate + started_at is skipped.</p>
          </div>
        </Card>
      )}

      {/* Drop zone */}
      <DropZone file={file} onFile={handleFile} />

      <div className="flex gap-3 mt-4">
        <Button
          onClick={upload}
          disabled={!file || uploading}
          loading={uploading}
          className="flex-1"
        >
          {uploading ? "Importing…" : MODE_LABELS[mode]}
        </Button>
        {file && (
          <Button
            variant="secondary"
            onClick={() => { setFile(null); setStudentResult(null); setHistoricResult(null); }}
            disabled={uploading}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Result summary */}
      {result && (
        <div className="mt-8 flex flex-col gap-4">
          <Alert variant={addedCount > 0 ? "success" : "info"}>
            <span className="font-semibold">
              {addedCount} {mode === "students" ? `student${addedCount !== 1 ? "s" : ""}` : `session${addedCount !== 1 ? "s" : ""}`} added
            </span>
            {dupCount > 0 && `, ${dupCount} duplicate${dupCount !== 1 ? "s" : ""} skipped`}
            {errCount > 0 && `, ${errCount} error${errCount !== 1 ? "s" : ""}`}
          </Alert>

          {result.duplicates.length > 0 && (
            <Card padding="sm">
              <p className="text-sm font-semibold text-gray-700 mb-3">Skipped Duplicates</p>
              <div className="flex flex-col gap-2">
                {result.duplicates.map((d) => (
                  <div key={d.row} className="flex items-start justify-between text-sm gap-2 py-1.5 border-b border-gray-100 last:border-0">
                    <div>
                      {"email" in d
                        ? <span className="font-medium text-gray-800">{(d as StudentImportRow).email}</span>
                        : <span className="font-mono font-medium text-gray-800">{(d as HistoricImportRow).plate}</span>}
                      {"plate" in d && (d as StudentImportRow).plate && (
                        <span className="text-gray-500 ml-1.5 font-mono text-xs">({(d as StudentImportRow).plate})</span>
                      )}
                      {"started_at" in d && (
                        <span className="text-gray-500 ml-1.5 text-xs">{(d as HistoricImportRow).started_at}</span>
                      )}
                      <p className="text-xs text-gray-400 mt-0.5">{d.reason}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-gray-400">Row {d.row}</span>
                      <Badge variant="ended" label="Skipped" />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {result.errors.length > 0 && (
            <Card padding="sm">
              <p className="text-sm font-semibold text-red-600 mb-3">Errors</p>
              <div className="flex flex-col gap-2">
                {result.errors.map((e) => (
                  <div key={e.row} className="flex items-start justify-between text-sm gap-2 py-1.5 border-b border-gray-100 last:border-0">
                    <div>
                      {"email" in e
                        ? <span className="font-medium text-gray-800">{(e as StudentImportRow).email || "(no email)"}</span>
                        : <span className="font-mono font-medium text-gray-800">{(e as HistoricImportRow).plate || "(no plate)"}</span>}
                      <p className="text-xs text-red-500 mt-0.5">{e.reason}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-gray-400">Row {e.row}</span>
                      <Badge variant="terminated" label="Error" />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
