

"""
Main OCR Service
Orchestrates: Image Preprocessing -> OCR -> Parsing -> Validation
"""
import logging
from typing import Optional

from preprocessing.image_processor import ImagePreprocessor
from ocr.ocr_engine import get_ocr_engine, normalize_language_code
from ocr.parser import InvoiceParser
from validators.invoice_validator import InvoiceValidator
from schemas.invoice import OCRResult, OCRResultItem
from core.config import settings

logger = logging.getLogger(__name__)

# Languages that use complex scripts — binarization degrades recognition quality.
# For these, the pipeline stops after contrast enhancement (no binarize step).
COMPLEX_SCRIPT_LANGS = {"hi", "mr", "gu", "ta", "te"}

# Unicode range checks used to detect Indic scripts in OCR output
_INDIC_RANGES = [
    ("\u0900", "\u097F", "hi"),   # Devanagari -> Hindi/Marathi
    ("\u0A80", "\u0AFF", "gu"),   # Gujarati
    ("\u0B80", "\u0BFF", "ta"),   # Tamil
    ("\u0C00", "\u0C7F", "te"),   # Telugu
]


def _detect_script(text: str) -> str:
    """Detect dominant script in a string. Returns normalized lang code."""
    counts = {}
    for start, end, lang in _INDIC_RANGES:
        counts[lang] = sum(1 for c in text if start <= c <= end)
    counts["en"] = sum(1 for c in text if c.isascii() and c.isalpha())
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else "en"


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
        """Full pipeline: bytes -> structured OCRResult."""
        norm_lang = normalize_language_code(language)
        use_complex_pipeline = norm_lang in COMPLEX_SCRIPT_LANGS

        # 1. Preprocessing
        logger.info(
            "Starting image preprocessing (language=%s, complex_script=%s)...",
            norm_lang, use_complex_pipeline,
        )
        try:
            if use_complex_pipeline:
                processed_image, preprocess_meta = self.preprocessor.process_for_indic(image_bytes)
            else:
                processed_image, preprocess_meta = self.preprocessor.process(image_bytes)
        except ValueError as e:
            logger.error("Preprocessing failed: %s", e)
            return OCRResult(
                warnings=[f"Image preprocessing failed: {str(e)}"],
                confidence_score=0.0,
            )

        # 2. OCR
        engine = _get_engine_for_language(norm_lang)
        logger.info("Running OCR with engine: %s, language: %s", engine.name, norm_lang)
        try:
            text_lines, ocr_confidence = engine.extract_text(
                processed_image, language=norm_lang
            )
        except Exception as e:
            logger.error("OCR failed: %s", e)
            return OCRResult(
                warnings=[f"OCR engine error: {str(e)}"],
                confidence_score=0.0,
            )

        # 2b. Auto-detect fallback.
        # "auto" uses an English-only EasyOCR reader (the only safe multi-script choice).
        # If the result is empty or the extracted text contains Indic characters,
        # re-detect the dominant script and re-run with the correct language reader.
        if norm_lang == "auto":
            raw_joined = " ".join(text_lines)
            detected_lang = _detect_script(raw_joined)
            if detected_lang != "en" or not text_lines:
                logger.info(
                    "Auto-detect: script='%s', re-running OCR with correct language reader.",
                    detected_lang,
                )
                # Switch to Indic-safe preprocessing when the script requires it
                if detected_lang in COMPLEX_SCRIPT_LANGS and not use_complex_pipeline:
                    try:
                        processed_image, _ = self.preprocessor.process_for_indic(image_bytes)
                    except ValueError:
                        pass  # keep the already-preprocessed image

                engine2 = _get_engine_for_language(detected_lang)
                try:
                    text_lines2, ocr_confidence2 = engine2.extract_text(
                        processed_image, language=detected_lang
                    )
                    if text_lines2:
                        text_lines = text_lines2
                        ocr_confidence = ocr_confidence2
                        logger.info(
                            "Re-run OCR extracted %d lines, confidence=%.3f",
                            len(text_lines), ocr_confidence,
                        )
                except Exception as e2:
                    logger.warning("Re-run OCR failed: %s. Keeping initial results.", e2)

        if not text_lines:
            return OCRResult(
                warnings=["OCR returned no text. Image may be blank or unreadable."],
                confidence_score=ocr_confidence,
            )

        logger.info("OCR extracted %d lines, confidence=%.3f", len(text_lines), ocr_confidence)
        for idx, ln in enumerate(text_lines):
            logger.debug("  OCR line [%02d]: %s", idx, ln)

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


def _get_engine_for_language(norm_lang: str):
    """
    Returns an OCR engine for the given normalized language code.
    For EasyOCR and PaddleOCR: creates a fresh adapter instance per call
    (adapters cache their underlying readers/engines by language key internally,
    so only the first call per language pays the model-load cost).
    Cloud providers use the global singleton since they are language-agnostic.
    """
    from ocr.ocr_engine import EasyOCRAdapter, PaddleOCRAdapter

    provider = settings.OCR_PROVIDER.lower()

    if provider == "easyocr":
        return EasyOCRAdapter(use_gpu=settings.PADDLE_USE_GPU)

    if provider == "paddleocr":
        return PaddleOCRAdapter(use_gpu=settings.PADDLE_USE_GPU)

    return get_ocr_engine()


_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service