# SocialScope

A self-hosted social media intelligence agent that continuously monitors X (Twitter) accounts to extract trends, sentiment, and actionable insights — powered entirely by a local LLM (Ollama).

## Features

- **Automated Scraping** — Playwright-based headless browser scrapes tweets from any public X profile on a configurable schedule.
- **Sentiment Analysis** — Every scraped tweet is scored as positive / neutral / negative and categorised by topic using Ollama.
- **On-Demand Analysis** — Select a target account and a date range, and the local LLM generates a structured Markdown summary of themes, sentiment shifts, notable tweets, and trends.
- **Analysis History** — Every generated summary is saved to the database and can be reviewed or deleted later from the dashboard.
- **Web Dashboard** — Next.js UI with five tabs: Targets, Tweets, Analysis, Schedules, and Settings.
- **Configurable Scraper Depth** — Adjust how many page scrolls the scraper performs per target from the Settings page (each scroll ≈ 20 tweets).
- **Fully Dockerised** — One command to start. No local Python/Node install required.
- **GPU Support** — Optional GPU-accelerated Ollama for faster LLM inference.

---

## G2 Success Criteria

> **G2: Social Knowledge "Doomscroll" Agent** — Build an agent that continuously monitors a social platform to extract market insights, trends, or sentiment.

### 1. Agent can fetch and parse content from 1 platform

SocialScope scrapes **X (Twitter)** using **Playwright** (headless Chromium). It navigates to each target's profile, intercepts the GraphQL `UserTweets` / `UserTweetsAndReplies` API responses, and extracts structured tweet data (text, timestamps, engagement metrics). The scraper runs automatically on a configurable schedule (default: every hour) or can be triggered manually from the dashboard.

| Component | Implementation |
|---|---|
| Platform | X / Twitter |
| Scraping tool | Playwright (headless browser) |
| Data captured | Tweet text, author, timestamp, likes, retweets, replies, views |
| Scheduling | Built-in task scheduler with configurable intervals |
| Auth | Uses browser cookies (auth_token + ct0) stored in the database |

### 2. Stores insights with timestamps and basic categorisation

Every scraped tweet is persisted in **PostgreSQL** with full metadata. An automated **sentiment analysis** pipeline (running via Ollama) labels each tweet with:

- **Sentiment** — `positive`, `neutral`, or `negative` with a confidence score
- **Category** — topic classification (e.g. `Technology`, `Politics`, `Business`, `Entertainment`)
- **Timestamp** — original tweet creation time + scrape time

The Tweets tab in the dashboard lets users filter by target, sentiment, and category with pagination.

### 3. Demonstrates one actionable insight generated from aggregated data

The **Analysis** feature lets users select a target account and date range, then generates a structured Markdown report via Ollama that includes:

- **Key themes and topics** — dominant subjects and recurring talking points
- **Sentiment overview** — overall tone and notable shifts during the period
- **Notable tweets** — the most impactful or viral posts with cited snippets
- **Trends** — changes over the time range (e.g. increased negativity, new topics)
- **Actionable takeaway** — a concise paragraph summarising the most important insight

All generated analyses are saved with timestamps and can be reviewed from the **Past Analyses** history table.

### Reference Stack Mapping

| Required | SocialScope Implementation |
|---|---|
| **Scraping**: Playwright, Puppeteer, or Lightpanda | **Playwright** — headless Chromium via `playwright.async_api` |
| **Memory**: Vector store or simple JSON log for trend tracking | **PostgreSQL** — relational DB storing tweets, sentiment scores, categories, and analysis history with timestamps |
| **Analysis**: Summarisation, topic clustering, or sentiment scoring | **Ollama (gemma4)** — automated sentiment scoring + on-demand summarisation with theme/trend analysis |
| **Workflow**: n8n/Dify for scheduling + data pipeline | **Built-in task scheduler** (`task_manager/runner.py`) with configurable intervals, running scrape → sentiment → analysis pipeline |

---

## Quick Start

### Prerequisites

- **Docker Desktop** (Windows/macOS) or **Docker Engine + Docker Compose** (Linux)
- **~8 GB disk space** for the Ollama model (`gemma4:e2b`)
- A logged-in **X (Twitter)** account for cookie-based authentication

