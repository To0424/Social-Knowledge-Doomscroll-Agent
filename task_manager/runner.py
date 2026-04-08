"""
TaskManager — polls the schedules table and dispatches registered tasks.

Usage (standalone):
    python -m task_manager.runner

Or via Docker:
    command: ["python", "-m", "task_manager.runner"]
"""

import asyncio
import logging
import os
import time

from config import get_db as _get_db_ctx
from task_manager.tasks import TASK_REGISTRY

logger = logging.getLogger("socialscope.task_manager")

POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "15"))


def _get_db():
    """Return a connected Database instance (not as context manager)."""
    db = _get_db_ctx()
    db.connect()
    db.init_schema()
    return db


class TaskManager:
    """Central orchestrator that polls the schedules table and runs due tasks."""

    def __init__(self, poll_interval: int = POLL_INTERVAL):
        self.poll_interval = poll_interval
        self._loop = asyncio.new_event_loop()
        self._db = None

    def start(self):
        """Run the polling loop (blocking). Call this from __main__."""
        logger.info("Task Manager started (poll=%ds, tasks=%s)",
                     self.poll_interval, list(TASK_REGISTRY.keys()))

        asyncio.set_event_loop(self._loop)
        self._db = _get_db()

        while True:
            try:
                self._poll()
            except Exception:
                logger.error("Poll cycle error — reconnecting in %ds",
                             self.poll_interval, exc_info=True)
                self._reconnect()
            time.sleep(self.poll_interval)

    def run_task(self, task_name: str, db=None):
        """Execute a single task by name (used by the API for on-demand runs)."""
        target_db = db or self._db
        self._loop.run_until_complete(self._dispatch(task_name, target_db))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _poll(self):
        due = self._db.get_due_schedules()
        for sched in due:
            task_name = sched["task_name"]
            logger.info("Running scheduled task: %s", task_name)
            try:
                self._loop.run_until_complete(self._dispatch(task_name, self._db))
                self._db.mark_schedule_ran(sched["id"])
                logger.info("Task %s completed, next run at +%ds",
                            task_name, sched["interval_seconds"])
            except Exception:
                logger.error("Task %s failed", task_name, exc_info=True)
                self._db.mark_schedule_ran(sched["id"])

        if not due:
            logger.debug("No due tasks — sleeping %ds", self.poll_interval)

    @staticmethod
    async def _dispatch(task_name: str, db):
        fn = TASK_REGISTRY.get(task_name)
        if fn is None:
            logger.warning("Unknown task: %s", task_name)
            return
        if asyncio.iscoroutinefunction(fn):
            await fn(db)
        else:
            fn(db)

    def _reconnect(self):
        try:
            self._db.close()
        except Exception:
            pass
        try:
            self._db = _get_db()
        except Exception:
            logger.error("Reconnect failed", exc_info=True)


# ── Entrypoint ────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    TaskManager().start()


if __name__ == "__main__":
    main()
