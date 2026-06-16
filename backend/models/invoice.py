"""Database Models"""
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Numeric, DateTime, ForeignKey,
    Text, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base


class InvoiceMaster(Base):
    __tablename__ = "invoice_master"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    grand_total: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    invoice_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    language_detected: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_invoice_number", "invoice_number"),
        Index("idx_created_at", "created_at"),
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("invoice_master.id", ondelete="CASCADE")
    )
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    invoice: Mapped["InvoiceMaster"] = relationship("InvoiceMaster", back_populates="items")

    __table_args__ = (Index("idx_invoice_id", "invoice_id"),)