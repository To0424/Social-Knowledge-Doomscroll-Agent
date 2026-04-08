"""X credential management routes."""

from fastapi import APIRouter

from api.schemas import CredentialsUpdate
from config import get_db
from task_manager.scraper.x_client import XScraper

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


@router.get("")
def get_credentials():
    """Return whether X cookies are configured (never exposes actual values)."""
    with get_db() as db:
        auth_token = db.get_setting("x_auth_token")
        ct0 = db.get_setting("x_ct0")
        return {
            "has_auth_token": auth_token is not None,
            "has_ct0": ct0 is not None,
            "configured": auth_token is not None and ct0 is not None,
        }


@router.put("")
def save_credentials(body: CredentialsUpdate):
    """Save X cookies to the database and write the Playwright session file."""
    with get_db() as db:
        db.set_setting("x_auth_token", body.auth_token)
        db.set_setting("x_ct0", body.ct0)
    XScraper.login_from_cookies(body.auth_token, body.ct0)
    return {"status": "ok", "message": "Credentials saved"}


@router.delete("")
def delete_credentials():
    """Remove stored X cookies."""
    with get_db() as db:
        db.delete_setting("x_auth_token")
        db.delete_setting("x_ct0")
    return {"status": "ok", "message": "Credentials removed"}
