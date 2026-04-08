"""Analysis route — summarise / consolidate tweets for a target + date range."""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import get_db, get_llm_client
from llm.analysis import summarise_tweets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    target_id: int
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD


class AnalysisResponse(BaseModel):
    id: int
    summary: str
    tweet_count: int
    username: str
    start_date: str
    end_date: str
    created_at: str


class AnalysisListItem(BaseModel):
    id: int
    target_id: int
    username: str
    start_date: str
    end_date: str
    tweet_count: int
    created_at: str


@router.post("", response_model=AnalysisResponse)
def run_analysis(body: AnalysisRequest):
    """Fetch tweets for a target within a date range and summarise them via Ollama."""
    with get_db() as db:
        targets = db.get_targets(active_only=False)
        target = next((t for t in targets if t["id"] == body.target_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        tweets = db.get_tweets_by_date_range(
            target_id=body.target_id,
            start_date=body.start_date,
            end_date=body.end_date,
        )

        username = target["username"]

        if not tweets:
            summary_text = f"No tweets found for @{username} between {body.start_date} and {body.end_date}."
            tweet_count = 0
        else:
            client = get_llm_client()
            summary_text = summarise_tweets(client, tweets, username)
            tweet_count = len(tweets)

        saved = db.save_analysis(
            target_id=body.target_id,
            username=username,
            start_date=body.start_date,
            end_date=body.end_date,
            tweet_count=tweet_count,
            summary=summary_text,
        )

    return AnalysisResponse(
        id=saved["id"],
        summary=saved["summary"],
        tweet_count=saved["tweet_count"],
        username=saved["username"],
        start_date=str(saved["start_date"]),
        end_date=str(saved["end_date"]),
        created_at=str(saved["created_at"]),
    )


@router.get("", response_model=list[AnalysisListItem])
def list_analyses(target_id: int | None = Query(None)):
    """List past analysis records, optionally filtered by target."""
    with get_db() as db:
        rows = db.get_analyses(target_id=target_id)
    return [
        AnalysisListItem(
            id=r["id"],
            target_id=r["target_id"],
            username=r["username"],
            start_date=str(r["start_date"]),
            end_date=str(r["end_date"]),
            tweet_count=r["tweet_count"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: int):
    """Get a single past analysis by ID."""
    with get_db() as db:
        row = db.get_analysis(analysis_id)
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse(
        id=row["id"],
        summary=row["summary"],
        tweet_count=row["tweet_count"],
        username=row["username"],
        start_date=str(row["start_date"]),
        end_date=str(row["end_date"]),
        created_at=str(row["created_at"]),
    )


@router.delete("/{analysis_id}")
def delete_analysis(analysis_id: int):
    """Delete a past analysis record."""
    with get_db() as db:
        row = db.get_analysis(analysis_id)
        if not row:
            raise HTTPException(status_code=404, detail="Analysis not found")
        db.delete_analysis(analysis_id)
    return {"status": "deleted"}
