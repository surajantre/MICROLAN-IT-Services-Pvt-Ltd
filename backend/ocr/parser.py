

# """
# AI Parsing Layer
# Converts raw OCR text lines -> structured invoice JSON
# Supports: English, Hindi, Marathi, Gujarati, Tamil, Telugu

# Parsing strategies (in order):
#   1. Same-line: "ProductName Qty Price [Total]" on one line (English style)
#   2. Multi-line grouping: name on one line, numbers on next (common in handwritten Indic)
#   3. Column alignment: numbers detected by position across lines
# """
# import re
# import logging
# from typing import List, Optional, Tuple
# from dataclasses import dataclass, field

# logger = logging.getLogger(__name__)

# # Devanagari digit -> ASCII digit mapping
# DEVANAGARI_DIGIT_MAP = str.maketrans("०१२३४५६७८९", "0123456789")

# # Gujarati digit -> ASCII digit
# GUJARATI_DIGIT_MAP = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")

# # Tamil digit -> ASCII digit
# TAMIL_DIGIT_MAP = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")

# # Telugu digit -> ASCII digit
# TELUGU_DIGIT_MAP = str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789")

# ALL_DIGIT_MAPS = [
#     DEVANAGARI_DIGIT_MAP,
#     GUJARATI_DIGIT_MAP,
#     TAMIL_DIGIT_MAP,
#     TELUGU_DIGIT_MAP,
# ]


# def normalize_digits(text: str) -> str:
#     """Convert any Indic script digits to ASCII digits."""
#     for mapping in ALL_DIGIT_MAPS:
#         text = text.translate(mapping)
#     return text


# # Regex: matches integers and decimals (after digit normalization)
# RE_NUMBER = re.compile(r"\b[\d,]+(?:\.\d+)?\b")

# RE_INVOICE_NO = re.compile(
#     r"(?:invoice|bill|inv|receipt|no|number|क्र|क्रमांक|नं)[.\s#:-]*([A-Z0-9\-/]{2,})",
#     re.IGNORECASE,
# )

# # Lines to skip: document-level headers/footers
# # Keep this list tight — do NOT add single Indic words that could be product names
# SKIP_PREFIXES = [
#     "invoice no", "bill no", "receipt no", "invoice date", "bill date",
#     "customer name", "customer address", "phone", "mobile", "email",
#     "gstin", "gst no", "pan no", "tax invoice", "cash memo",
#     "subtotal", "sub total", "grand total", "net total", "net amount",
#     "discount", "shipping", "delivery charge", "igst", "cgst", "sgst",
#     # Indic document-level markers
#     "दिनांक", "ग्राहक", "पता", "दूरभाष",
#     "மொத்த தொகை", "మొత్తం మొత్తం",
# ]

# # Single-word total markers: skip only when line = keyword + number
# TOTAL_ONLY_KEYWORDS = [
#     "total", "कुल", "जमा", "योग", "एकूण", "बाकी",
#     "மொத்தம்", "మొత్తం", "sum", "amount",
# ]


# @dataclass
# class ParsedItem:
#     name: str
#     qty: float
#     price: float
#     total: float
#     confidence: float = 1.0


# @dataclass
# class ParsedInvoice:
#     invoice_no: Optional[str] = None
#     items: List[ParsedItem] = field(default_factory=list)
#     grand_total: Optional[float] = None
#     language: Optional[str] = None
#     parsing_confidence: float = 0.0
#     warnings: List[str] = field(default_factory=list)
#     raw_text: str = ""


# class InvoiceParser:
#     """Multi-strategy invoice parser with fallback chain."""

#     def parse(self, text_lines: List[str], ocr_confidence: float = 0.9) -> ParsedInvoice:
#         raw_text = "\n".join(text_lines)
#         result = ParsedInvoice(raw_text=raw_text)

#         # Normalize all Indic digits to ASCII before any processing
#         norm_lines = [normalize_digits(line) for line in text_lines]