### 1. Clone and configure

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work out of the box):

```ini
POSTGRES_PASSWORD=changeme
LLM_MODEL=gemma4:e2b
MAX_SCROLLS=10
```

### 2. Start all services

**PowerShell (Windows):**

```powershell
.\start.ps1          # Starts infra + app + scheduler + pgAdmin
.\start.ps1 -GPU     # Same but with GPU-accelerated Ollama
```

**Or use Docker Compose directly:**

```bash
docker compose -f docker-compose.yml \
               -f docker-compose.app.yml \
               -f docker-compose.scheduler.yml \
               --profile pgadmin \
               up -d --build
```

This starts **6 containers**:

| Container | Port | Purpose |
|---|---|---|
| `postgres` | 5432 | PostgreSQL database |
| `ollama` | 11434 | Local LLM server |
| `api` | 8000 | FastAPI backend |
| `web` | 3000 | Next.js dashboard |
| `scheduler` | — | Background task runner |
| `pgadmin` | 5050 | Database admin (optional) |

### 3. Add X credentials

1. Open the dashboard at **http://localhost:3000**
2. Go to **Settings**
3. Paste your `auth_token` and `ct0` cookies from X (obtainable from browser DevTools → Application → Cookies)

### 4. Add a target

1. Go to the **Targets** tab
2. Enter an X username (e.g. `elonmusk`) and click **Add**
3. The scraper will pick it up on the next scheduled run, or trigger it manually from **Schedules**

### 5. Analyse

1. Wait for tweets to be scraped and sentiment-analysed (check the **Tweets** tab)
2. Go to the **Analysis** tab
3. Select the target, pick a date range, and click **Analyze**
4. The LLM generates a Markdown summary — past analyses are listed below

### Stopping

```powershell
.\stop.ps1            # Stop all containers (data is preserved)
.\stop.ps1 -Volumes   # Stop and delete all data volumes
```

---

## Dashboard Overview

### Targets

Add or remove X accounts to monitor. Shows last scraped time for each target.

### Tweets

Browse all scraped tweets with filters for target, sentiment, and category. Pagination adjusts to the filtered count.

### Analysis

Run on-demand LLM-powered summaries for a target + date range. Summary is rendered as Markdown with headings, bullet points, and tables. Past analyses are listed in a history table with View and Delete actions.

### Schedules

View and configure the two automated tasks:

- **scrape_x** — scrapes tweets from all active targets (default: every 60 minutes)
- **analyze_sentiment** — runs sentiment analysis on unprocessed tweets (default: every 30 minutes)

Each task can be toggled on/off, have its interval changed, or be triggered manually.

### Settings

- **X / Twitter Credentials** — manage browser cookies for scraping
- **Scraper Settings** — configure max scrolls per target (1–100, each scroll ≈ 20 tweets)

---

## How It Works

1. **Scraping**: Playwright navigates to an X user profile and intercepts the internal GraphQL `UserTweets`/`UserTweetsAndReplies` API responses. This captures structured JSON directly from X's backend — more reliable than DOM parsing.

2. **Storage**: Tweets are upserted into PostgreSQL with deduplication by `tweet_id`. Engagement metrics (likes, retweets, views) are updated on re-scrape.

3. **Sentiment Analysis**: Unanalyzed tweets are batched (chunks of 10) and sent to Ollama for sentiment scoring (-1.0 to 1.0), labeling (positive/negative/neutral), and topic categorization.

4. **On-Demand Analysis**: The user selects a target + date range. The API fetches matching tweets from the database and sends the 50 most recent to Ollama with a structured prompt. The model returns a Markdown summary that is saved to the database.

5. **Task Scheduler**: `task_manager/runner.py` polls the `schedules` table every 15 seconds (configurable via `WORKER_POLL_INTERVAL`, default 30 in Docker). When a task is due, it dispatches it from the `TASK_REGISTRY`. Default intervals: scrape (1h), sentiment (30m). Intervals and active state are adjustable via the dashboard.

---

## Trade-offs & Constraints

### GraphQL API interception vs. DOM parsing

**Chose**: Intercept X's internal `UserTweets`/`UserTweetsAndReplies` GraphQL responses via Playwright's network listener.

