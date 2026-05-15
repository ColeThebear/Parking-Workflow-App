import { useState } from "react";
import type { KeyboardEvent } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card, CardRow } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TextInput } from "@/components/ui/Input";

type SessionResult = {
  plate:      string;
  zone:       string;
  start_time: string;
  expires_at: string | null;
  user_name?: string;
};

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function Lookup() {
  const { showToast } = useToast();

  const [plate,        setPlate]        = useState("");
  const [loading,      setLoading]      = useState(false);
  const [result,       setResult]       = useState<SessionResult | null>(null);
  const [searchedPlate, setSearchedPlate] = useState<string | null>(null);

  async function search() {
    const trimmed = plate.trim();
    if (!trimmed) return;

    setLoading(true);
    setResult(null);
    setSearchedPlate(null);

    try {
      const { data } = await api.get<{ success: boolean; data: SessionResult }>(
        "/enforcement/lookup",
        { params: { plate: trimmed } }
      );
      setSearchedPlate(trimmed);
      setResult(data.success ? data.data : null);
    } catch (err) {
      showToast("error", getErrorMessage(err, "Lookup failed."));
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") search();
  }

  const notFound = searchedPlate !== null && !result;

  return (
    <div className="max-w-md mx-auto px-4 py-10">
      <Card>
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Plate Lookup</h1>
        <p className="text-sm text-gray-500 mb-6">
          Enter a vehicle plate to check for an active parking session.
        </p>

        {/* Search input */}
        <div className="flex gap-2 mb-4">
          <TextInput
            className="flex-1 uppercase tracking-widest"
            placeholder="ABC1234"
            value={plate}
            onChange={(e) => {
              setPlate(e.target.value.toUpperCase());
              setResult(null);
              setSearchedPlate(null);
            }}
            onKeyDown={handleKeyDown}
            autoFocus
          />
          <Button
            onClick={search}
            disabled={!plate.trim() || loading}
            loading={loading}
          >
            Search
          </Button>
        </div>

        {/* Not found */}
        {notFound && (
          <Alert variant="info">
            No active session found for plate{" "}
            <strong className="font-mono tracking-widest">{searchedPlate}</strong>.
          </Alert>
        )}

        {/* Found */}
        {result && (
          <div className="rounded-xl bg-green-50 border border-green-200 p-4 mt-2">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-green-800">Active Session Found</p>
              <Badge variant="active" />
            </div>
            <CardRow label="Plate"   value={<span className="font-mono tracking-widest">{result.plate}</span>} />
            <CardRow label="Zone"    value={result.zone} />
            <CardRow label="Started" value={fmt(result.start_time)} />
            {result.expires_at && (
              <CardRow label="Expires" value={fmt(result.expires_at)} />
            )}
            {result.user_name && (
              <CardRow label="Registered To" value={result.user_name} />
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