#         logger.debug("Parser input lines:\n%s", "\n".join(
#             f"  [{i}] {l}" for i, l in enumerate(norm_lines)
#         ))

#         result.language = self._detect_language(raw_text)
#         result.invoice_no = self._extract_invoice_number(norm_lines)

#         # Strategy 1: same-line items
#         items, conf = self._extract_items_same_line(norm_lines)

#         # Strategy 2: multi-line grouping (name line + number line)
#         # Use this if same-line found fewer than 2 items
#         if len(items) < 2:
#             items_ml, conf_ml = self._extract_items_multiline(norm_lines)
#             if len(items_ml) > len(items):
#                 items = items_ml
#                 conf = conf_ml
#                 logger.info("Switched to multi-line parsing strategy, found %d items", len(items))

#         result.items = items
#         result.parsing_confidence = conf
#         result.grand_total = self._extract_grand_total(norm_lines, items)

#         if not items:
#             result.warnings.append("No line items detected.")
#         if not result.invoice_no:
#             result.warnings.append("Invoice number not found.")

#         logger.info(
#             "Parsed %d items, lang=%s, inv=%s, grand_total=%s",
#             len(items), result.language, result.invoice_no, result.grand_total,
#         )
#         return result

#     # ------------------------------------------------------------------
#     # Language Detection
#     # ------------------------------------------------------------------
#     def _detect_language(self, text: str) -> str:
#         devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
#         gujarati   = sum(1 for c in text if "\u0A80" <= c <= "\u0AFF")
#         tamil      = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
#         telugu     = sum(1 for c in text if "\u0C00" <= c <= "\u0C7F")
#         latin      = sum(1 for c in text if c.isascii() and c.isalpha())
#         scores = {
#             "hi/mr": devanagari, "gu": gujarati,
#             "ta": tamil, "te": telugu, "en": latin,
#         }
#         best = max(scores, key=scores.get)
#         return best if scores[best] > 0 else "en"

#     # ------------------------------------------------------------------
#     # Invoice Number Extraction
#     # ------------------------------------------------------------------
#     def _extract_invoice_number(self, lines: List[str]) -> Optional[str]:
#         for line in lines[:10]:
#             m = RE_INVOICE_NO.search(line)
#             if m:
#                 return m.group(1).strip()
#         for line in lines[:5]:
#             for tok in line.split():
#                 if re.match(r"^[A-Z]{2,5}[-/]?\d{3,}", tok):
#                     return tok
#         return None

#     # ------------------------------------------------------------------
#     # Strategy 1: Same-line parsing
#     # ProductName  Qty  Price  [Total] — all on one line
#     # ------------------------------------------------------------------
#     def _extract_items_same_line(self, lines: List[str]) -> Tuple[List[ParsedItem], float]:
#         items, confidences = [], []
#         for line in lines:
#             item = self._parse_line_item(line)
#             if item:
#                 items.append(item)
#                 confidences.append(item.confidence)
#         avg = sum(confidences) / len(confidences) if confidences else 0.0
#         return items, avg

#     def _should_skip_line(self, line: str) -> bool:
#         lower = line.lower().strip()
#         if len(lower) < 2:
#             return True
#         for kw in SKIP_PREFIXES:
#             if lower.startswith(kw):
#                 return True
#         for kw in TOTAL_ONLY_KEYWORDS:
#             if lower.startswith(kw):
#                 remainder = lower[len(kw):].strip(" :.-")
#                 if re.match(r"^[\d,.\s]+$", remainder):
#                     return True
#         return False

#     def _parse_line_item(self, line: str) -> Optional[ParsedItem]:
#         """Parse one line as: Name Qty Price [Total]"""
#         line = line.strip()
#         if not line or len(line) < 3:
#             return None
#         if self._should_skip_line(line):
#             return None

#         numbers = self._extract_numbers(line)
#         if len(numbers) < 2:
#             return None

#         first_pos = self._find_first_number_pos(line)
#         name = line[:first_pos].strip(" -:.|,")
#         if not name:
#             return None

