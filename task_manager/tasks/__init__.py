"""Task registry — maps task_name strings to callable implementations."""

from task_manager.tasks.scrape_x import task_scrape_x
from task_manager.tasks.analyze_sentiment import task_analyze_sentiment

TASK_REGISTRY: dict[str, callable] = {
    "scrape_x": task_scrape_x,
    "analyze_sentiment": task_analyze_sentiment,
}
