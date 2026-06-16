"""Pydantic Schemas for Request/Response Validation"""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator
import math


class InvoiceItemCreate(BaseModel):
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None


class InvoiceItemResponse(BaseModel):
    id: int
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    invoice_number: Optional[str] = None
    grand_total: Optional[float] = None
    confidence_score: Optional[float] = None
    language_detected: Optional[str] = None
    raw_text: Optional[str] = None
    warnings: Optional[str] = None
    items: List[InvoiceItemCreate] = []


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: Optional[str] = None
    grand_total: Optional[float] = None
    invoice_image: Optional[str] = None
    confidence_score: Optional[float] = None
    language_detected: Optional[str] = None
    warnings: Optional[str] = None
    created_at: datetime
    items: List[InvoiceItemResponse] = []

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InvoiceResponse]


class OCRResultItem(BaseModel):
    name: str
    qty: float
    price: float
    total: float


class OCRResult(BaseModel):
    invoice_no: Optional[str] = None
    products: List[OCRResultItem] = []
    grand_total: Optional[float] = None
    confidence_score: float = 0.0
    language_detected: Optional[str] = None
    warnings: List[str] = []
    raw_text: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    invoice_id: int
    confidence: float
    data: OCRResult
    message: str = "Invoice processed successfully"


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    ocr_engine: str