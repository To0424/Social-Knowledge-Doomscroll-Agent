"""
SocialScope FastAPI application factory.

Provides REST endpoints for target management, tweet browsing, analysis,
schedule management, task triggers, and X credential management.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import all_routers
from config import get_db

logger = logging.getLogger("socialscope.api")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_db() as db:
        db.init_schema()
    logger.info("SocialScope API started — schema initialized")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="SocialScope API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in all_routers:
        app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
