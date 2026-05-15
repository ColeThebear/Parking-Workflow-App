import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { TextInput, SelectInput } from "@/components/ui/Input";

const PARKING_ZONES = ["Lot A", "Lot B", "Lot C", "Lot D", "Visitor Lot"];

export default function StartParking() {
  const { showToast } = useToast();
  const navigate  = useNavigate();
  const location  = useLocation();

  const [plate,   setPlate]   = useState("");
  const [zone,    setZone]    = useState("");
  const [loading, setLoading] = useState(false);

  // Shown once when the student returns after an operator-terminated session
  const terminatedByOperator = location.state?.terminatedByOperator === true;

  // On mount, redirect to active session if one already exists
  useEffect(() => {
    api.get("/student/active")
      .then(() => navigate("/student/active", { replace: true }))
      .catch(() => {});
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!plate.trim() || !zone) {
      showToast("error", "Please enter a plate number and select a zone.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/student/start", { plate: plate.trim().toUpperCase(), zone });
      showToast("success", "Parking session started.");
      navigate("/student/active", { replace: true });
    } catch (err) {
      showToast("error", getErrorMessage(err, "Failed to start session."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-10">
      {terminatedByOperator && (
        <Alert variant="warning" title="Session Ended by Campus Operations" className="mb-6">
          Your previous parking session was ended by campus operations. Please start a new session
          if you need to park.
        </Alert>
      )}

      <Card>
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Start Parking</h1>
        <p className="text-sm text-gray-500 mb-6">
          Enter your plate number and select a parking zone to begin.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <TextInput
            label="License Plate"
            placeholder="e.g. ABC1234"
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
            disabled={loading}
            className="uppercase tracking-widest"
          />

          <SelectInput
            label="Parking Zone"
            value={zone}
            onChange={(e) => setZone(e.target.value)}
            disabled={loading}
          >
            <option value="">Select a zone…</option>
            {PARKING_ZONES.map((z) => (
              <option key={z} value={z}>{z}</option>
            ))}
          </SelectInput>

          <Button
            type="submit"
            loading={loading}
            disabled={!plate.trim() || !zone}
            fullWidth
            className="mt-2"
          >
            Start Parking
          </Button>
        </form>
      </Card>
    </div>
  );
}