**Why**: DOM selectors break constantly as X deploys obfuscated class names. The GraphQL API returns structured JSON with all fields (engagement metrics, timestamps, user data). The trade-off is dependency on X's internal API structure, but it's still more stable than CSS selectors.

### Cookie-based auth vs. API keys

X has no public API for free-tier users. We use `auth_token` + `ct0` cookies exported from a logged-in browser session. This avoids the cost of X API Pro ($5,000+/mo) but means sessions need periodic refresh. Cookies can be updated from the dashboard Settings page.

### Local LLM (Ollama) vs. cloud APIs

**Chose**: Ollama with local models (e.g. `gemma4:e2b`).

**Why**: Zero cost per inference, no API rate limits, data stays local. Trade-off: slower inference and smaller context windows than cloud models, but adequate for batch sentiment scoring and short-form analysis.

### DB-based scheduling vs. dedicated tools

**Chose**: A simple polling loop (`task_manager/runner.py`) that checks a `schedules` table.

**Why**: Zero additional infrastructure — just another container running the same image. Trade-off: no retry queue, no distributed locking. Appropriate for a single-instance deployment.

### Split Docker Compose

**Chose**: Four composable files instead of one monolithic `docker-compose.yml`.

**Why**: Allows running only the services you need. Developing the frontend? Skip the scheduler. Want GPU? Add the GPU override. Need to inspect the DB? Add `--profile pgadmin`.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Docker Network                                │
│                                                                        │
│   ┌───────────┐       ┌───────────┐      ┌──────────────────────────┐  │
│   │  Next.js  │ ───▶ |  FastAPI  │ ───▶ │       PostgreSQL         │  │
│   │  (web)    │       │  (api)    │      │  targets · tweets        │  │
│   │  :3000    │       │  :8000    │ ◀──  │  analyses setting       │  │
│   └───────────┘       └─────┬─────┘      │  schedules               │  │
│                          │               └────────────▲─────────────┘  │
│                          │                            │                │
│                          ▼                            │                │
│                    ┌──────────┐           ┌───────────┐                │
│                    │  Ollama  │ ◀──────── │ Scheduler │──────▶ X.com  │
│                    │ (gemma4) │           │ scrape    │                │
│                    │  :11434  │           │ sentiment │                │
│                    └──────────┘           └───────────┘                │
└────────────────────────────────────────────────────────────────────────┘
```

**Data flow:**

1. **Scheduler** triggers `scrape_x` → Playwright scrapes X profiles → tweets stored in PostgreSQL
2. **Scheduler** triggers `analyze_sentiment` → unprocessed tweets sent to Ollama → sentiment + category written back
3. **User** opens Analysis tab → selects target + dates → API fetches tweets → Ollama generates summary → saved to DB
4. **Dashboard** reads everything from PostgreSQL via the FastAPI REST API

---

## HTTP API Reference

### Targets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/targets` | List all targets |
| `POST` | `/api/targets` | Add a target `{ "username": "..." }` |
| `DELETE` | `/api/targets/{id}` | Deactivate a target |

### Tweets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tweets?target_id=&sentiment=&category=&limit=&offset=` | Browse tweets with filters |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analysis` | Run analysis `{ "target_id", "start_date", "end_date" }` |
| `GET` | `/api/analysis` | List past analyses (optional `?target_id=`) |
| `GET` | `/api/analysis/{id}` | Get a single analysis |
| `DELETE` | `/api/analysis/{id}` | Delete an analysis |

### Schedules

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/schedules` | List all scheduled tasks |
| `PATCH` | `/api/schedules/{id}` | Update interval or toggle active |
| `POST` | `/api/schedules/{id}/run` | Trigger a task immediately |

### Credentials

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/credentials` | Check if credentials are configured |
| `PUT` | `/api/credentials` | Save X cookies `{ "auth_token", "ct0" }` |
| `DELETE` | `/api/credentials` | Remove stored credentials |

### Scraper Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/scraper-settings` | Get current scraper config |
| `PUT` | `/api/scraper-settings` | Update `{ "max_scrolls": 10 }` (1–100) |

