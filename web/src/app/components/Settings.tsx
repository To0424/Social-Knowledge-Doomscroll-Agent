"use client";

import { useEffect, useState } from "react";
import {
  getCredentials,
  saveCredentials,
  deleteCredentials,
  getScraperSettings,
  updateScraperSettings,
  type CredentialStatus,
} from "@/lib/api";

export default function Settings() {
  const [status, setStatus] = useState<CredentialStatus | null>(null);
  const [authToken, setAuthToken] = useState("");
  const [ct0, setCt0] = useState("");
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [maxScrolls, setMaxScrolls] = useState(10);
  const [savingScrolls, setSavingScrolls] = useState(false);

  const loadStatus = () => {
    getCredentials().then(setStatus).catch(console.error);
  };

  const loadScraperSettings = () => {
    getScraperSettings()
      .then((s) => setMaxScrolls(s.max_scrolls))
      .catch(console.error);
  };

  useEffect(() => {
    loadStatus();
    loadScraperSettings();
  }, []);

  const flash = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const handleSave = async () => {
    if (!authToken.trim() || !ct0.trim()) {
      flash("Both cookies are required");
      return;
    }
    setSaving(true);
    try {
      await saveCredentials(authToken.trim(), ct0.trim());
      flash("Credentials saved");
      setAuthToken("");
      setCt0("");
      loadStatus();
    } catch (e: unknown) {
      flash(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    try {
      await deleteCredentials();
      flash("Credentials removed");
      loadStatus();
    } catch (e: unknown) {
      flash(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  return (
    <>
      <div className="section-header">
        <h2>Settings</h2>
      </div>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>X / Twitter Credentials</h3>

        {status && (
          <div style={{ marginBottom: "1rem" }}>
            <span className={`badge ${status.configured ? "positive" : "negative"}`}>
              {status.configured ? "Configured" : "Not configured"}
            </span>
            {status.configured && (
              <button
                className="btn btn-sm btn-danger"
                style={{ marginLeft: "0.75rem" }}
                onClick={handleRemove}
              >
                Remove
              </button>
            )}
          </div>
        )}

        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1rem", lineHeight: 1.6 }}>
          To scrape X, the app needs your browser cookies. Steps:<br />
          1. Open <strong>x.com</strong> and make sure you&#39;re logged in<br />
          2. Press <strong>F12</strong> → Application → Cookies → https://x.com<br />
          3. Copy the values of <code>auth_token</code> and <code>ct0</code><br />
          4. Paste them below and click Save
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: "500px" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.25rem" }}>
              auth_token
            </label>
            <input
              type="password"
              value={authToken}
              onChange={(e) => setAuthToken(e.target.value)}
              placeholder="Paste auth_token cookie value"
              style={{ width: "100%" }}
            />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.25rem" }}>
              ct0
            </label>
            <input
              type="password"
              value={ct0}
              onChange={(e) => setCt0(e.target.value)}
              placeholder="Paste ct0 cookie value"
              style={{ width: "100%" }}
            />
          </div>
          <button
            className="btn btn-primary"
            disabled={saving || !authToken.trim() || !ct0.trim()}
            onClick={handleSave}
            style={{ alignSelf: "flex-start" }}
          >
            {saving ? "Saving…" : "Save Credentials"}
          </button>
        </div>
      </div>

      {/* ── Scraper Settings ── */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>Scraper Settings</h3>

        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1rem", lineHeight: 1.6 }}>
          Control how deep the scraper scrolls on each target&#39;s profile page.
          Each scroll loads roughly 20 more tweets. Higher values collect more tweets
          but take longer.
        </p>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end", maxWidth: "500px" }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.25rem" }}>
              Max Scrolls <span style={{ color: "var(--muted)", fontWeight: 400 }}>(1–100, default 10)</span>
            </label>
            <input
              type="number"
              min={1}
              max={100}
              value={maxScrolls}
              onChange={(e) => setMaxScrolls(Number(e.target.value))}
              style={{ width: "100%" }}
            />
          </div>
          <button
            className="btn btn-primary"
            disabled={savingScrolls || maxScrolls < 1 || maxScrolls > 100}
            onClick={async () => {
              setSavingScrolls(true);
              try {
                await updateScraperSettings({ max_scrolls: maxScrolls });
                flash("Scraper settings saved");
              } catch (e: unknown) {
                flash(`Failed: ${e instanceof Error ? e.message : String(e)}`);
              } finally {
                setSavingScrolls(false);
              }
            }}
          >
            {savingScrolls ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </>
  );
}
