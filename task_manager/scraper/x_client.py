"""
Playwright-based X/Twitter profile scraper.

Scrapes all tweets and replies from a specific user's profile by
intercepting X's internal GraphQL API responses (UserTweets /
UserTweetsAndReplies) — far more reliable than DOM selector parsing.

Auth flow: on first run, launches a visible browser for manual login,
then saves the session cookies for headless reuse.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Response

logger = logging.getLogger(__name__)

AUTH_DIR = Path("auth")
STORAGE_STATE_PATH = AUTH_DIR / "x_state.json"

# GraphQL endpoint fragments we intercept on a user profile page
_PROFILE_API_MARKERS = (
    "UserTweets",
    "UserTweetsAndReplies",
    "UserByScreenName",
)


class XScraper:
    def __init__(
        self,
        target_username: str,
        max_scrolls: int = 10,
        headless: bool = True,
    ):
        self.target_username = target_username
        self.max_scrolls = max_scrolls
        self.headless = headless
        self._collected: dict[str, dict] = {}
        self._pw = None
        self._browser = None
        self._context = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def login_from_cookies(auth_token: str, ct0: str):
        """Build a Playwright storage state from cookies copied from a real browser."""
        state = {
            "cookies": [
                {
                    "name": "auth_token",
                    "value": auth_token,
                    "domain": ".x.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "None",
                },
                {
                    "name": "ct0",
                    "value": ct0,
                    "domain": ".x.com",
                    "path": "/",
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "Lax",
                },
            ],
            "origins": [],
        }
        AUTH_DIR.mkdir(parents=True, exist_ok=True)
        STORAGE_STATE_PATH.write_text(json.dumps(state, indent=2))
        logger.info("Session saved to %s", STORAGE_STATE_PATH)

    async def scrape(self, auth_token: str | None = None, ct0: str | None = None) -> list[dict]:
        """Scrape all tweets & replies from the target user's profile.

        If auth_token and ct0 are provided (e.g. from the DB), the session
        file is written/refreshed before launching the browser.
        """
        if auth_token and ct0:
            self.login_from_cookies(auth_token, ct0)

        if not STORAGE_STATE_PATH.exists():
            if self.headless:
                raise RuntimeError(
                    "No session file found at auth/x_state.json. "
                    "Run 'python main.py login' first to save X cookies."
                )
            logger.warning("No saved session found — launching interactive login.")
            await self.login()

        await self._setup_browser()
        try:
            page = await self._context.new_page()
            page.on("response", self._on_response)

            url = f"https://x.com/{self.target_username}/with_replies"
            logger.info("Navigating to %s", url)
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(5000)

            prev_count = 0
            stall_rounds = 0
            for i in range(1, self.max_scrolls + 1):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                logger.info(
                    "Scroll %d/%d — %d tweets collected",
                    i, self.max_scrolls, len(self._collected),
                )
                if len(self._collected) == prev_count:
                    stall_rounds += 1
                    if stall_rounds >= 3:
                        logger.info("No new tweets after 3 scrolls — stopping early.")
                        break
                else:
                    stall_rounds = 0
                prev_count = len(self._collected)

            await self._context.storage_state(path=str(STORAGE_STATE_PATH))
        finally:
            await self._teardown()

        tweets = list(self._collected.values())
        logger.info("Scraping complete — %d unique tweets", len(tweets))
        return tweets

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    async def _setup_browser(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx_opts: dict = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        }
        if STORAGE_STATE_PATH.exists():
            ctx_opts["storage_state"] = str(STORAGE_STATE_PATH)
        self._context = await self._browser.new_context(**ctx_opts)

    async def _teardown(self):
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    # ------------------------------------------------------------------
    # API interception
    # ------------------------------------------------------------------

    async def _on_response(self, response: Response):
        """Intercept X's UserTweets / UserTweetsAndReplies GraphQL endpoints."""
        url = response.url
        if not any(marker in url for marker in _PROFILE_API_MARKERS):
            return
        try:
            body = await response.json()
            self._extract_tweets(body)
        except Exception:
            logger.debug("Failed to parse API response from %s", url, exc_info=True)

    def _extract_tweets(self, obj, depth: int = 0):
        """Walk the nested GraphQL payload and extract tweet objects."""
        if depth > 30:
            return
        if isinstance(obj, dict):
            legacy = obj.get("legacy")
            if isinstance(legacy, dict) and "full_text" in legacy:
                parsed = self._parse_tweet(obj)
                if parsed and parsed["tweet_id"] not in self._collected:
                    self._collected[parsed["tweet_id"]] = parsed
            for v in obj.values():
                self._extract_tweets(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_tweets(item, depth + 1)

    # ------------------------------------------------------------------
    # Tweet parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_tweet(tweet_obj: dict) -> dict | None:
        try:
            legacy = tweet_obj["legacy"]
            user_result = (
                tweet_obj.get("core", {})
                .get("user_results", {})
                .get("result", {})
            )
            user_core = user_result.get("core", {})
            user_legacy = user_result.get("legacy", {})
            screen_name = (
                user_core.get("screen_name")
                or user_legacy.get("screen_name", "unknown")
            )
            display_name = (
                user_core.get("name")
                or user_legacy.get("name", "")
            )
            created_at = XScraper._parse_x_date(legacy.get("created_at", ""))
            return {
                "tweet_id": legacy.get("id_str", ""),
                "author_username": screen_name,
                "author_display_name": display_name,
                "content": legacy.get("full_text", ""),
                "created_at": created_at,
                "likes_count": legacy.get("favorite_count", 0),
                "retweets_count": legacy.get("retweet_count", 0),
                "replies_count": legacy.get("reply_count", 0),
                "views_count": int(
                    tweet_obj.get("views", {}).get("count", 0) or 0
                ),
                "raw_data": json.dumps(tweet_obj, default=str),
            }
        except Exception as exc:
            logger.debug("Failed to parse tweet: %s", exc)
            return None

    @staticmethod
    def _parse_x_date(date_str: str) -> datetime | None:
        try:
            return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
        except (ValueError, TypeError):
            return None
