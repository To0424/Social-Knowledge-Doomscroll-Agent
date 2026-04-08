-- socialscope schema

CREATE TABLE IF NOT EXISTS targets (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(120) UNIQUE NOT NULL,
    display_name    VARCHAR(240),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_scraped_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tweets (
    id              SERIAL PRIMARY KEY,
    tweet_id        VARCHAR(64) UNIQUE NOT NULL,
    target_id       INTEGER REFERENCES targets(id),
    author_username VARCHAR(120),
    author_display_name VARCHAR(240),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    likes_count     INTEGER DEFAULT 0,
    retweets_count  INTEGER DEFAULT 0,
    replies_count   INTEGER DEFAULT 0,
    views_count     BIGINT  DEFAULT 0,
    sentiment_score DOUBLE PRECISION,
    sentiment_label VARCHAR(20),
    category        VARCHAR(64),
    raw_data        JSONB
);

CREATE INDEX IF NOT EXISTS idx_tweets_created   ON tweets (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_sentiment ON tweets (sentiment_label);
CREATE INDEX IF NOT EXISTS idx_tweets_category  ON tweets (category);
CREATE INDEX IF NOT EXISTS idx_tweets_target    ON tweets (target_id);

-- ── Analysis history ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS analyses (
    id              SERIAL PRIMARY KEY,
    target_id       INTEGER NOT NULL REFERENCES targets(id),
    username        VARCHAR(120) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    tweet_count     INTEGER NOT NULL DEFAULT 0,
    summary         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analyses_target ON analyses (target_id, created_at DESC);

-- ── Scheduled tasks ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS schedules (
    id              SERIAL PRIMARY KEY,
    task_name       VARCHAR(120) UNIQUE NOT NULL,
    description     VARCHAR(512),
    interval_seconds INTEGER NOT NULL DEFAULT 3600,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_run_at     TIMESTAMPTZ,
    next_run_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed default tasks if table is empty
INSERT INTO schedules (task_name, description, interval_seconds)
VALUES
    ('scrape_x',          'Scrape tweets from all active targets',         3600),
    ('analyze_sentiment', 'Run sentiment analysis on unanalyzed tweets',   1800)
ON CONFLICT (task_name) DO NOTHING;

-- ── App settings (key-value, stores credentials etc.) ────────────────

CREATE TABLE IF NOT EXISTS settings (
    key         VARCHAR(120) PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
