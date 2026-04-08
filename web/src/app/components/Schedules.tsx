"use client";

import { useEffect, useState } from "react";
import {
  getSchedules,
  patchSchedule,
  runScheduleNow,
  type Schedule,
} from "@/lib/api";

const PRESET_INTERVALS = [
  { label: "5 min", value: 300 },
  { label: "15 min", value: 900 },
  { label: "30 min", value: 1800 },
  { label: "1 hour", value: 3600 },
  { label: "2 hours", value: 7200 },
  { label: "6 hours", value: 21600 },
  { label: "12 hours", value: 43200 },
  { label: "24 hours", value: 86400 },
];

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1).replace(/\.0$/, "")}h`;
  return `${(seconds / 86400).toFixed(1).replace(/\.0$/, "")}d`;
}

function timeUntil(dateStr: string): string {
  const diff = new Date(dateStr).getTime() - Date.now();
  if (diff <= 0) return "due now";
  const secs = Math.round(diff / 1000);
  if (secs < 60) return `in ${secs}s`;
  if (secs < 3600) return `in ${Math.round(secs / 60)}m`;
  return `in ${(secs / 3600).toFixed(1)}h`;
}

export default function Schedules() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [editId, setEditId] = useState<number | null>(null);
  const [editInterval, setEditInterval] = useState<number>(3600);
  const [runningId, setRunningId] = useState<number | null>(null);

  const load = () => {
    getSchedules().then(setSchedules).catch(console.error);
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, []);

  const flash = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handlePatch = async (id: number, body: { interval_seconds?: number; is_active?: boolean }) => {
    try {
      await patchSchedule(id, body);
      flash("Schedule updated");
      load();
      setEditId(null);
    } catch (e: unknown) {
      flash(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const handleRunNow = async (id: number, taskName: string) => {
    setRunningId(id);
    flash(`Running ${taskName}...`);
    try {
      await runScheduleNow(id);
      flash(`${taskName} started in background`);
      load();
    } catch (e: unknown) {
      flash(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setRunningId(null);
    }
  };

  return (
    <>
      <div className="section-header">
        <h2>Schedules</h2>
        <span style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
          Worker polls every 30s
        </span>
      </div>

      <div className="card">
        {schedules.length === 0 ? (
          <p className="empty">No scheduled tasks found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Description</th>
                <th>Interval</th>
                <th>Status</th>
                <th>Last run</th>
                <th>Next run</th>
                <th></th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {schedules.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600 }}>{s.task_name}</td>
                  <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                    {s.description || "—"}
                  </td>
                  <td>
                    {editId === s.id ? (
                      <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
                        <select
                          value={editInterval}
                          onChange={(e) => setEditInterval(Number(e.target.value))}
                          style={{ width: "100px" }}
                        >
                          {PRESET_INTERVALS.map((p) => (
                            <option key={p.value} value={p.value}>
                              {p.label}
                            </option>
                          ))}
                        </select>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handlePatch(s.id, { interval_seconds: editInterval })}
                        >
                          Save
                        </button>
                        <button
                          className="btn btn-sm"
                          onClick={() => setEditId(null)}
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <span
                        style={{ cursor: "pointer", borderBottom: "1px dashed var(--muted)" }}
                        onClick={() => {
                          setEditId(s.id);
                          setEditInterval(s.interval_seconds);
                        }}
                        title="Click to edit"
                      >
                        {formatDuration(s.interval_seconds)}
                      </span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${s.is_active ? "positive" : "neutral"}`}>
                      {s.is_active ? "active" : "paused"}
                    </span>
                  </td>
                  <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                    {s.last_run_at
                      ? new Date(s.last_run_at).toLocaleString()
                      : "never"}
                  </td>
                  <td style={{ fontSize: "0.8rem" }}>
                    {s.is_active ? (
                      <span style={{ color: "var(--accent)" }}>
                        {timeUntil(s.next_run_at)}
                      </span>
                    ) : (
                      <span style={{ color: "var(--muted)" }}>—</span>
                    )}
                  </td>
                  <td>
                    <button
                      className={`btn btn-sm ${s.is_active ? "btn-danger" : "btn-primary"}`}
                      onClick={() => handlePatch(s.id, { is_active: !s.is_active })}
                    >
                      {s.is_active ? "Pause" : "Resume"}
                    </button>
                  </td>
                  <td>
                    <button
                      className="btn btn-sm btn-primary"
                      disabled={runningId === s.id}
                      onClick={() => handleRunNow(s.id, s.task_name)}
                    >
                      {runningId === s.id ? "Running…" : "Run Now"}
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