#         if len(numbers) == 2:
#             qty, price = numbers[0], numbers[1]
#             total = round(qty * price, 2)
#             conf = 0.85
#         elif len(numbers) >= 3:
#             qty, price, total = numbers[0], numbers[1], numbers[2]
#             expected = round(qty * price, 2)
#             tol = max(0.05 * total, 1.0)
#             if abs(expected - total) > tol:
#                 total = expected
#                 conf = 0.75
#             else:
#                 conf = 0.95
#         else:
#             return None

#         if qty <= 0 or price < 0:
#             return None

#         return ParsedItem(name=name, qty=qty, price=price, total=total, confidence=conf)

#     # ------------------------------------------------------------------
#     # Strategy 2: Multi-line grouping
#     #
#     # Handwritten Indic invoices often look like:
#     #   दूध                <- product name line (no numbers)
#     #   2  30  60          <- qty / price / total on the next line
#     #
#     # OR a table where each row is split across lines because EasyOCR
#     # reads columns top-to-bottom before moving right.
#     #
#     # Algorithm:
#     #   - A "name line" has no numbers (or only 1 number that could be serial)
#     #   - A "number line" has 2+ numbers and no significant text
#     #   - Pair consecutive name+number lines
#     # ------------------------------------------------------------------
#     def _extract_items_multiline(self, lines: List[str]) -> Tuple[List[ParsedItem], float]:
#         items, confidences = [], []
#         i = 0
#         while i < len(lines):
#             line = lines[i].strip()
#             if not line or self._should_skip_line(line):
#                 i += 1
#                 continue

#             numbers = self._extract_numbers(line)
#             text_part = RE_NUMBER.sub("", line).strip(" -:.|,")

#             # Name line: has meaningful text, fewer than 2 numbers
#             is_name_line = bool(text_part) and len(text_part) > 1 and len(numbers) < 2

#             if is_name_line and i + 1 < len(lines):
#                 next_line = lines[i + 1].strip()
#                 next_nums = self._extract_numbers(next_line)
#                 next_text = RE_NUMBER.sub("", next_line).strip()

#                 # Number line: 2+ numbers, minimal text
#                 if len(next_nums) >= 2 and len(next_text) <= 3:
#                     name = text_part
#                     if len(next_nums) == 2:
#                         qty, price = next_nums[0], next_nums[1]
#                         total = round(qty * price, 2)
#                         conf = 0.80
#                     else:
#                         qty, price, total = next_nums[0], next_nums[1], next_nums[2]
#                         expected = round(qty * price, 2)
#                         tol = max(0.05 * total, 1.0)
#                         conf = 0.90 if abs(expected - total) <= tol else 0.70
#                         if conf == 0.70:
#                             total = expected

#                     if qty > 0 and price >= 0:
#                         items.append(ParsedItem(
#                             name=name, qty=qty, price=price,
#                             total=total, confidence=conf,
#                         ))
#                         confidences.append(conf)
#                         i += 2  # consumed both lines
#                         continue

#             i += 1

#         avg = sum(confidences) / len(confidences) if confidences else 0.0
#         return items, avg

#     # ------------------------------------------------------------------
#     # Helpers
#     # ------------------------------------------------------------------
#     def _extract_numbers(self, text: str) -> List[float]:
#         results = []
#         for m in RE_NUMBER.findall(text):
#             try:
#                 results.append(float(m.replace(",", "")))
#             except ValueError:
#                 pass
#         return results

#     def _find_first_number_pos(self, text: str) -> int:
#         m = RE_NUMBER.search(text)
#         return m.start() if m else len(text)

#     # ------------------------------------------------------------------
#     # Grand Total Extraction
#     # ------------------------------------------------------------------
#     def _extract_grand_total(
#         self, lines: List[str], items: List[ParsedItem]
#     ) -> Optional[float]:
#         total_keywords = [
#             "grand total", "net total", "total amount", "amount due",
#             "total", "कुल", "जमा", "योग", "एकूण", "बाकी", "कुल राशि",
#             "மொத்தம்", "மொத்த தொகை", "మొత్తం",
#         ]
#         for line in reversed(lines):
#             lower = line.lower()
#             if any(kw in lower for kw in total_keywords):
#                 nums = self._extract_numbers(line)
#                 if nums:
#                     return nums[-1]
#         if items:
#             return round(sum(item.total for item in items), 2)
#         return None





