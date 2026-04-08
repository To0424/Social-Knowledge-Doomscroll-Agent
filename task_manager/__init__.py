"""
task_manager — Central orchestrator for SocialScope.

Polls the `schedules` table at a configurable interval and dispatches
registered tasks (scrape_x, analyze_sentiment).
"""

from task_manager.runner import TaskManager

__all__ = ["TaskManager"]
