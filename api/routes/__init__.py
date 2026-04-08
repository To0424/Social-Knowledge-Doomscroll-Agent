"""Route package — collects all APIRouters."""

from api.routes.targets import router as targets_router
from api.routes.tweets import router as tweets_router
from api.routes.analysis import router as analysis_router
from api.routes.schedules import router as schedules_router
from api.routes.credentials import router as credentials_router
from api.routes.pipeline import router as pipeline_router
from api.routes.scraper_settings import router as scraper_settings_router

all_routers = [
    targets_router,
    tweets_router,
    analysis_router,
    schedules_router,
    credentials_router,
    pipeline_router,
    scraper_settings_router,
]
