import { useState, useRef } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

type ImportRow  = { row: number; email: string; plate: string | null; reason: string };
type ImportResult = { added: number; duplicates: ImportRow[]; errors: ImportRow[] };

export default function CsvImport() {
  const { showToast }                  = useToast();
  const inputRef                       = useRef<HTMLInputElement>(null);
  const [dragging,  setDragging]       = useState(false);
  const [file,      setFile]           = useState<File | null>(null);
  const [uploading, setUploading]      = useState(false);
  const [result,    setResult]         = useState<ImportResult | null>(null);

  function handleFile(f: File) {
    if (!f.name.toLowerCase().endsWith(".csv")) {
      showToast("error", "Only CSV files are accepted.");
      return;
    }
    setFile(f);
    setResult(null);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  async function upload() {
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<ImportResult>("/operator/import-students", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
      if (data.added > 0) showToast("success", `${data.added} student${data.added !== 1 ? "s" : ""} imported.`);
    } catch (err) {
      showToast("error", getErrorMessage(err, "Import failed."));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Import Students</h1>
      <p className="text-sm text-gray-500 mb-6">
        Upload a CSV file to bulk-create student accounts. Duplicates are skipped automatically.
      </p>

      {/* Format guide */}
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

      {/* Drop zone */}
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
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
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

      <div className="flex gap-3 mt-4">
        <Button
          onClick={upload}
          disabled={!file || uploading}
          loading={uploading}
          className="flex-1"
        >
          {uploading ? "Importing…" : "Import Students"}
        </Button>
        {file && (
          <Button
            variant="secondary"
            onClick={() => { setFile(null); setResult(null); }}
            disabled={uploading}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Result summary */}
      {result && (
        <div className="mt-8 flex flex-col gap-4">
          <Alert variant={result.added > 0 ? "success" : "info"}>
            <span className="font-semibold">{result.added} student{result.added !== 1 ? "s" : ""} added</span>
            {result.duplicates.length > 0 && `, ${result.duplicates.length} duplicate${result.duplicates.length !== 1 ? "s" : ""} skipped`}
            {result.errors.length > 0 && `, ${result.errors.length} error${result.errors.length !== 1 ? "s" : ""}`}
          </Alert>

          {result.duplicates.length > 0 && (
            <Card padding="sm">
              <p className="text-sm font-semibold text-gray-700 mb-3">Skipped Duplicates</p>
              <div className="flex flex-col gap-2">
                {result.duplicates.map((d) => (
                  <div key={d.row} className="flex items-start justify-between text-sm gap-2 py-1.5 border-b border-gray-100 last:border-0">
                    <div>
                      <span className="font-medium text-gray-800">{d.email}</span>
                      {d.plate && <span className="text-gray-500 ml-1.5 font-mono text-xs">({d.plate})</span>}
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
                      <span className="font-medium text-gray-800">{e.email || "(no email)"}</span>
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
