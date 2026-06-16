"""Invoice Database Repository"""
import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload

from models.invoice import InvoiceMaster, InvoiceItem
from schemas.invoice import InvoiceCreate, OCRResult

logger = logging.getLogger(__name__)


class InvoiceRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        ocr_result: OCRResult,
        image_path: Optional[str] = None,
    ) -> InvoiceMaster:
        """Save full invoice to DB."""
        invoice = InvoiceMaster(
            invoice_number=ocr_result.invoice_no,
            grand_total=ocr_result.grand_total,
            invoice_image=image_path,
            confidence_score=ocr_result.confidence_score,
            language_detected=ocr_result.language_detected,
            raw_text=ocr_result.raw_text,
            warnings="; ".join(ocr_result.warnings) if ocr_result.warnings else None,
        )
        self.db.add(invoice)
        await self.db.flush()  # get ID

        for product in ocr_result.products:
            item = InvoiceItem(
                invoice_id=invoice.id,
                product_name=product.name,
                quantity=product.qty,
                unit_price=product.price,
                total_amount=product.total,
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(invoice)
        logger.info("Saved invoice id=%d, items=%d", invoice.id, len(ocr_result.products))
        return invoice

    async def get_by_id(self, invoice_id: int) -> Optional[InvoiceMaster]:
        stmt = (
            select(InvoiceMaster)
            .options(selectinload(InvoiceMaster.items))
            .where(InvoiceMaster.id == invoice_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_invoices(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> Tuple[List[InvoiceMaster], int]:
        stmt = select(InvoiceMaster).options(selectinload(InvoiceMaster.items))

        if search:
            stmt = stmt.where(
                or_(
                    InvoiceMaster.invoice_number.ilike(f"%{search}%"),
                    InvoiceMaster.language_detected.ilike(f"%{search}%"),
                )
            )

        # Sort
        col = getattr(InvoiceMaster, sort_by, InvoiceMaster.created_at)
        stmt = stmt.order_by(desc(col) if sort_dir == "desc" else col)

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginate
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        invoices = result.scalars().all()

        return list(invoices), total

    async def delete(self, invoice_id: int) -> bool:
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            return False
        await self.db.delete(invoice)
        await self.db.commit()
        return True