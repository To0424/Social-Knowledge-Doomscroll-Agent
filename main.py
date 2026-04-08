#!/usr/bin/env python3
"""
SocialScope — Social Media Intelligence Agent
CLI entrypoint for login and manual commands.

Usage:
    python main.py login                     # one-time: save X cookies
    python main.py add-target <username>     # add a scrape target
    python main.py scrape                    # scrape all active targets → PostgreSQL
    python main.py analyze                   # run sentiment analysis on new tweets
    python main.py run                       # scrape → analyze (full pipeline)
"""

import argparse
import asyncio
import json
import logging

from config import get_db
from task_manager.scraper.x_client import XScraper
from task_manager.tasks.scrape_x import task_scrape_x
from task_manager.tasks.analyze_sentiment import task_analyze_sentiment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("socialscope")


# ── Commands ──────────────────────────────────────────────────────────

def cmd_login():
    print(
        "\n=== X/Twitter Cookie Login ==="
        "\n"
        "\n1. Open https://x.com in your normal browser and make sure you're logged in"
        "\n2. Open DevTools: press F12 (or right-click → Inspect)"
        "\n3. Go to: Application tab → Cookies → https://x.com"
        "\n4. Find and copy the values of these two cookies:"
        "\n   - auth_token"
        "\n   - ct0"
        "\n"
    )
    auth_token = input("Paste auth_token value: ").strip()
    ct0 = input("Paste ct0 value: ").strip()

    if not auth_token or not ct0:
        print("Error: both cookies are required.")
        return

    XScraper.login_from_cookies(auth_token, ct0)
    print("\nSession saved to auth/x_state.json — you can now run: python main.py scrape")


def cmd_add_target(username: str):
    with get_db() as db:
        db.init_schema()
        target = db.add_target(username)
        print(f"Target added: @{target['username']} (id={target['id']})")


async def cmd_scrape():
    with get_db() as db:
        db.init_schema()
        result = await task_scrape_x(db)
        logger.info("Scrape result: %s", result)
        return result.get("tweets_upserted", 0)


def cmd_analyze():
    with get_db() as db:
        db.init_schema()
        result = task_analyze_sentiment(db)
        logger.info("Analyze result: %s", result)

        summary = db.get_sentiment_summary()
        logger.info("Sentiment distribution: %s", json.dumps(summary, indent=2, default=str))


async def cmd_run():
    """Full pipeline: scrape all targets → analyze."""
    count = await cmd_scrape()
    if count:
        cmd_analyze()


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SocialScope — Social media intelligence agent for X/Twitter",
    )
    parser.add_argument(
        "command",
        choices=["login", "add-target", "scrape", "analyze", "run"],
        help="Action to perform",
    )
    parser.add_argument("args", nargs="*", help="Additional arguments")
    args = parser.parse_args()

    if args.command == "login":
        cmd_login()
    elif args.command == "add-target":
        if not args.args:
            print("Usage: python main.py add-target <username>")
            return
        cmd_add_target(args.args[0])
    elif args.command == "scrape":
        asyncio.run(cmd_scrape())
    elif args.command == "analyze":
        cmd_analyze()
    elif args.command == "run":
        asyncio.run(cmd_run())


if __name__ == "__main__":
    main()
