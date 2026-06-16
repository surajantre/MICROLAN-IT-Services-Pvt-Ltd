"""Unit Tests - Invoice Parser"""
import pytest
from services.parser import InvoiceParser


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


class TestInvoiceNumberExtraction:
    def test_extracts_inv_number(self, parser):
        lines = ["Invoice No: INV001", "Milk 2 30"]
        assert parser._extract_invoice_number(lines) == "INV001"

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

    def test_skips_total_line(self, parser):
        item = parser._parse_line_item("Total 160")
        assert item is None

    def test_skips_header_line(self, parser):
        item = parser._parse_line_item("Invoice Bill Receipt")
        assert item is None

    def test_parses_hindi_line(self, parser):
        item = parser._parse_line_item("दूध 2 30")
        assert item is not None
        assert "दूध" in item.name

    def test_auto_corrects_wrong_total(self, parser):
        # 2 * 30 = 60, not 70
        item = parser._parse_line_item("Milk 2 30 70")
        assert item is not None
        assert item.total == 60.0


class TestGrandTotal:
    def test_extracts_total_from_line(self, parser):
        lines = ["Milk 2 30 60", "Bread 1 40 40", "Total 100"]
        from services.parser import ParsedItem
        items = [ParsedItem("Milk", 2, 30, 60), ParsedItem("Bread", 1, 40, 40)]
        total = parser._extract_grand_total(lines, items)
        assert total == 100.0

    def test_computes_total_from_items(self, parser):
        from services.parser import ParsedItem
        items = [ParsedItem("Milk", 2, 30, 60), ParsedItem("Bread", 1, 40, 40)]
        total = parser._extract_grand_total([], items)
        assert total == 100.0


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
        assert result.language in ("hi/mr", "en")