"""Task: analyze_sentiment — Score and categorize unanalyzed tweets via LLM."""

import logging

from config import get_llm_client
from llm.sentiment import analyze_sentiment

logger = logging.getLogger(__name__)


def task_analyze_sentiment(db) -> dict:
    """Run sentiment analysis on up to 50 unanalyzed tweets."""
    client = get_llm_client()
    unanalyzed = db.get_unanalyzed_tweets(limit=50)
    if not unanalyzed:
        logger.info("Nothing to analyze")
        return {"analyzed": 0}

    logger.info("Processing %d tweets …", len(unanalyzed))
    results = analyze_sentiment(client, unanalyzed)
    for r in results:
        db.update_sentiment(
            tweet_id=r["tweet_id"],
            score=r["sentiment_score"],
            label=r["sentiment_label"],
            category=r["category"],
        )
    logger.info("Done: %d tweets", len(results))
    return {"analyzed": len(results)}
