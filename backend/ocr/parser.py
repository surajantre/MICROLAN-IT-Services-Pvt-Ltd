"""
AI Parsing Layer
Converts raw OCR text lines → structured invoice JSON
Uses: Regex → NLP heuristics → Rule Engine → LLM Validation
"""
import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Common number words to fix OCR misreads
OCR_NUMBER_FIXES = {
    "O": "0", "o": "0", "l": "1", "I": "1",
    "S": "5", "Z": "2", "B": "8", "G": "6",
}

# Invoice header keywords (multilingual)
INVOICE_KEYWORDS = {
    "invoice": ["invoice", "bill", "receipt", "बिल", "रसीद", "चलान",
                "बीजक", "ਬਿੱਲ", "బిల్లు", "பில்", "ഇൻവോയ്സ്"],
    "total":   ["total", "grand total", "amount", "कुल", "जमा", "कुल राशि",
                "மொத்தம்", "మొత్తం", " కుల", "योग"],
    "qty":     ["qty", "quantity", "pcs", "nos", "मात्रा", "नग", "संख्या"],
    "price":   ["price", "rate", "unit price", "मूल्य", "दर", "कीमत", "भाव"],
}

# Regex patterns
RE_INVOICE_NO = re.compile(
    r"(?:invoice|bill|inv|receipt)[.\s#:-]*([A-Z0-9\-/]+)",
    re.IGNORECASE
)
RE_NUMBER = re.compile(r"[\d,]+(?:\.\d+)?")
RE_LINE_ITEMS = re.compile(
    r"(.+?)\s+([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)\s*([\d,]+(?:\.\d+))?",
)


@dataclass
class ParsedItem:
    name: str
    qty: float
    price: float
    total: float
    confidence: float = 1.0


@dataclass
class ParsedInvoice:
    invoice_no: Optional[str] = None
    items: List[ParsedItem] = field(default_factory=list)
    grand_total: Optional[float] = None
    language: Optional[str] = None
    parsing_confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)
    raw_text: str = ""


class InvoiceParser:
    """Multi-strategy invoice parser with fallback chain."""

    def parse(self, text_lines: List[str], ocr_confidence: float = 0.9) -> ParsedInvoice:
        """Parse OCR text lines into structured invoice data."""
        raw_text = "\n".join(text_lines)
        result = ParsedInvoice(raw_text=raw_text)

        # 1. Language detection
        result.language = self._detect_language(raw_text)

        # 2. Extract invoice number
        result.invoice_no = self._extract_invoice_number(text_lines)

        # 3. Extract line items
        items, parsing_conf = self._extract_items(text_lines)
        result.items = items
        result.parsing_confidence = parsing_conf

        # 4. Extract grand total
        result.grand_total = self._extract_grand_total(text_lines, items)

        # 5. Warnings
        if not items:
            result.warnings.append("No line items detected. OCR may have failed.")
        if not result.invoice_no:
            result.warnings.append("Invoice number not found.")

        logger.info(
            "Parsed %d items, lang=%s, inv=%s",
            len(items), result.language, result.invoice_no
        )
        return result

    # ------------------------------------------------------------------ #
    # Language Detection
    # ------------------------------------------------------------------ #
    def _detect_language(self, text: str) -> str:
        """Detect script/language from Unicode ranges."""
        devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        gujarati   = sum(1 for c in text if "\u0A80" <= c <= "\u0AFF")
        tamil      = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
        telugu     = sum(1 for c in text if "\u0C00" <= c <= "\u0C7F")
        latin      = sum(1 for c in text if c.isascii() and c.isalpha())

        scores = {
            "hi/mr": devanagari,
            "gu": gujarati,
            "ta": tamil,
            "te": telugu,
            "en": latin,
        }
        detected = max(scores, key=scores.get)
        return detected if scores[detected] > 0 else "en"

    # ------------------------------------------------------------------ #
    # Invoice Number Extraction
    # ------------------------------------------------------------------ #
    def _extract_invoice_number(self, lines: List[str]) -> Optional[str]:
        for line in lines[:10]:  # check first 10 lines
            m = RE_INVOICE_NO.search(line)
            if m:
                return m.group(1).strip()
        # Fallback: look for standalone alphanumeric ID
        for line in lines[:5]:
            tokens = line.split()
            for tok in tokens:
                if re.match(r"^[A-Z]{2,4}\d{3,}", tok):
                    return tok
        return None

    # ------------------------------------------------------------------ #
    # Line Item Extraction
    # ------------------------------------------------------------------ #
    def _extract_items(self, lines: List[str]) -> Tuple[List[ParsedItem], float]:
        items = []
        confidences = []

        for line in lines:
            item = self._parse_line_item(line)
            if item:
                items.append(item)
                confidences.append(item.confidence)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return items, avg_conf

    def _parse_line_item(self, line: str) -> Optional[ParsedItem]:
        """Try to parse a single line as: ProductName Qty UnitPrice [Total]"""
        line = line.strip()
        if not line or len(line) < 3:
            return None

        # Skip header/total lines
        lower = line.lower()
        skip_patterns = [
            "invoice", "bill", "receipt", "total", "grand", "subtotal",
            "tax", "gst", "vat", "date", "customer", "name", "phone",
            "address", "बिल", "कुल", "दिनांक", "ग्राहक",
        ]
        if any(kw in lower for kw in skip_patterns):
            return None

        # Find all numbers in line
        numbers = self._extract_numbers(line)
        if len(numbers) < 2:
            return None

        # Extract product name (everything before the numbers)
        first_num_pos = self._find_first_number_pos(line)
        name = line[:first_num_pos].strip(" -:.|")
        if not name:
            return None

        # Assign numbers: [qty, price] or [qty, price, total]
        if len(numbers) == 2:
            qty, price = numbers[0], numbers[1]
            total = round(qty * price, 2)
            conf = 0.85
        elif len(numbers) >= 3:
            qty, price, total = numbers[0], numbers[1], numbers[2]
            expected_total = round(qty * price, 2)
            # Check consistency
            if abs(expected_total - total) > 0.05 * total:
                total = expected_total
                conf = 0.75  # lower confidence, recalculated
            else:
                conf = 0.95
        else:
            return None

        if qty <= 0 or price < 0:
            return None

        return ParsedItem(
            name=name,
            qty=qty,
            price=price,
            total=total,
            confidence=conf,
        )

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numeric values from text, handling commas."""
        matches = RE_NUMBER.findall(text)
        results = []
        for m in matches:
            try:
                results.append(float(m.replace(",", "")))
            except ValueError:
                pass
        return results

    def _find_first_number_pos(self, text: str) -> int:
        m = RE_NUMBER.search(text)
        return m.start() if m else len(text)

    # ------------------------------------------------------------------ #
    # Grand Total Extraction
    # ------------------------------------------------------------------ #
    def _extract_grand_total(
        self, lines: List[str], items: List[ParsedItem]
    ) -> Optional[float]:
        # Look for explicit total line
        total_keywords = ["total", "grand total", "amount", "कुल", "जमा", "योग",
                          "மொத்தம்", "మొత్తం"]
        for line in reversed(lines):
            lower = line.lower()
            if any(kw in lower for kw in total_keywords):
                nums = self._extract_numbers(line)
                if nums:
                    return nums[-1]

        # Fallback: sum of item totals
        if items:
            return round(sum(item.total for item in items), 2)
        return None