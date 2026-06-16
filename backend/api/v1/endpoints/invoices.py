"""Invoice API Endpoints"""
import os
import uuid
import logging
from typing import Optional
from fastapi import (
    APIRouter, Depends, File, Form, HTTPException,
    UploadFile, Query, status
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from services.ocr_service import get_ocr_service
from repositories.invoice_repository import InvoiceRepository
from schemas.invoice import (
    UploadResponse, InvoiceResponse, InvoiceListResponse, ErrorResponse
)
from core.config import settings
from core.security import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "image/tiff", "image/bmp", "application/pdf",
}


@router.post(
    "/invoice/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a handwritten invoice",
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def upload_invoice(
    invoice_image: UploadFile = File(..., description="Invoice image (JPG/PNG/TIFF/BMP)"),
    language: str = Form(
        default="auto",
        description="Language hint: en, hi, mr, gu, ta, te, auto",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a handwritten invoice image and extract structured data.

    Supported languages: English, Hindi, Marathi, Gujarati, Tamil, Telugu.

    Returns structured JSON with product names, quantities, prices and totals.
    """
    # Validate content type
    if invoice_image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {invoice_image.content_type}. "
                   f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Validate file size
    image_bytes = await invoice_image.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(image_bytes)//1024}KB. Max: {settings.MAX_FILE_SIZE_MB}MB",
        )

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save image
    filename = f"{uuid.uuid4()}{os.path.splitext(invoice_image.filename or '.jpg')[1]}"
    image_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # Process via OCR pipeline
    try:
        ocr_service = get_ocr_service()
        ocr_result = await ocr_service.process_invoice(image_bytes, language=language)
    except Exception as e:
        logger.exception("OCR processing error")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    # Save to DB
    try:
        repo = InvoiceRepository(db)
        invoice = await repo.create(ocr_result, image_path=image_path)
    except Exception as e:
        logger.exception("Database save error")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return UploadResponse(
        success=True,
        invoice_id=invoice.id,
        confidence=ocr_result.confidence_score,
        data=ocr_result,
    )


@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    summary="List all invoices with pagination and search",
)
async def list_invoices(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by invoice number"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    sort_dir: str = Query(
    default="desc",
    pattern="^(asc|desc)$",
    description="Sort direction",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve paginated list of processed invoices."""
    repo = InvoiceRepository(db)
    invoices, total = await repo.list_invoices(
        page=page, page_size=page_size,
        search=search, sort_by=sort_by, sort_dir=sort_dir
    )
    return InvoiceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[InvoiceResponse.model_validate(inv) for inv in invoices],
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice details by ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve a single invoice with all line items."""
    repo = InvoiceRepository(db)
    invoice = await repo.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found.")
    return InvoiceResponse.model_validate(invoice)


@router.delete(
    "/invoices/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an invoice",
)
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    repo = InvoiceRepository(db)
    deleted = await repo.delete(invoice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found.")