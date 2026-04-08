const BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Types ──────────────────────────────────────────

export interface Target {
  id: number;
  username: string;
  display_name: string | null;
  is_active: boolean;
  created_at: string;
  last_scraped_at: string | null;
}

export interface Tweet {
  id: number;
  tweet_id: string;
  target_id: number | null;
  author_username: string;
  author_display_name: string | null;
  content: string;
  created_at: string;
  scraped_at: string;
  likes_count: number;
  retweets_count: number;
  replies_count: number;
  views_count: number;
  sentiment_score: number | null;
  sentiment_label: string | null;
  category: string | null;
  target_username: string | null;
}

export interface AnalysisResponse {
  id: number;
  summary: string;
  tweet_count: number;
  username: string;
  start_date: string;
  end_date: string;
  created_at: string;
}

export interface AnalysisListItem {
  id: number;
  target_id: number;
  username: string;
  start_date: string;
  end_date: string;
  tweet_count: number;
  created_at: string;
}

export interface Schedule {
  id: number;
  task_name: string;
  description: string | null;
  interval_seconds: number;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string;
  created_at: string;
}

export interface CredentialStatus {
  has_auth_token: boolean;
  has_ct0: boolean;
  configured: boolean;
}

// ── Targets ────────────────────────────────────────

export const getTargets = () => request<Target[]>("/api/targets");
export const addTarget = (username: string, display_name?: string) =>
  request<Target>("/api/targets", {
    method: "POST",
    body: JSON.stringify({ username, display_name }),
  });
export const removeTarget = (id: number) =>
  request<{ status: string }>(`/api/targets/${id}`, { method: "DELETE" });

// ── Tweets ─────────────────────────────────────────

export const getTweets = (params?: {
  target_id?: number;
  sentiment?: string;
  category?: string;
  limit?: number;
  offset?: number;
}) => {
  const q = new URLSearchParams();
  if (params?.target_id) q.set("target_id", String(params.target_id));
  if (params?.sentiment) q.set("sentiment", params.sentiment);
  if (params?.category) q.set("category", params.category);
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  return request<{ tweets: Tweet[]; total: number }>(`/api/tweets?${q}`);
};

// ── Analysis ───────────────────────────────────────

export const runAnalysis = (target_id: number, start_date: string, end_date: string) =>
  request<AnalysisResponse>("/api/analysis", {
    method: "POST",
    body: JSON.stringify({ target_id, start_date, end_date }),
  });

export const getAnalyses = (target_id?: number) => {
  const q = target_id ? `?target_id=${target_id}` : "";
  return request<AnalysisListItem[]>(`/api/analysis${q}`);
};

export const getAnalysis = (id: number) =>
  request<AnalysisResponse>(`/api/analysis/${id}`);

export const deleteAnalysis = (id: number) =>
  request<{ status: string }>(`/api/analysis/${id}`, { method: "DELETE" });

// ── Schedules ──────────────────────────────────────

export const getSchedules = () => request<Schedule[]>("/api/schedules");

export const patchSchedule = (
  id: number,
  body: { interval_seconds?: number; is_active?: boolean },
) =>
  request<{ status: string }>(`/api/schedules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

export const runScheduleNow = (id: number) =>
  request<{ status: string; task: string; message: string }>(
    `/api/schedules/${id}/run`,
    { method: "POST" },
  );

// ── Credentials ────────────────────────────────────

export const getCredentials = () => request<CredentialStatus>("/api/credentials");

export const saveCredentials = (auth_token: string, ct0: string) =>
  request<{ status: string }>("/api/credentials", {
    method: "PUT",
    body: JSON.stringify({ auth_token, ct0 }),
  });

export const deleteCredentials = () =>
  request<{ status: string }>("/api/credentials", { method: "DELETE" });

// ── Scraper settings ───────────────────────────────

export interface ScraperSettings {
  max_scrolls: number;
}

export const getScraperSettings = () =>
  request<ScraperSettings>("/api/scraper-settings");

export const updateScraperSettings = (body: ScraperSettings) =>
  request<{ status: string }>("/api/scraper-settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });

// ── Pipeline triggers ──────────────────────────────

export const triggerScrape = () =>
  request<{ status: string; tweets_upserted?: number }>("/api/scrape", { method: "POST" });
export const triggerAnalyze = () =>
  request<{ status: string; analyzed?: number }>("/api/analyze", { method: "POST" });
