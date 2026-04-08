"""Schedule management routes."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from api.schemas import ScheduleUpdate
from config import get_db
from task_manager.tasks import TASK_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("")
def list_schedules():
    with get_db() as db:
        return db.get_schedules()


@router.patch("/{schedule_id}")
def update_schedule(schedule_id: int, body: ScheduleUpdate):
    with get_db() as db:
        db.update_schedule(
            schedule_id,
            interval_seconds=body.interval_seconds,
            is_active=body.is_active,
        )
        return {"status": "ok"}


@router.post("/{schedule_id}/run")
async def run_schedule_now(schedule_id: int):
    """Immediately execute a scheduled task (fire-and-forget)."""
    with get_db() as db:
        schedules = db.get_schedules()
        sched = next((s for s in schedules if s["id"] == schedule_id), None)
        if not sched:
            raise HTTPException(status_code=404, detail="Schedule not found")

        task_name = sched["task_name"]
        if task_name not in TASK_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Unknown task: {task_name}")

    async def _run():
        try:
            fn = TASK_REGISTRY[task_name]
            with get_db() as db:
                if asyncio.iscoroutinefunction(fn):
                    await fn(db)
                else:
                    await asyncio.to_thread(fn, db)
                db.mark_schedule_ran(schedule_id)
            logger.info("Background task %s completed", task_name)
        except Exception:
            logger.error("Background task %s failed", task_name, exc_info=True)

    asyncio.create_task(_run())
    return {"status": "ok", "task": task_name, "message": "Task started"}
