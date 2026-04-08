"use client";

import { useEffect, useState } from "react";
import { getTweets, getTargets, type Tweet, type Target } from "@/lib/api";

const PAGE_SIZE = 30;

export default function Tweets() {
  const [tweets, setTweets] = useState<Tweet[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [targets, setTargets] = useState<Target[]>([]);

  // Filters
  const [targetId, setTargetId] = useState<number | undefined>();
  const [sentiment, setSentiment] = useState<string | undefined>();

  const load = () => {
    getTweets({
      target_id: targetId,
      sentiment,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    })
      .then((r) => {
        setTweets(r.tweets);
        setTotal(r.total);
      })
      .catch(console.error);
  };

  useEffect(() => {
    getTargets().then(setTargets).catch(console.error);
  }, []);

  useEffect(load, [targetId, sentiment, page]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const resetFilters = () => {
    setTargetId(undefined);
    setSentiment(undefined);
    setPage(0);
  };

  const badgeClass = (label: string | null) => {
    if (!label) return "";
    if (label === "positive") return "positive";
    if (label === "negative") return "negative";
    return "neutral";
  };

  return (
    <>
      <div className="section-header">
        <h2>Tweets</h2>
        <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
          {total} total
        </span>
      </div>

      {/* Filters */}
      <div className="filter-row">
        <select
          value={targetId ?? ""}
          onChange={(e) => {
            setTargetId(e.target.value ? Number(e.target.value) : undefined);
            setPage(0);
          }}
        >
          <option value="">All targets</option>
          {targets.map((t) => (
            <option key={t.id} value={t.id}>
              @{t.username}
            </option>
          ))}
        </select>

        <select
          value={sentiment ?? ""}
          onChange={(e) => {
            setSentiment(e.target.value || undefined);
            setPage(0);
          }}
        >
          <option value="">All sentiments</option>
          <option value="positive">Positive</option>
          <option value="negative">Negative</option>
          <option value="neutral">Neutral</option>
        </select>

        <button className="btn btn-sm" onClick={resetFilters}>
          Clear
        </button>
      </div>

      {/* Table */}
      <div className="card">
        {tweets.length === 0 ? (
          <p className="empty">No tweets found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ width: "100px" }}>Author</th>
                <th>Content</th>
                <th style={{ width: "90px" }}>Sentiment</th>
                <th style={{ width: "90px" }}>Category</th>
                <th style={{ width: "120px" }}>Posted</th>
              </tr>
            </thead>
            <tbody>
              {tweets.map((tw) => (
                <tr key={tw.id}>
                  <td>@{tw.author_username}</td>
                  <td style={{ maxWidth: "500px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {tw.content}
                  </td>
                  <td>
                    {tw.sentiment_label ? (
                      <span className={`badge ${badgeClass(tw.sentiment_label)}`}>
                        {tw.sentiment_label}
                      </span>
                    ) : (
                      <span style={{ color: "var(--muted)" }}>—</span>
                    )}
                  </td>
                  <td style={{ color: "var(--muted)" }}>{tw.category || "—"}</td>
                  <td style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
                    {new Date(tw.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-sm"
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
          >
            ← Prev
          </button>
          <span style={{ color: "var(--muted)", fontSize: "0.8rem", alignSelf: "center" }}>
            {page + 1} / {totalPages}
          </span>
          <button
            className="btn btn-sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage(page + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </>
  );
}
