"""
Invoice Validation Engine
Auto-corrects totals, validates quantities/prices, calculates confidence.
"""
import logging
from typing import List, Tuple
# from services.parser import ParsedInvoice, ParsedItem
from ocr.parser import ParsedInvoice, ParsedItem

logger = logging.getLogger(__name__)


class InvoiceValidator:
    """Validates and auto-corrects parsed invoice data."""

    TOLERANCE = 0.02  # 2% tolerance for floating point

    def validate(
        self,
        invoice: ParsedInvoice,
        ocr_confidence: float,
        parsing_confidence: float,
    ) -> Tuple[ParsedInvoice, float, List[str]]:
        """
        Validate invoice data.
        Returns (corrected_invoice, final_confidence, warnings).
        """
        warnings = list(invoice.warnings)
        validation_score = 1.0

        # 1. Validate and fix each item
        valid_items = []
        for item in invoice.items:
            item, item_warnings, item_ok = self._validate_item(item)
            warnings.extend(item_warnings)
            if item_ok:
                valid_items.append(item)
            else:
                validation_score -= 0.1
        invoice.items = valid_items

        # 2. Validate grand total
        if invoice.items:
            computed_total = round(sum(i.total for i in invoice.items), 2)
            if invoice.grand_total is None:
                invoice.grand_total = computed_total
                warnings.append("Grand total not detected; computed from items.")
            elif abs(invoice.grand_total - computed_total) > self.TOLERANCE * max(computed_total, 1):
                warnings.append(
                    f"Grand total mismatch: stated={invoice.grand_total}, "
                    f"computed={computed_total}. Using computed."
                )
                invoice.grand_total = computed_total
                validation_score -= 0.05

        # 3. No items warning
        if not invoice.items:
            validation_score = 0.0
            warnings.append("No valid line items found after validation.")

        # Clamp validation score
        validation_score = max(0.0, min(1.0, validation_score))

        # 4. Final confidence formula
        final_score = (
            ocr_confidence * 0.5
            + parsing_confidence * 0.3
            + validation_score * 0.2
        )
        final_score = round(max(0.0, min(1.0, final_score)), 4)
        invoice.warnings = warnings

        logger.info(
            "Validation complete: items=%d, grand_total=%s, score=%.4f",
            len(invoice.items), invoice.grand_total, final_score
        )
        return invoice, final_score, warnings

    def _validate_item(
        self, item: ParsedItem
    ) -> Tuple[ParsedItem, List[str], bool]:
        """Validate a single item. Returns (item, warnings, is_valid)."""
        warnings = []

        # Quantity check
        if item.qty is None or item.qty <= 0:
            warnings.append(f"Invalid quantity for '{item.name}': {item.qty}. Skipping item.")
            return item, warnings, False

        # Price check
        if item.price is None or item.price < 0:
            warnings.append(f"Invalid price for '{item.name}': {item.price}. Skipping item.")
            return item, warnings, False

        # Total check: qty × price == total
        expected = round(item.qty * item.price, 2)
        if abs(expected - item.total) > self.TOLERANCE * max(item.total, 1):
            warnings.append(
                f"Total mismatch for '{item.name}': "
                f"{item.qty}×{item.price}={expected} ≠ {item.total}. Auto-corrected."
            )
            item.total = expected

        return item, warnings, True