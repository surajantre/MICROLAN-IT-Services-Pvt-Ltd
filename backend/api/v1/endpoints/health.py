"""Health Check Endpoint"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from database.connection import get_db
from schemas.invoice import HealthResponse
from core.config import settings
from ocr.ocr_engine import get_ocr_engine

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System health check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check system health: database connectivity and OCR engine status."""
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # OCR engine name
    try:
        engine_name = get_ocr_engine().name
    except Exception:
        engine_name = "not initialized"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        ocr_engine=engine_name,
    )