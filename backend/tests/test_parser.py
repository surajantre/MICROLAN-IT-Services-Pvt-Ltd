

"""Unit Tests - Invoice Parser"""
import pytest
from ocr.parser import InvoiceParser, ParsedItem


@pytest.fixture
def parser():
    return InvoiceParser()


class TestLanguageDetection:
    def test_detects_english(self, parser):
        assert parser._detect_language("Milk Bread Butter") == "en"

    def test_detects_hindi(self, parser):
        assert parser._detect_language("दूध ब्रेड मक्खन") == "hi/mr"

    def test_detects_tamil(self, parser):
        assert parser._detect_language("பால் ரொட்டி") == "ta"

    def test_detects_telugu(self, parser):
        assert parser._detect_language("పాలు బ్రెడ్") == "te"

    def test_detects_gujarati(self, parser):
        assert parser._detect_language("દૂધ બ્રેડ") == "gu"


class TestInvoiceNumberExtraction:
    def test_extracts_inv_number(self, parser):
        lines = ["Invoice No: INV001", "Milk 2 30"]
        assert parser._extract_invoice_number(lines) == "INV001"

    def test_extracts_slash_format(self, parser):
        lines = ["Bill No: BL/2024/001", "Sugar 1 50"]
        assert parser._extract_invoice_number(lines) == "BL/2024/001"

    def test_no_invoice_number(self, parser):
        lines = ["Milk 2 30", "Bread 1 40"]
        assert parser._extract_invoice_number(lines) is None


class TestLineItemParsing:
    def test_parses_standard_english_line(self, parser):
        item = parser._parse_line_item("Milk 2 30 60")
        assert item is not None
        assert item.name == "Milk"
        assert item.qty == 2
        assert item.price == 30
        assert item.total == 60

    def test_parses_two_number_line(self, parser):
        item = parser._parse_line_item("Bread 1 40")
        assert item is not None
        assert item.qty == 1
        assert item.price == 40
        assert item.total == 40

    def test_skips_grand_total_line(self, parser):
        item = parser._parse_line_item("Grand Total 160")
        assert item is None

    def test_skips_subtotal_line(self, parser):
        item = parser._parse_line_item("Subtotal 160")
        assert item is None

    def test_skips_total_keyword_with_number(self, parser):
        # "Total 160" should be skipped — it is a totals line
        item = parser._parse_line_item("Total 160")
        assert item is None

    def test_skips_header_line(self, parser):
        item = parser._parse_line_item("Invoice No: INV-001")
        assert item is None

    def test_parses_hindi_line(self, parser):
        item = parser._parse_line_item("दूध 2 30")
        assert item is not None
        assert "दूध" in item.name

    def test_parses_hindi_three_numbers(self, parser):
        item = parser._parse_line_item("दूध 2 30 60")
        assert item is not None
        assert item.total == 60

    def test_parses_tamil_line(self, parser):
        item = parser._parse_line_item("பால் 2 30 60")
        assert item is not None
        assert "பால்" in item.name
        assert item.total == 60

    def test_parses_telugu_line(self, parser):
        item = parser._parse_line_item("పాలు 3 25 75")
        assert item is not None
        assert item.qty == 3
        assert item.price == 25

    def test_auto_corrects_wrong_total(self, parser):
        # 2 * 30 = 60, not 70
        item = parser._parse_line_item("Milk 2 30 70")
        assert item is not None
        assert item.total == 60.0
        assert item.confidence < 0.9  # lowered because total was corrected

    def test_skips_line_with_only_one_number(self, parser):
        item = parser._parse_line_item("Milk 2")
        assert item is None

    def test_skips_zero_quantity(self, parser):
        item = parser._parse_line_item("Milk 0 30")
        assert item is None


class TestGrandTotal:
    def test_extracts_total_from_explicit_line(self, parser):
        lines = ["Milk 2 30 60", "Bread 1 40 40", "Total 100"]
        items = [ParsedItem("Milk", 2, 30, 60), ParsedItem("Bread", 1, 40, 40)]
        total = parser._extract_grand_total(lines, items)
        assert total == 100.0

    def test_extracts_hindi_total_keyword(self, parser):
        lines = ["दूध 2 30 60", "कुल 60"]
        items = [ParsedItem("दूध", 2, 30, 60)]
        total = parser._extract_grand_total(lines, items)
        assert total == 60.0

    def test_computes_total_from_items_when_no_keyword(self, parser):
        items = [ParsedItem("Milk", 2, 30, 60), ParsedItem("Bread", 1, 40, 40)]
        total = parser._extract_grand_total([], items)
        assert total == 100.0

    def test_grand_total_keyword_wins_over_sum(self, parser):
        # Explicit "Grand Total" line should take precedence
        lines = ["Milk 2 30 60", "Bread 1 40 40", "Grand Total 105"]
        items = [ParsedItem("Milk", 2, 30, 60), ParsedItem("Bread", 1, 40, 40)]
        total = parser._extract_grand_total(lines, items)
        assert total == 105.0


class TestFullParse:
    def test_full_english_invoice(self, parser):
        lines = [
            "Invoice No: INV-2024-001",
            "Milk 2 30 60",
            "Bread 1 40 40",
            "Butter 1 60 60",
            "Grand Total 160",
        ]
        result = parser.parse(lines)
        assert result.invoice_no == "INV-2024-001"
        assert len(result.items) == 3
        assert result.grand_total == 160

    def test_full_hindi_invoice(self, parser):
        lines = [
            "दूध      2      30",
            "ब्रेड     1      40",
            "कुल 70",
        ]
        result = parser.parse(lines)
        assert len(result.items) >= 1
        assert result.language == "hi/mr"
        assert result.grand_total == 70.0

    def test_full_tamil_invoice(self, parser):
        lines = [
            "Invoice No: TN-001",
            "பால் 2 30 60",
            "ரொட்டி 1 40 40",
            "மொத்தம் 100",
        ]
        result = parser.parse(lines)
        assert result.invoice_no == "TN-001"
        assert len(result.items) >= 1
        assert result.language == "ta"

    def test_full_telugu_invoice(self, parser):
        lines = [
            "పాలు 3 25 75",
            "బ్రెడ్ 1 40 40",
            "మొత్తం 115",
        ]
        result = parser.parse(lines)
        assert len(result.items) >= 1
        assert result.language == "te"

    def test_mixed_language_invoice(self, parser):
        # Product names in Hindi, numbers in standard ASCII
        lines = [
            "Bill No: B001",
            "आटा 5 kg 50 250",
            "चावल 2 kg 60 120",
            "कुल 370",
        ]
        result = parser.parse(lines)
        assert len(result.items) >= 1
        assert result.grand_total is not None