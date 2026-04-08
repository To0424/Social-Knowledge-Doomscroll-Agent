"""PostgreSQL storage layer for tweets, targets, analyses, and settings."""

import logging

import psycopg2
import psycopg2.extras
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    def __init__(self, host: str, port: int, dbname: str, user: str, password: str):
        self._dsn = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        self._conn = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self):
        self._conn = psycopg2.connect(**self._dsn)
        self._conn.autocommit = True
        logger.info("Connected to PostgreSQL %s:%s/%s", self._dsn["host"], self._dsn["port"], self._dsn["dbname"])

    def close(self):
        if self._conn:
            self._conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def init_schema(self):
        sql = SCHEMA_PATH.read_text()
        with self._conn.cursor() as cur:
            cur.execute(sql)
        logger.info("Schema initialized")

    # ------------------------------------------------------------------
    # Targets
    # ------------------------------------------------------------------

    def add_target(self, username: str, display_name: str | None = None) -> dict:
        sql = """
            INSERT INTO targets (username, display_name)
            VALUES (%s, %s)
            ON CONFLICT (username) DO UPDATE SET
                is_active = true,
                display_name = COALESCE(EXCLUDED.display_name, targets.display_name)
            RETURNING id, username, display_name, is_active, created_at, last_scraped_at
        """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (username.lower().strip(), display_name))
            return dict(cur.fetchone())

    def remove_target(self, target_id: int):
        sql = "UPDATE targets SET is_active = false WHERE id = %s"
        with self._conn.cursor() as cur:
            cur.execute(sql, (target_id,))

    def get_targets(self, active_only: bool = True) -> list[dict]:
        sql = "SELECT * FROM targets"
        if active_only:
            sql += " WHERE is_active = true"
        sql += " ORDER BY created_at"
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def update_target_scraped(self, target_id: int):
        sql = "UPDATE targets SET last_scraped_at = now() WHERE id = %s"
        with self._conn.cursor() as cur:
            cur.execute(sql, (target_id,))

    # ------------------------------------------------------------------
    # Tweets
    # ------------------------------------------------------------------

    def upsert_tweets(self, tweets: list[dict], target_id: int | None = None) -> int:
        """Insert tweets, skipping duplicates. Returns number of new rows."""
        if not tweets:
            return 0

        sql = """
            INSERT INTO tweets (
                tweet_id, target_id, author_username, author_display_name,
                content, created_at, likes_count, retweets_count,
                replies_count, views_count, raw_data
            ) VALUES (
                %(tweet_id)s, %(target_id)s, %(author_username)s, %(author_display_name)s,
                %(content)s, %(created_at)s, %(likes_count)s, %(retweets_count)s,
                %(replies_count)s, %(views_count)s, %(raw_data)s
            )
            ON CONFLICT (tweet_id) DO UPDATE SET
                author_username    = EXCLUDED.author_username,
                author_display_name = EXCLUDED.author_display_name,
                likes_count    = EXCLUDED.likes_count,
                retweets_count = EXCLUDED.retweets_count,
                replies_count  = EXCLUDED.replies_count,
                views_count    = EXCLUDED.views_count
        """
        inserted = 0
        with self._conn.cursor() as cur:
            for t in tweets:
                row = {
                    "tweet_id": t["tweet_id"],
                    "target_id": target_id,
                    "author_username": t.get("author_username"),
                    "author_display_name": t.get("author_display_name"),
                    "content": t.get("content", ""),
                    "created_at": t.get("created_at"),
                    "likes_count": t.get("likes_count", 0),
                    "retweets_count": t.get("retweets_count", 0),
                    "replies_count": t.get("replies_count", 0),
                    "views_count": t.get("views_count", 0),
                    "raw_data": t.get("raw_data"),
                }
                cur.execute(sql, row)
                inserted += 1
        logger.info("Upserted %d tweets", inserted)
        return inserted

    def update_sentiment(self, tweet_id: str, score: float, label: str, category: str):
        sql = """
            UPDATE tweets
               SET sentiment_score = %s,
                   sentiment_label = %s,
                   category        = %s
             WHERE tweet_id = %s
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, (score, label, category, tweet_id))

    def get_unanalyzed_tweets(self, limit: int = 50) -> list[dict]:
        sql = """
            SELECT tweet_id, content, author_username, created_at,
                   likes_count, retweets_count, views_count
              FROM tweets
             WHERE sentiment_label IS NULL
             ORDER BY scraped_at DESC
             LIMIT %s
        """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            return [dict(r) for r in cur.fetchall()]

    def get_tweets(self, target_id: int | None = None, sentiment: str | None = None,
                   category: str | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
        conditions = []
        params: list = []
        if target_id is not None:
            conditions.append("t.target_id = %s")
            params.append(target_id)
        if sentiment:
            conditions.append("t.sentiment_label = %s")
            params.append(sentiment)
        if category:
            conditions.append("t.category = %s")
            params.append(category)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT t.id, t.tweet_id, t.author_username, t.author_display_name,
                   t.content, t.created_at, t.scraped_at,
                   t.likes_count, t.retweets_count, t.replies_count, t.views_count,
                   t.sentiment_score, t.sentiment_label, t.category,
                   tg.username AS target_username
              FROM tweets t
              LEFT JOIN targets tg ON t.target_id = tg.id
              {where}
             ORDER BY t.created_at DESC NULLS LAST
             LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_tweet_count(self, target_id: int | None = None,
                         sentiment: str | None = None,
                         category: str | None = None) -> int:
        conditions: list[str] = []
        params: list = []
        if target_id is not None:
            conditions.append("target_id = %s")
            params.append(target_id)
        if sentiment:
            conditions.append("sentiment_label = %s")
            params.append(sentiment)
        if category:
            conditions.append("category = %s")
            params.append(category)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"SELECT COUNT(*) FROM tweets {where}"
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]

    def get_recent_tweets(self, target_id: int | None = None, limit: int = 100) -> list[dict]:
        if target_id is not None:
            sql = """
                SELECT tweet_id, content, author_username, created_at,
                       likes_count, retweets_count, views_count,
                       sentiment_score, sentiment_label, category
                  FROM tweets WHERE target_id = %s
                 ORDER BY created_at DESC NULLS LAST LIMIT %s
            """
            params = (target_id, limit)
        else:
            sql = """
                SELECT tweet_id, content, author_username, created_at,
                       likes_count, retweets_count, views_count,
                       sentiment_score, sentiment_label, category
                  FROM tweets
                 ORDER BY created_at DESC NULLS LAST LIMIT %s
            """
            params = (limit,)
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_tweets_by_date_range(self, target_id: int, start_date: str, end_date: str,
                                  limit: int = 500) -> list[dict]:
        """Fetch tweets for a target within a date range (inclusive)."""
        sql = """
            SELECT tweet_id, content, author_username, created_at,
                   likes_count, retweets_count, views_count,
                   sentiment_score, sentiment_label, category
              FROM tweets
             WHERE target_id = %s
               AND created_at >= %s::date
               AND created_at < (%s::date + INTERVAL '1 day')
             ORDER BY created_at DESC
             LIMIT %s
        """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (target_id, start_date, end_date, limit))
            return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Analyses
    # ------------------------------------------------------------------

    def save_analysis(self, target_id: int, username: str, start_date: str,
                      end_date: str, tweet_count: int, summary: str) -> dict:
        sql = """
            INSERT INTO analyses (target_id, username, start_date, end_date, tweet_count, summary)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, target_id, username, start_date, end_date, tweet_count, summary, created_at
        """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (target_id, username, start_date, end_date, tweet_count, summary))
            return dict(cur.fetchone())

    def get_analyses(self, target_id: int | None = None, limit: int = 20) -> list[dict]:
        if target_id is not None:
            sql = """
                SELECT id, target_id, username, start_date, end_date,
                       tweet_count, summary, created_at
                  FROM analyses WHERE target_id = %s
                 ORDER BY created_at DESC LIMIT %s
            """
            params = (target_id, limit)
        else:
            sql = """
                SELECT id, target_id, username, start_date, end_date,
                       tweet_count, summary, created_at
                  FROM analyses ORDER BY created_at DESC LIMIT %s
            """
            params = (limit,)
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_analysis(self, analysis_id: int) -> dict | None:
        sql = """
            SELECT id, target_id, username, start_date, end_date,
                   tweet_count, summary, created_at
              FROM analyses WHERE id = %s
        """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (analysis_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def delete_analysis(self, analysis_id: int):
        sql = "DELETE FROM analyses WHERE id = %s"
        with self._conn.cursor() as cur:
            cur.execute(sql, (analysis_id,))

    def get_sentiment_summary(self, target_id: int | None = None) -> dict:
        if target_id is not None:
            sql = """
                SELECT sentiment_label, COUNT(*) AS cnt,
                       ROUND(AVG(sentiment_score)::numeric, 3) AS avg_score
                  FROM tweets WHERE sentiment_label IS NOT NULL AND target_id = %s
                 GROUP BY sentiment_label ORDER BY cnt DESC
            """
            params = (target_id,)
        else:
            sql = """
                SELECT sentiment_label, COUNT(*) AS cnt,
                       ROUND(AVG(sentiment_score)::numeric, 3) AS avg_score
                  FROM tweets WHERE sentiment_label IS NOT NULL
                 GROUP BY sentiment_label ORDER BY cnt DESC
            """
            params = ()
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return {r["sentiment_label"]: dict(r) for r in cur.fetchall()}

    def get_category_summary(self, target_id: int | None = None) -> list[dict]:
        if target_id is not None:
            sql = """
                SELECT category, COUNT(*) AS cnt,
                       ROUND(AVG(sentiment_score)::numeric, 3) AS avg_score
                  FROM tweets WHERE category IS NOT NULL AND target_id = %s
                 GROUP BY category ORDER BY cnt DESC
            """
            params = (target_id,)
        else:
            sql = """
                SELECT category, COUNT(*) AS cnt,
                       ROUND(AVG(sentiment_score)::numeric, 3) AS avg_score
                  FROM tweets WHERE category IS NOT NULL
                 GROUP BY category ORDER BY cnt DESC
            """
            params = ()
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Schedules
    # ------------------------------------------------------------------

    def get_schedules(self) -> list[dict]:
        sql = "SELECT * FROM schedules ORDER BY id"
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def get_due_schedules(self) -> list[dict]:
        """Return active schedules whose next_run_at <= now()."""
        sql = """
            SELECT * FROM schedules
             WHERE is_active = true AND next_run_at <= now()
             ORDER BY next_run_at
        """
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def mark_schedule_ran(self, schedule_id: int):
        """Update last_run_at to now and compute next_run_at."""
        sql = """
            UPDATE schedules
               SET last_run_at = now(),
                   next_run_at = now() + (interval_seconds * INTERVAL '1 second')
             WHERE id = %s
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, (schedule_id,))

    def update_schedule(self, schedule_id: int, interval_seconds: int | None = None,
                        is_active: bool | None = None):
        parts = []
        params: list = []
        if interval_seconds is not None:
            parts.append("interval_seconds = %s")
            params.append(interval_seconds)
        if is_active is not None:
            parts.append("is_active = %s")
            params.append(is_active)
        if not parts:
            return
        if interval_seconds is not None or is_active is True:
            parts.append("next_run_at = now() + (%s * INTERVAL '1 second')")
            params.append(interval_seconds if interval_seconds is not None else 3600)
        sql = f"UPDATE schedules SET {', '.join(parts)} WHERE id = %s"
        params.append(schedule_id)
        with self._conn.cursor() as cur:
            cur.execute(sql, params)

    # ------------------------------------------------------------------
    # Settings (key-value store)
    # ------------------------------------------------------------------

    def get_setting(self, key: str) -> str | None:
        sql = "SELECT value FROM settings WHERE key = %s"
        with self._conn.cursor() as cur:
            cur.execute(sql, (key,))
            row = cur.fetchone()
            return row[0] if row else None

    def set_setting(self, key: str, value: str):
        sql = """
            INSERT INTO settings (key, value, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, (key, value))

    def delete_setting(self, key: str):
        sql = "DELETE FROM settings WHERE key = %s"
        with self._conn.cursor() as cur:
            cur.execute(sql, (key,))


