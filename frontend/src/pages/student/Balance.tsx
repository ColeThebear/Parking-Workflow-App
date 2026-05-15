import { useState, useEffect } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { PageSpinner } from "@/components/ui/Spinner";

type Transaction = {
  amount:      number;
  description: string;
  tx_type:     string;
  created_at:  string;
};

type BalanceData = {
  balance:      number;
  transactions: Transaction[];
};

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function fmtMoney(cents: number) {
  return `$${(Math.abs(cents) / 100).toFixed(2)}`;
}

export default function StudentBalance() {
  const { showToast }             = useToast();
  const [data,    setData]        = useState<BalanceData | null>(null);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    api.get<BalanceData>("/student/balance")
      .then(({ data }) => setData(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load balance.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">My Balance</h1>
      <p className="text-sm text-gray-500 mb-6">Parking credits and transaction history.</p>

      {loading && <PageSpinner />}

      {!loading && data && (
        <>
          {/* Balance card */}
          <Card className="mb-6 text-center py-8">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Available Balance
            </p>
            <p className="text-5xl font-bold text-gray-900">
              ${(data.balance / 100).toFixed(2)}
            </p>
            {data.balance <= 0 && (
              <p className="text-sm text-gray-400 mt-3">
                Contact the parking office to add funds.
              </p>
            )}
          </Card>

          {/* Transaction history */}
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Recent Transactions
          </h2>

          {data.transactions.length === 0 ? (
            <Alert variant="info">No transactions yet.</Alert>
          ) : (
            <div className="flex flex-col gap-2">
              {data.transactions.map((t, i) => (
                <Card key={i} padding="sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{t.description}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{fmt(t.created_at)}</p>
                    </div>
                    <p className={`text-sm font-bold shrink-0 ${t.amount >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {t.amount >= 0 ? "+" : "−"}{fmtMoney(t.amount)}
                    </p>
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
