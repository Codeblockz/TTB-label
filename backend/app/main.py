import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.init_db import create_all_tables
from app.db.session import engine
from app.routers import analysis, batch, health, samples

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models so metadata is populated
    from app.models import analysis, batch, label  # noqa: F401

    logger.info("Creating database tables...")
    await create_all_tables(engine)
    logger.info("Database ready")
    yield


app = FastAPI(
    title="LabelCheck API",
    description="AI-powered alcohol label verification for TTB compliance",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(batch.router)
app.include_router(samples.router)
