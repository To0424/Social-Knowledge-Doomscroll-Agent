"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  getTargets,
  runAnalysis,
  getAnalyses,
  getAnalysis,
  deleteAnalysis,
  type Target,
  type AnalysisResponse,
  type AnalysisListItem,
} from "@/lib/api";

export default function Analysis() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [targetId, setTargetId] = useState<number | "">("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<AnalysisListItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadHistory = () => {
    setLoadingHistory(true);
    getAnalyses()
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoadingHistory(false));
  };

  useEffect(() => {
    getTargets().then(setTargets).catch(console.error);
    loadHistory();
  }, []);

  const handleAnalyze = async () => {
    if (!targetId || !startDate || !endDate) return;
    setBusy(true);
    setResult(null);
    setError(null);
    try {
      const res = await runAnalysis(Number(targetId), startDate, endDate);
      setResult(res);
      loadHistory();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleViewHistory = async (id: number) => {
    setError(null);
    try {
      const res = await getAnalysis(id);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteAnalysis(id);
      if (result?.id === id) setResult(null);
      loadHistory();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const fmtDate = (d: string) => {
    try {
      return new Date(d).toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return d;
    }
  };

  const fmtTime = (d: string) => {
    try {
      return new Date(d).toLocaleString(undefined, {
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
      });
    } catch {
      return d;
    }
  };

  return (
    <>
      <div className="section-header">
        <h2>Analysis</h2>
      </div>

      {/* ── New analysis form ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1rem", lineHeight: 1.6 }}>
          Select a target account and a date range, then click <strong>Analyze</strong> to
          generate a consolidated summary of their tweets using the local LLM.
        </p>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.25rem" }}>
              Account
            </label>
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value ? Number(e.target.value) : "")}
              style={{ minWidth: "180px" }}
            >
              <option value="">Select target…</option>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>
                  @{t.username}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.25rem" }}>
              From
            </label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.25rem" }}>
              To
            </label>
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>

          <button
            className="btn btn-primary"
            disabled={busy || !targetId || !startDate || !endDate}
            onClick={handleAnalyze}
          >
            {busy ? "Analyzing…" : "Analyze"}
          </button>
        </div>
      </div>

      {/* ── Loading / error states ── */}
      {busy && (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          <span className="spinner" style={{ width: "1.5rem", height: "1.5rem" }} />
          <p style={{ color: "var(--muted)", marginTop: "1rem" }}>
            Generating summary — this may take a moment…
          </p>
        </div>
      )}

      {error && (
        <div className="card" style={{ borderColor: "var(--negative)" }}>
          <p style={{ color: "var(--negative)" }}>Error: {error}</p>
        </div>
      )}

      {/* ── Current summary (rendered as Markdown) ── */}
      {result && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <h3 style={{ margin: 0 }}>Summary — @{result.username}</h3>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span className="badge neutral">{result.tweet_count} tweets</span>
              <span className="badge neutral">{fmtDate(result.start_date)} – {fmtDate(result.end_date)}</span>
            </div>
          </div>
          <div className="analysis-markdown">
            <ReactMarkdown>{result.summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* ── Past analyses ── */}
      <div className="card">
        <h3 style={{ marginBottom: "0.75rem" }}>Past Analyses</h3>
        {loadingHistory && <p style={{ color: "var(--muted)" }}>Loading…</p>}
        {!loadingHistory && history.length === 0 && (
          <p style={{ color: "var(--muted)" }}>No analyses yet. Run one above to get started.</p>
        )}
        {history.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Account</th>
                <th>Date Range</th>
                <th>Tweets</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>@{h.username}</td>
                  <td>{fmtDate(h.start_date)} – {fmtDate(h.end_date)}</td>
                  <td>{h.tweet_count}</td>
                  <td>{fmtTime(h.created_at)}</td>
                  <td style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                    <button className="btn btn-sm" onClick={() => handleViewHistory(h.id)}>
                      View
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(h.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
