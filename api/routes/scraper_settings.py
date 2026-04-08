"""Scraper settings route — configurable scraping parameters."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config import get_db

router = APIRouter(prefix="/api/scraper-settings", tags=["scraper-settings"])

DEFAULT_MAX_SCROLLS = 10


class ScraperSettings(BaseModel):
    max_scrolls: int = Field(ge=1, le=100)


@router.get("", response_model=ScraperSettings)
def get_scraper_settings():
    with get_db() as db:
        val = db.get_setting("max_scrolls")
    return ScraperSettings(max_scrolls=int(val) if val else DEFAULT_MAX_SCROLLS)


@router.put("")
def update_scraper_settings(body: ScraperSettings):
    with get_db() as db:
        db.set_setting("max_scrolls", str(body.max_scrolls))
    return {"status": "saved"}
