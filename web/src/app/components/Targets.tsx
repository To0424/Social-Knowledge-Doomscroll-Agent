"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  getTargets,
  addTarget,
  removeTarget,
  type Target,
} from "@/lib/api";

export default function Targets() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const load = () => {
    getTargets().then(setTargets).catch(console.error);
  };

  useEffect(load, []);

  const flash = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;
    setLoading(true);
    try {
      await addTarget(username.trim().replace(/^@/, ""), displayName.trim() || undefined);
      setUsername("");
      setDisplayName("");
      flash("Target added");
      load();
    } catch (err: unknown) {
      flash(`Failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (id: number) => {
    try {
      await removeTarget(id);
      flash("Target removed");
      load();
    } catch (err: unknown) {
      flash(`Failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <>
      <div className="section-header">
        <h2>Targets</h2>
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} className="card" style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.75rem" }}>
          Add Target
        </h3>
        <div className="filter-row">
          <input
            placeholder="Username (e.g. realDonaldTrump)"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ flex: 1, minWidth: "200px" }}
          />
          <input
            placeholder="Display name (optional)"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            style={{ flex: 1, minWidth: "200px" }}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <span className="spinner" /> : null}
            Add
          </button>
        </div>
      </form>

      {/* Table */}
      <div className="card">
        {targets.length === 0 ? (
          <p className="empty">No targets yet. Add one above.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Display name</th>
                <th>Status</th>
                <th>Last scraped</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {targets.map((t) => (
                <tr key={t.id}>
                  <td>@{t.username}</td>
                  <td>{t.display_name || "—"}</td>
                  <td>
                    <span className={`badge ${t.is_active ? "positive" : "neutral"}`}>
                      {t.is_active ? "active" : "paused"}
                    </span>
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {t.last_scraped_at
                      ? new Date(t.last_scraped_at).toLocaleString()
                      : "never"}
                  </td>
                  <td style={{ color: "var(--muted)" }}>
                    {new Date(t.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleRemove(t.id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {toast && <div className="toast">{toast}</div>}
    </>
  );
}
