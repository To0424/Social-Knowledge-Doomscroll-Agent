"""Pipeline trigger routes — on-demand scrape / analyze / full run."""

import asyncio
import logging

from fastapi import APIRouter, Query

from config import get_db
from task_manager.tasks.scrape_x import task_scrape_x
from task_manager.tasks.analyze_sentiment import task_analyze_sentiment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.post("/scrape")
async def trigger_scrape():
    """Scrape all active targets."""
    with get_db() as db:
        result = await task_scrape_x(db)
    return {"status": "ok", **result}


@router.post("/analyze")
def trigger_analyze():
    """Run sentiment analysis on all unanalyzed tweets."""
    with get_db() as db:
        result = task_analyze_sentiment(db)
    return {"status": "ok", **result}


@router.post("/run")
async def trigger_run():
    """Full pipeline: scrape all targets → analyze."""
    scrape_result = await trigger_scrape()
    analyze_result = await asyncio.to_thread(trigger_analyze)
    return {
        "scrape": scrape_result,
        "analyze": analyze_result,
    }


@router.get("/stats")
def get_stats(target_id: int | None = Query(None)):
    with get_db() as db:
        return {
            "sentiment": db.get_sentiment_summary(target_id=target_id),
            "categories": db.get_category_summary(target_id=target_id),
            "tweet_count": db.get_tweet_count(target_id=target_id),
        }