"""
AI Parsing Layer — High-Accuracy Invoice Parser
Handles: English, Hindi (Devanagari), Marathi, Gujarati, Tamil, Telugu

Key formats supported:
  1. "Item  Qty @ Rate/unit  Total"   — standard @ format
  2. "Item  Qty  Rate  Total"         — column format (no @)
  3. "1. Item  Qty @ Rate  Total"     — numbered rows
  4. Multi-line: name on one line, numbers on next

Critical fixes:
  - Middle-dot (·) treated as decimal separator (common in handwritten Indian invoices)
  - Indic script digits normalized to ASCII before parsing
  - Qty+unit combos like "5 किलो", "1L", "500g", "2 लीटर" extracted correctly
  - Numbers embedded in item names (e.g. "5kg") not mistaken for qty/price columns
  - "@" sign used to reliably split qty from rate
"""
import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indic digit normalization
# ---------------------------------------------------------------------------
DIGIT_TRANS = str.maketrans(
    "०१२३४५६७८९"   # Devanagari
    "૦૧૨૩૪૫૬૭૮૯"  # Gujarati
    "௦௧௨௩௪௫௬௭௮௯"  # Tamil
    "౦౧౨౩౪౫౬౭౮౯",  # Telugu
    "0123456789" * 4,
)


def normalize_text(text: str) -> str:
    """Normalize Indic digits, middle-dot decimals, rupee symbols, noise."""
    text = text.translate(DIGIT_TRANS)
    # Middle-dot (·) used as decimal in Indian handwriting → real decimal
    text = text.replace("·", ".").replace("•", ".")
    # Rupee sign variants
    text = text.replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("/-", "")
    # Remove serial-number prefixes like "1.", "२.", "੧." at start of line
    text = re.sub(r"^\s*[\d]+\s*[.)]\s*", "", text)
    return text


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# A "clean" number: digits with optional commas and one decimal point
# Also matches numbers that had middle-dot replaced above
RE_NUM = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")

# Quantity with embedded unit: "5 किलो", "10 किलो", "2 लीटर", "1L", "500g", "2 kg"
# Captures: (numeric_part, unit_part)
RE_QTY_UNIT = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*"
    r"(किलो|कि\.?ग्रा\.?|किग्रा|लीटर|ली\.?|li\.?|ltr|litre|liter|"
    r"kg|kgs|gm|gms|gram|g\b|ml|ltr|l\b|pcs|nos|units?|"
    r"કિલો|કિ\.?ગ્રા\.?|લીટર|"
    r"கிலோ|லிட்டர்|"
    r"కిలో|లీటర్)",
    re.IGNORECASE,
)

# "@" separator: "Qty [unit] @ Rate[/unit]"
RE_AT_SPLIT = re.compile(r"@")

# Invoice number patterns
RE_INVOICE_NO = re.compile(
    r"(?:invoice|bill|inv|receipt|no|number|क्र|क्रमांक|नं)[.\s#:-]*([A-Z0-9\-/]{2,})",
    re.IGNORECASE,
)

# Lines to ALWAYS skip (very specific — we keep this tight to avoid dropping product lines)
SKIP_EXACT = {
    "total", "grand total", "net total", "subtotal", "sub total",
    "कुल", "कुल राशि", "कुल योग", "एकूण", "एकुण", "बाकी", "जमा", "योग",
    "மொத்தம்", "மொத்த தொகை", "మొత్తం",
    "कुल सरवालो", "कुल योग",
}

