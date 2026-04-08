"""Task: scrape_x — Scrape tweets from all active targets using Playwright."""

import logging
import os

logger = logging.getLogger(__name__)


async def task_scrape_x(db) -> dict:
    """Scrape all active targets and upsert tweets into the database."""
    from task_manager.scraper.x_client import XScraper

    targets = db.get_targets(active_only=True)
    if not targets:
        logger.info("No active targets")
        return {"tweets_upserted": 0}

    auth_token = db.get_setting("x_auth_token")
    ct0 = db.get_setting("x_ct0")

    # Read max_scrolls from DB settings, fall back to env var, then default 10
    max_scrolls_setting = db.get_setting("max_scrolls")
    max_scrolls = int(max_scrolls_setting) if max_scrolls_setting else int(os.getenv("MAX_SCROLLS", "10"))
    logger.info("Scraping with max_scrolls=%d", max_scrolls)

    total = 0
    errors = []
    for t in targets:
        try:
            scraper = XScraper(
                target_username=t["username"],
                max_scrolls=max_scrolls,
                headless=True,
            )
            tweets = await scraper.scrape(auth_token=auth_token, ct0=ct0)
            if tweets:
                count = db.upsert_tweets(tweets, target_id=t["id"])
                db.update_target_scraped(t["id"])
                total += count
                logger.info("Scraped %d tweets for @%s", count, t["username"])
        except Exception as exc:
            logger.error("Failed for @%s: %s", t["username"], exc, exc_info=True)
            errors.append(f"@{t['username']}: {exc}")

    logger.info("Total upserted: %d", total)
    result = {"tweets_upserted": total}
    if errors:
        result["errors"] = errors
    return result
