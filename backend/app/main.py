from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

from app.db.init_db import init_db
from app.db.session import SessionLocal


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Coursewright API starting up...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield
    logger.info("Coursewright API shutting down...")

app = FastAPI(
    title="Coursewright API",
    description="AI-powered specialization discovery platform for QUEST Nawabshah students",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "ALLOWED_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "coursewright-api"}