# Prefixes that mark a line as a header/footer (not a product)
SKIP_PREFIXES = (
    "date", "दिनांक", "तारीख:", "तारीख :", "जमेर:", "मलन:",
    "gstin", "gst no", "pan", "tax invoice", "cash memo",
    "phone", "mobile", "email", "address", "customer",
    "item", "वस्तु", "description", "particulars",
    "s.no", "sr.", "sr.no", "क्र.", "क्रमांक", "no.", "नं.",
    "qty", "quantity", "जथ्थो", "मात्रा", "गते",
    "rate", "price", "भाव", "दर", "दाम", "मूल्य", "दूल",
    "amount", "total", "कुल", "एकूण", "मोत्थ", "मोत्थम्",
    "watermark",
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


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

class InvoiceParser:

    def parse(self, text_lines: List[str], ocr_confidence: float = 0.9) -> ParsedInvoice:
        raw_text = "\n".join(text_lines)
        result = ParsedInvoice(raw_text=raw_text)
        result.language = self._detect_language(raw_text)

        # Normalize every line
        norm = [normalize_text(ln) for ln in text_lines]

        logger.debug("=== Parser input (%d lines, lang=%s) ===", len(norm), result.language)
        for i, ln in enumerate(norm):
            logger.debug("  [%02d] %r", i, ln)

        result.invoice_no = self._extract_invoice_number(norm)

        # Try strategies in order; pick whichever yields more items
        items_at,   conf_at   = self._strategy_at_sign(norm)
        items_col,  conf_col  = self._strategy_column(norm)
        items_ml,   conf_ml   = self._strategy_multiline(norm)

        logger.debug("Strategy results: @=%d  col=%d  multiline=%d",
                     len(items_at), len(items_col), len(items_ml))

        # Pick the strategy with the most items; break ties by confidence
        best = max(
            [(items_at, conf_at), (items_col, conf_col), (items_ml, conf_ml)],
            key=lambda t: (len(t[0]), t[1]),
        )
        result.items, result.parsing_confidence = best

        result.grand_total = self._extract_grand_total(norm, result.items)

        if not result.items:
            result.warnings.append("No line items detected.")
        if not result.invoice_no:
            result.warnings.append("Invoice number not found.")

        logger.info(
            "Parsed %d items (lang=%s, inv=%s, total=%s)",
            len(result.items), result.language, result.invoice_no, result.grand_total,
        )
        return result

    # -----------------------------------------------------------------------
    # Language detection
    # -----------------------------------------------------------------------
    def _detect_language(self, text: str) -> str:
        scores = {
            "hi/mr": sum(1 for c in text if "\u0900" <= c <= "\u097F"),
            "gu":    sum(1 for c in text if "\u0A80" <= c <= "\u0AFF"),
            "ta":    sum(1 for c in text if "\u0B80" <= c <= "\u0BFF"),
            "te":    sum(1 for c in text if "\u0C00" <= c <= "\u0C7F"),
            "en":    sum(1 for c in text if c.isascii() and c.isalpha()),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "en"

    # -----------------------------------------------------------------------
    # Invoice number
    # -----------------------------------------------------------------------
    def _extract_invoice_number(self, lines: List[str]) -> Optional[str]:
        for line in lines[:10]:
            m = RE_INVOICE_NO.search(line)
            if m:
                return m.group(1).strip()
        return None

    # -----------------------------------------------------------------------
    # Line classification helpers
    # -----------------------------------------------------------------------
    def _is_skip_line(self, line: str) -> bool:
        s = line.strip().lower()
        if not s or len(s) < 2:
            return True
        if s in SKIP_EXACT:
            return True
        for pfx in SKIP_PREFIXES:
            if s.startswith(pfx):
                return True
        # Line is only numbers/symbols → likely a total or divider
        if re.match(r"^[\d\s,.\-=:₹/]+$", s):
            return True
        return False

    def _extract_numbers(self, text: str) -> List[float]:
        nums = []
        for m in RE_NUM.findall(text):
            try:
                nums.append(float(m.replace(",", "")))
            except ValueError:
                pass
        return nums

    def _strip_name_noise(self, name: str) -> str:
        """Remove leading serial numbers, punctuation noise from item names."""
        name = re.sub(r"^[\d]+\s*[.)]\s*", "", name.strip())
        name = name.strip(" -:.|,@")
        return name

    # -----------------------------------------------------------------------
    # Strategy 1: @ sign — "Name  Qty[unit] @ Rate[/unit]  Total"
    #
    # This is the dominant format in all 6 sample invoices.
    # Split on "@": left part has name+qty, right part has rate[/unit][total]
    # -----------------------------------------------------------------------
    def _strategy_at_sign(self, lines: List[str]) -> Tuple[List[ParsedItem], float]:
        items, confs = [], []
        for line in lines:
            if self._is_skip_line(line):
                continue
            if "@" not in line:
                continue
            item = self._parse_at_line(line)
            if item:
                items.append(item)
                confs.append(item.confidence)
        avg = sum(confs) / len(confs) if confs else 0.0
        return items, avg

    def _parse_at_line(self, line: str) -> Optional[ParsedItem]:
        """
        Parse lines like:
          "Rice (Basmati) 5kg @ 110.00/kg  - 550.00"
          "బాస్మతీ చోఖా  ప కిలో @ ૧૨૦.00/કિલો  ૬00.00"
          "मसाला डोसा 1 @ 120.00  120.00"
        """
        parts = RE_AT_SPLIT.split(line, maxsplit=1)
        if len(parts) != 2:
            return None

        left, right = parts[0], parts[1]

        # --- Extract qty from left side ---
        qty = self._extract_qty(left)
        if qty is None or qty <= 0:
            return None

        # --- Extract item name (left side minus the qty+unit) ---
        name = self._extract_name_from_left(left, qty)
        if not name:
            return None

        # --- Extract rate and optional total from right side ---
        # Right looks like: "110.00/kg  - 550.00" or "120.00  120.00" or "850.00  850.00"
        right_nums = self._extract_numbers(right)
        if not right_nums:
            return None

        rate = right_nums[0]
        expected = round(qty * rate, 2)

        if len(right_nums) >= 2:
            stated_total = right_nums[-1]
            tol = max(0.05 * max(expected, 1), 2.0)
            if abs(stated_total - expected) <= tol:
                total = stated_total
                conf = 0.95
            else:
                # Some invoices show "each" price, not cumulative — trust expected
                total = expected
                conf = 0.80
        else:
            total = expected
            conf = 0.85

        if rate < 0:
            return None

        return ParsedItem(
            name=name, qty=qty, price=rate, total=round(total, 2), confidence=conf
        )

    def _extract_qty(self, text: str) -> Optional[float]:
        """
        Extract the numeric quantity from the left side of @.
        Handles: "5 किलो", "10 किलो", "1L", "500g", "2 लीटर", "1", "2"
        Prefers qty+unit matches; falls back to last number before @.
        """
        # Try qty+unit pattern first
        matches = list(RE_QTY_UNIT.finditer(text))
        if matches:
            # Use the last match (closest to the @ sign)
            m = matches[-1]
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
        # Fallback: last number in the left-of-@ text
        nums = self._extract_numbers(text)
        if nums:
            return nums[-1]
        return None

    def _extract_name_from_left(self, left: str, qty: float) -> str:
        """
        Remove the qty (and its unit) from the left side to get the item name.
        """
        # Remove qty+unit combo
        result = RE_QTY_UNIT.sub("", left)
        # Remove any remaining standalone number equal to qty
        qty_str = str(int(qty)) if qty == int(qty) else str(qty)
        result = re.sub(r"\b" + re.escape(qty_str) + r"\b", "", result)
        return self._strip_name_noise(result)

    # -----------------------------------------------------------------------
    # Strategy 2: Column format — "Name  Qty  Rate  Total" (no @)
    #
    # Detect lines that have a text part followed by 2–3 numbers.
    # -----------------------------------------------------------------------
    def _strategy_column(self, lines: List[str]) -> Tuple[List[ParsedItem], float]:
        items, confs = [], []
        for line in lines:
            if self._is_skip_line(line):
                continue
            if "@" in line:
                continue  # handled by strategy 1
            item = self._parse_column_line(line)
            if item:
                items.append(item)
                confs.append(item.confidence)
        avg = sum(confs) / len(confs) if confs else 0.0
        return items, avg

    def _parse_column_line(self, line: str) -> Optional[ParsedItem]:
        """
        Parse: "साबण  4  35.00  350.00"  or  "Rice  5  110.00  550.00"
        Must have text part + at least 2 numbers.
        """
        # Find where numbers start
        m = RE_NUM.search(line)
        if not m:
            return None

        name_part = line[:m.start()].strip()
        num_part  = line[m.start():]

        name = self._strip_name_noise(name_part)
        if not name or len(name) < 1:
            return None

        nums = self._extract_numbers(num_part)
        if len(nums) < 2:
            return None

        # Filter out noise numbers (e.g. serial "1.", "2.")
        # Heuristic: first number that looks like a reasonable qty (< 10000, > 0)
        qty   = nums[0]
        rate  = nums[1]
        expected = round(qty * rate, 2)

        if len(nums) >= 3:
            stated = nums[2]
            tol = max(0.05 * max(expected, 1), 2.0)
            if abs(stated - expected) <= tol:
                total = stated
                conf = 0.92
            else:
                total = expected
                conf = 0.72
        else:
            total = expected
            conf = 0.82

        if qty <= 0 or rate < 0:
            return None

        return ParsedItem(
            name=name, qty=qty, price=rate, total=round(total, 2), confidence=conf
        )

    # -----------------------------------------------------------------------
    # Strategy 3: Multi-line — name line then number line
    # -----------------------------------------------------------------------
    def _strategy_multiline(self, lines: List[str]) -> Tuple[List[ParsedItem], float]:
        items, confs = [], []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or self._is_skip_line(line):
                i += 1
                continue

            nums_this = self._extract_numbers(line)
            text_only = RE_NUM.sub("", line).strip(" -:.|,@")

            # Name line: has meaningful text, 0 or 1 numbers (could be serial)
            is_name_line = bool(text_only) and len(text_only) > 1 and len(nums_this) <= 1

            if is_name_line and i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                nxt_nums = self._extract_numbers(nxt)
                nxt_text = RE_NUM.sub("", nxt).strip()

                if len(nxt_nums) >= 2 and len(nxt_text) <= 4:
                    name = self._strip_name_noise(text_only)
                    if name:
                        qty, rate = nxt_nums[0], nxt_nums[1]
                        expected  = round(qty * rate, 2)
                        if len(nxt_nums) >= 3:
                            stated = nxt_nums[2]
                            tol = max(0.05 * max(expected, 1), 2.0)
                            total = stated if abs(stated - expected) <= tol else expected
                            conf  = 0.88 if total == stated else 0.70
                        else:
                            total = expected
                            conf  = 0.78

                        if qty > 0 and rate >= 0:
                            items.append(ParsedItem(
                                name=name, qty=qty, price=rate,
                                total=round(total, 2), confidence=conf,
                            ))
                            confs.append(conf)
                            i += 2
                            continue
            i += 1

        avg = sum(confs) / len(confs) if confs else 0.0
        return items, avg

    # -----------------------------------------------------------------------
    # Grand total extraction
    # -----------------------------------------------------------------------
    def _extract_grand_total(
        self, lines: List[str], items: List[ParsedItem]
    ) -> Optional[float]:
        total_kws = [
            "grand total", "net total", "total amount", "कुल योग", "कुल सरवालो",
            "total", "कुल", "जमा", "योग", "एकूण", "एकुण", "बाकी",
            "மொத்தம்", "మొత్తం", "मोत्थम्", "मोत्थ",
        ]
        for line in reversed(lines):
            lower = line.lower()
            if any(kw in lower for kw in total_kws):
                nums = self._extract_numbers(line)
                if nums:
                    # Take the largest number on the total line (most likely the total)
                    return max(nums)
        if items:
            return round(sum(i.total for i in items), 2)
        return None