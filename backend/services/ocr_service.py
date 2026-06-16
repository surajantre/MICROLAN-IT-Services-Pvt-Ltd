"""
Main OCR Service
Orchestrates: Image Preprocessing → OCR → Parsing → Validation
"""
import logging
from typing import Optional

from preprocessing.image_processor import ImagePreprocessor
from ocr.ocr_engine import get_ocr_engine
# from services.parser import InvoiceParser
from ocr.parser import InvoiceParser
from validators.invoice_validator import InvoiceValidator
from schemas.invoice import OCRResult, OCRResultItem

logger = logging.getLogger(__name__)


class OCRService:
    """Full invoice OCR pipeline."""

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.parser = InvoiceParser()
        self.validator = InvoiceValidator()

    async def process_invoice(
        self,
        image_bytes: bytes,
        language: str = "auto",
    ) -> OCRResult:
        """
        Full pipeline: bytes → structured OCRResult.
        """
        # 1. Preprocessing
        logger.info("Starting image preprocessing...")
        try:
            processed_image, preprocess_meta = self.preprocessor.process(image_bytes)
        except ValueError as e:
            logger.error("Preprocessing failed: %s", e)
            return OCRResult(
                warnings=[f"Image preprocessing failed: {str(e)}"],
                confidence_score=0.0,
            )

        # 2. OCR
        logger.info("Running OCR with engine: %s", get_ocr_engine().name)
        try:
            text_lines, ocr_confidence = get_ocr_engine().extract_text(
                processed_image, language=language
            )
        except Exception as e:
            logger.error("OCR failed: %s", e)
            return OCRResult(
                warnings=[f"OCR engine error: {str(e)}"],
                confidence_score=0.0,
            )

        if not text_lines:
            return OCRResult(
                warnings=["OCR returned no text. Image may be blank or unreadable."],
                confidence_score=ocr_confidence,
            )

        logger.info("OCR extracted %d lines, confidence=%.3f", len(text_lines), ocr_confidence)

        # 3. Parse
        parsed = self.parser.parse(text_lines, ocr_confidence)
        parsing_confidence = parsed.parsing_confidence

        # 4. Validate
        validated, final_score, warnings = self.validator.validate(
            parsed, ocr_confidence, parsing_confidence
        )

        # 5. Build response
        items = [
            OCRResultItem(
                name=item.name,
                qty=item.qty,
                price=item.price,
                total=item.total,
            )
            for item in validated.items
        ]

        # Preprocess warnings
        all_warnings = list(preprocess_meta.get("warnings", []))
        all_warnings.extend(warnings)

        return OCRResult(
            invoice_no=validated.invoice_no,
            products=items,
            grand_total=validated.grand_total,
            confidence_score=final_score,
            language_detected=validated.language,
            warnings=all_warnings,
            raw_text=validated.raw_text,
        )


# Singleton
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service