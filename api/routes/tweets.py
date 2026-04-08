"""Tweet browsing routes."""

from fastapi import APIRouter, Query

from config import get_db

router = APIRouter(prefix="/api/tweets", tags=["tweets"])


@router.get("")
def list_tweets(
    target_id: int | None = Query(None),
    sentiment: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    with get_db() as db:
        tweets = db.get_tweets(
            target_id=target_id, sentiment=sentiment,
            category=category, limit=limit, offset=offset,
        )
        total = db.get_tweet_count(target_id=target_id, sentiment=sentiment, category=category)
        return {"tweets": tweets, "total": total}
