"""
Handwritten Multilingual Invoice OCR System
FastAPI Backend - Main Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.v1.endpoints import invoices, auth, health
from database.connection import engine, Base
from core.config import settings
from core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Handwritten Invoice OCR System...")
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized.")
    yield
    logger.info("Shutting down Invoice OCR System...")
    await engine.dispose()


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Handwritten Invoice OCR API",
    description="""
## Enterprise Handwritten Multilingual Invoice OCR System

Extract structured data from handwritten invoices in multiple languages:
- 🇮🇳 Hindi, Marathi, Gujarati, Tamil, Telugu
- 🇬🇧 English

### Features
- **AI-Powered OCR** using PaddleOCR (free, open-source)
- **Image Preprocessing** with OpenCV
- **Structured JSON** output
- **Confidence Scoring**
- **Auto-validation** of totals
- **PostgreSQL** storage
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(invoices.router, prefix="/api/v1", tags=["Invoices"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Handwritten Invoice OCR System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }