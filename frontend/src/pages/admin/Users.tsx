import { useState, useEffect } from "react";
import api, { getErrorMessage } from "@/api/client";
import { useToast } from "@/components/ToastProvider";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/Input";
import { PageSpinner } from "@/components/ui/Spinner";

type AppUser = {
  id:    number;
  email: string;
  role:  string;
};

const ROLE_BADGE: Record<string, "active" | "terminated" | "neutral" | "ended"> = {
  PARKER:      "active",
  ENFORCEMENT: "ended",
  OPERATOR:    "neutral",
  ADMIN:       "terminated",
  GUEST:       "neutral",
};

function fmt(cents: number) { return `$${(cents / 100).toFixed(2)}`; }

// ── Credit dialog ─────────────────────────────────────────────────────────────

function CreditDialog({ user, onDone, onCancel }: {
  user:     AppUser;
  onDone:   () => void;
  onCancel: () => void;
}) {
  const { showToast }                 = useToast();
  const [amount,  setAmount]          = useState("");
  const [desc,    setDesc]            = useState("Admin credit");
  const [loading, setLoading]         = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const cents = Math.round(parseFloat(amount) * 100);
    if (!cents || cents <= 0) { showToast("error", "Enter a valid dollar amount."); return; }
    setLoading(true);
    try {
      await api.post("/admin/balance/credit", {
        user_id:     user.id,
        amount:      cents,
        description: desc.trim() || "Admin credit",
      });
      showToast("success", `${fmt(cents)} credited to ${user.email}.`);
      onDone();
    } catch (err) {
      showToast("error", getErrorMessage(err, "Credit failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-1">Credit Balance</h3>
        <p className="text-sm text-gray-500 mb-4">{user.email}</p>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <TextInput
            label="Amount ($)"
            placeholder="10.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            type="number"
            min="0.01"
            step="0.01"
            disabled={loading}
          />
          <TextInput
            label="Description"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            disabled={loading}
          />
          <div className="flex gap-2 pt-1">
            <Button type="submit" loading={loading} className="flex-1">Credit</Button>
            <Button variant="secondary" onClick={onCancel} disabled={loading}>Cancel</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminUsers() {
  const { showToast }                   = useToast();
  const [users,     setUsers]           = useState<AppUser[]>([]);
  const [loading,   setLoading]         = useState(true);
  const [filter,    setFilter]          = useState("");
  const [crediting, setCrediting]       = useState<AppUser | null>(null);

  useEffect(() => {
    api.get<AppUser[]>("/admin/users")
      .then(({ data }) => setUsers(data))
      .catch((err) => showToast("error", getErrorMessage(err, "Failed to load users.")))
      .finally(() => setLoading(false));
  }, []);

  const visible = filter
    ? users.filter((u) => u.email.toLowerCase().includes(filter.toLowerCase()) || u.role.includes(filter.toUpperCase()))
    : users;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Users</h1>
      <p className="text-sm text-gray-500 mb-6">All accounts in the system.</p>

      {loading && <PageSpinner />}

      {!loading && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <TextInput
              className="w-64"
              placeholder="Filter by email or role…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <p className="text-xs text-gray-400">{visible.length} of {users.length}</p>
          </div>

          {visible.length === 0 ? (
            <Alert variant="info">No users match your filter.</Alert>
          ) : (
            <Card padding="sm">
              <table className="w-full">
                <thead>
                  <tr>
                    {["ID", "Email", "Role", "Actions"].map((h) => (
                      <th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-2.5 bg-gray-50 first:rounded-tl-lg last:rounded-tr-lg">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {visible.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2.5 text-sm border-b border-gray-100 text-gray-400 font-mono">
                        #{u.id}
                      </td>
                      <td className="px-3 py-2.5 text-sm border-b border-gray-100 font-medium text-gray-900">
                        {u.email}
                      </td>
                      <td className="px-3 py-2.5 text-sm border-b border-gray-100">
                        <Badge variant={ROLE_BADGE[u.role] ?? "neutral"} label={u.role} />
                      </td>
                      <td className="px-3 py-2.5 text-sm border-b border-gray-100">
                        {u.role === "PARKER" && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setCrediting(u)}
                          >
                            Credit Balance
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </>
      )}

      {crediting && (
        <CreditDialog
          user={crediting}
          onDone={() => setCrediting(null)}
          onCancel={() => setCrediting(null)}
        />
      )}
    </div>
  );
}
