"""Target management routes."""

from fastapi import APIRouter

from api.schemas import TargetCreate
from config import get_db

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("")
def list_targets():
    with get_db() as db:
        return db.get_targets(active_only=False)


@router.post("")
def create_target(body: TargetCreate):
    with get_db() as db:
        return db.add_target(body.username, body.display_name)


@router.delete("/{target_id}")
def delete_target(target_id: int):
    with get_db() as db:
        db.remove_target(target_id)
        return {"status": "ok"}