### Pipeline Triggers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scrape` | Trigger scraping immediately |
| `POST` | `/api/analyze` | Trigger sentiment analysis immediately |
| `POST` | `/api/run` | Full pipeline: scrape → analyze |
| `GET` | `/api/stats?target_id=` | Sentiment/category summary + tweet count |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

---

## Project Structure

```
├── api/                        # FastAPI application
│   ├── __init__.py             # App factory with lifespan
│   ├── schemas.py              # Shared Pydantic models
│   └── routes/
│       ├── analysis.py         # POST/GET/DELETE analysis summaries
│       ├── credentials.py      # X cookie management
│       ├── pipeline.py         # Manual trigger endpoints
│       ├── schedules.py        # Schedule CRUD + run-now
│       ├── scraper_settings.py # Max scrolls configuration
│       ├── targets.py          # Target CRUD
│       └── tweets.py           # Tweet browsing with filters
├── db/
│   ├── database.py             # Database class with all SQL methods
│   └── schema.sql              # PostgreSQL schema (5 tables)
├── llm/
│   ├── client.py               # LLMClient wrapping Ollama's /v1 API
│   ├── sentiment.py            # Sentiment scoring prompt + parser
│   └── analysis.py             # Tweet summarisation prompt + builder
├── task_manager/
│   ├── runner.py               # Polling loop that checks schedules
│   ├── tasks/
│   │   ├── scrape_x.py         # Scrape all active targets
│   │   └── analyze_sentiment.py# Batch sentiment analysis
│   └── scraper/
│       └── x_client.py         # Playwright X scraper (GraphQL intercept)
├── web/                        # Next.js 15 dashboard
│   ├── Dockerfile              # Web container image
│   ├── package.json            # Node.js dependencies
│   ├── next.config.js          # Next.js config (proxy timeout)
│   ├── tsconfig.json           # TypeScript config
│   └── src/
│       ├── app/
│       │   ├── page.tsx        # Main page with tab navigation
│       │   ├── layout.tsx      # Root layout
│       │   ├── globals.css     # Global styles + Markdown CSS
│       │   └── components/
│       │       ├── Targets.tsx
│       │       ├── Tweets.tsx
│       │       ├── Analysis.tsx
│       │       ├── Schedules.tsx
│       │       └── Settings.tsx
│       └── lib/
│           └── api.ts          # Typed API client
├── config.py                   # Shared factories: get_db(), get_llm_client()
├── main.py                     # CLI entry point for scheduler
├── entrypoint.sh               # Ollama model pull + uvicorn start
├── Dockerfile                  # Python backend image
├── docker-compose.yml          # Infrastructure (Postgres, Ollama, pgAdmin)
├── docker-compose.app.yml      # API + Web
├── docker-compose.scheduler.yml# Background scheduler
├── docker-compose.gpu.yml      # GPU override for Ollama
├── start.ps1                   # Windows start script
├── stop.ps1                    # Windows stop script
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variable template
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Scraping | Playwright (async, Chromium) |
| Backend API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 |
| LLM | Ollama with gemma4:e2b (local, no API keys) |
| Frontend | Next.js 15, React 19, react-markdown |
| Containerisation | Docker Compose (4 Compose files) |

## Database Schema

| Table | Purpose |
|-------|---------|
| `targets` | X accounts to monitor (username, active flag, last scraped) |
| `tweets` | Scraped tweets with sentiment/category labels and engagement metrics |
| `analyses` | Saved LLM-generated summaries tied to target + date range |
| `schedules` | Task schedule configuration (interval, active, last run) |
| `settings` | Key–value store (credentials, scraper config) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `socialscope` | Database name |
| `POSTGRES_USER` | `socialscope` | Database user |
| `POSTGRES_PASSWORD` | `changeme` | Database password |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL |
| `LLM_MODEL` | `gemma4:e2b` | Ollama model to use |
| `MAX_SCROLLS` | `10` | Default scroll depth (overridden from Settings UI) |
| `WORKER_POLL_INTERVAL` | `30` | Scheduler polling interval in seconds (code default: 15) |
| `PGADMIN_EMAIL` | `admin@socialscope.dev` | pgAdmin login email |
| `PGADMIN_PASSWORD` | `admin` | pgAdmin login password |
