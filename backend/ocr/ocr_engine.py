


"""
OCR Abstraction Layer
Primary: EasyOCR (stable on Python 3.11, Windows, no version conflicts)
Secondary: PaddleOCR (with version-safe init)
Also: Google Vision, Azure Form Recognizer, AWS Textract
"""
import logging
import pytesseract
import os
import tempfile
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Language Normalization
# -----------------------------------------------------------------------------

LANG_NORM_MAP = {
    "en": "en", "eng": "en", "english": "en",
    "hi": "hi", "hin": "hi", "hindi": "hi",
    "mr": "mr", "mar": "mr", "marathi": "mr",
    "gu": "gu", "guj": "gu", "gujarati": "gu",
    "ta": "ta", "tam": "ta", "tamil": "ta",
    "te": "te", "tel": "te", "telugu": "te",
    "auto": "auto", "detect": "auto",
}


def normalize_language_code(language: str) -> str:
    """Normalizes mixed-case, whitespace-padded, or full-name language codes."""
    if not language:
        return "en"
    return LANG_NORM_MAP.get(str(language).strip().lower(), "en")


# -----------------------------------------------------------------------------
# Base Interface
# -----------------------------------------------------------------------------

class BaseOCRAdapter(ABC):
    """Abstract OCR adapter — swap providers without changing business logic."""

    @abstractmethod
    def extract_text(
        self, image: np.ndarray, language: str = "en"
    ) -> Tuple[List[str], float]:
        """Returns (list_of_text_lines, avg_confidence_0_to_1)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# -----------------------------------------------------------------------------
# EasyOCR Adapter
# EasyOCR language codes: https://www.jaided.ai/easyocr/
# -----------------------------------------------------------------------------

# EasyOCR script-compatibility rules:
#   - Each script group can only be combined with English ("en").
#   - Scripts from different groups CANNOT be mixed in one reader.
#   - Groups: Devanagari (hi), Dravidian (ta, te), Gujarati (gu) — each is separate.
#   - "auto" uses English-only so the reader initializes without conflict;
#     the language-detection in parser.py then identifies the actual script post-OCR.
#     For explicit Indic languages the correct per-script reader is used.
EASYOCR_LANG_MAP = {
    "en":   ["en"],
    "hi":   ["hi", "en"],   # Hindi — Devanagari script + English
    "mr":   ["hi", "en"],   # Marathi uses same Devanagari model as Hindi
    "gu":   ["gu", "en"],   # Gujarati script + English
    "ta":   ["ta", "en"],   # Tamil — Dravidian script, English-only companion allowed
    "te":   ["te", "en"],   # Telugu — Dravidian script, English-only companion allowed
    # "auto" must NOT combine scripts from different groups.
    # Use English-only; the parser detects the script from the extracted text.
    "auto": ["en"],
}


class EasyOCRAdapter(BaseOCRAdapter):
    """
    EasyOCR adapter — compatible with Python 3.11 + Windows.
    Free, open-source, no version conflicts, multilingual.
    Install: pip install easyocr
    Models (~100 MB each) auto-downloaded on first use.
    """

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._readers: dict = {}

    def _get_reader(self, language: str):
        norm_lang = normalize_language_code(language)
        langs = EASYOCR_LANG_MAP.get(norm_lang, ["en"])
        key = "_".join(langs)

        if key not in self._readers:
            try:
                import easyocr
                logger.info("Initializing EasyOCR for langs=%s (requested: %s)", langs, language)
                self._readers[key] = easyocr.Reader(
                    langs,
                    gpu=self.use_gpu,
                    verbose=False,
                )
                logger.info("EasyOCR initialized successfully for langs: %s", key)
            except ImportError:
                raise RuntimeError("EasyOCR not installed. Run: pip install easyocr")
        return self._readers[key]

    def extract_text(
        self, image: np.ndarray, language: str = "en"
    ) -> Tuple[List[str], float]:
        if not isinstance(image, np.ndarray):
            raise ValueError("Input image must be a numpy array")
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)
        image = np.ascontiguousarray(image)

        reader = self._get_reader(language)
        results = reader.readtext(image, detail=1, paragraph=False)

        if not results:
            return [], 0.0

        lines, confidences = [], []
        for (_, text, conf) in results:
            text = text.strip()
            if text:
                lines.append(text)
                confidences.append(float(conf))

        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        logger.info(
            "EasyOCR extracted %d regions, language=%s, avg_conf=%.3f",
            len(lines), language, avg_conf,
        )
        return lines, avg_conf

    @property
    def name(self) -> str:
        return "EasyOCR"


# -----------------------------------------------------------------------------
# PaddleOCR Adapter
#
# PaddleOCR supported lang codes (2.x / 3.x):
#   en, ch, japan, korean, hi (hindi), ta (tamil), te (telugu),
#   ka (kannada), latin, arabic, cyrillic, devanagari
#
# NOTE: There is no "gu" (Gujarati) model in PaddleOCR — falls back to "en".
#       For Gujarati, prefer EasyOCR which has a native Gujarati model.
# -----------------------------------------------------------------------------

PADDLE_LANG_MAP = {
    "en":   "en",
    "hi":   "hi",           # PaddleOCR has a Hindi model ("hi") since 2.6
    "mr":   "hi",           # Marathi uses same Devanagari model as Hindi
    "gu":   "en",           # No Gujarati PaddleOCR model; EasyOCR recommended
    "ta":   "ta",
    "te":   "te",
    "auto": "ch",           # Chinese + Latin multilingual model covers more scripts
}

# Languages where PaddleOCR has no native model — warn and suggest EasyOCR
PADDLE_UNSUPPORTED = {"gu"}


class PaddleOCRAdapter(BaseOCRAdapter):
    """
    PaddleOCR adapter.
    Compatible pairs:
      paddlepaddle==2.6.2 + paddleocr==2.7.3  (Python <= 3.10)
      paddlepaddle==3.0.0 + paddleocr==2.9.1  (Python 3.11+, Linux)

    NOTE: For Gujarati (gu), PaddleOCR has no native model. Switch to EasyOCR
          (OCR_PROVIDER=easyocr in .env) for best Gujarati results.
    """

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._engines: dict = {}

    def _get_engine(self, lang: str):
        norm_lang = normalize_language_code(lang)
        paddle_lang = PADDLE_LANG_MAP.get(norm_lang, "en")

        if norm_lang in PADDLE_UNSUPPORTED:
            logger.warning(
                "PaddleOCR has no native model for language '%s'. "
                "Falling back to 'en'. Consider switching to EasyOCR for this language.",
                norm_lang,
            )

        if paddle_lang not in self._engines:
            try:
                from paddleocr import PaddleOCR

                logger.info(
                    "Initializing PaddleOCR lang=%s (requested: %s)", paddle_lang, lang
                )
                base_kwargs = {"use_angle_cls": True, "lang": paddle_lang}
                engine = None

                # Try use_gpu API first (older PaddleOCR)
                try:
                    engine = PaddleOCR(**base_kwargs, use_gpu=self.use_gpu)
                    logger.info("PaddleOCR init OK (use_gpu API)")
                except (TypeError, ValueError, AttributeError) as e1:
                    logger.debug("use_gpu API failed: %s — trying device API", e1)

                    # Try device API (PaddleOCR 2.8+ / 3.x)
                    try:
                        engine = PaddleOCR(
                            **base_kwargs,
                            device="gpu" if self.use_gpu else "cpu",
                        )
                        logger.info("PaddleOCR init OK (device API)")
                    except (TypeError, ValueError, AttributeError) as e2:
                        logger.debug("device API failed: %s — trying CPU fallback", e2)

                        # Plain CPU fallback
                        try:
                            engine = PaddleOCR(**base_kwargs)
                            logger.info("PaddleOCR init OK (CPU fallback)")
                        except Exception as e3:
                            raise RuntimeError(
                                f"Failed to initialize PaddleOCR: {e3}\n"
                                "Fix: verify paddlepaddle and paddleocr version compatibility."
                            )

                self._engines[paddle_lang] = engine

            except ImportError:
                raise RuntimeError(
                    "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle"
                )

        return self._engines[paddle_lang]

    def extract_text(
        self, image: np.ndarray, language: str = "en"
    ) -> Tuple[List[str], float]:
        if not isinstance(image, np.ndarray):
            raise ValueError("Input image must be a numpy array")
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)
        image = np.ascontiguousarray(image)

        engine = self._get_engine(language)

        try:
            result = engine.ocr(image, cls=True)
        except Exception as e:
            logger.warning(
                "Direct array inference failed: %s. Falling back to temp file.", e
            )
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                cv2.imwrite(tmp.name, image)
                tmp_path = tmp.name
            try:
                result = engine.ocr(tmp_path, cls=True)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        if not result or not result[0]:
            return [], 0.0

        lines, confidences = [], []
        for block in result:
            if not block:
                continue
            for line in block:
                text = line[1][0]
                conf = float(line[1][1])
                if text.strip():
                    lines.append(text.strip())
                    confidences.append(conf)

        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        logger.info(
            "PaddleOCR extracted %d regions, language=%s, avg_conf=%.3f",
            len(lines), language, avg_conf,
        )
        return lines, avg_conf

    @property
    def name(self) -> str:
        return "PaddleOCR"

class TesseractAdapter(BaseOCRAdapter):

    LANG_MAP = {
        "en": "eng",
        "hi": "hin",
        "mr": "hin",
        "gu": "guj",
        "ta": "tam",
        "te": "tel",
        "auto": "eng",
    }

    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

    def extract_text(
        self,
        image: np.ndarray,
        language: str = "en"
    ):
        lang = self.LANG_MAP.get(language, "eng")

        config = (
            "--oem 3 "
            "--psm 6 "
            "-c preserve_interword_spaces=1"
        )

        text = pytesseract.image_to_string(
            image,
            lang=lang,
            config=config
        )

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        return lines, 0.85

    @property
    def name(self):
        return "Tesseract"
# -----------------------------------------------------------------------------
# Cloud Adapters
# -----------------------------------------------------------------------------

class GoogleVisionAdapter(BaseOCRAdapter):
    def __init__(self, credentials_path: str = ""):
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google.cloud import vision
                self._client = vision.ImageAnnotatorClient()
            except ImportError:
                raise RuntimeError("Install: pip install google-cloud-vision")
        return self._client

    def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
        from google.cloud import vision
        client = self._get_client()
        _, buffer = cv2.imencode(".png", image)
        gv_image = vision.Image(content=buffer.tobytes())
        response = client.text_detection(image=gv_image)
        if response.error.message:
            raise RuntimeError(f"Google Vision error: {response.error.message}")
        texts = response.text_annotations
        if not texts:
            return [], 0.0
        lines = [ln.strip() for ln in texts[0].description.split("\n") if ln.strip()]
        return lines, 0.90

    @property
    def name(self) -> str:
        return "GoogleVision"


class AzureFormRecognizerAdapter(BaseOCRAdapter):
    def __init__(self, endpoint: str, key: str):
        self.endpoint = endpoint
        self.key = key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from azure.ai.formrecognizer import DocumentAnalysisClient
                from azure.core.credentials import AzureKeyCredential
                self._client = DocumentAnalysisClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.key),
                )
            except ImportError:
                raise RuntimeError("Install: pip install azure-ai-formrecognizer")
        return self._client

    def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
        client = self._get_client()
        _, buffer = cv2.imencode(".png", image)
        poller = client.begin_analyze_document("prebuilt-read", buffer.tobytes())
        result = poller.result()
        lines, confidences = [], []
        for page in result.pages:
            for line in page.lines:
                lines.append(line.content)
                if hasattr(line, "confidence") and line.confidence:
                    confidences.append(line.confidence)
        return lines, float(np.mean(confidences)) if confidences else 0.85

    @property
    def name(self) -> str:
        return "AzureFormRecognizer"


class AWSTextractAdapter(BaseOCRAdapter):
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client("textract", region_name=self.region)
            except ImportError:
                raise RuntimeError("Install: pip install boto3")
        return self._client

    def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
        client = self._get_client()
        _, buffer = cv2.imencode(".png", image)
        response = client.detect_document_text(Document={"Bytes": buffer.tobytes()})
        lines, confidences = [], []
        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                lines.append(block["Text"])
                confidences.append(block.get("Confidence", 90.0) / 100.0)
        return lines, float(np.mean(confidences)) if confidences else 0.85

    @property
    def name(self) -> str:
        return "AWSTextract"


# -----------------------------------------------------------------------------
# PDF Rendering
# -----------------------------------------------------------------------------

def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[np.ndarray]:
    """Converts PDF pages into numpy arrays (BGR) using PyMuPDF."""
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            raise RuntimeError(
                "PyMuPDF not installed. Run: pip install pymupdf"
            )

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        zoom = dpi / 72
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, 3
        )
        img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
        images.append(img_bgr)
    doc.close()
    return images


def convert_pdf_to_images_fallback(pdf_bytes: bytes) -> List[np.ndarray]:
    """Alternative PDF converter using pdf2image."""
    try:
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(pdf_bytes, dpi=200)
        return [cv2.cvtColor(np.array(p), cv2.COLOR_RGB2BGR) for p in pages]
    except ImportError:
        raise RuntimeError("Neither PyMuPDF nor pdf2image are available.")


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_ocr_engine(provider: str = "easyocr", **kwargs) -> BaseOCRAdapter:
    # adapters = {
    #     "easyocr":   lambda: EasyOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
    #     "paddleocr": lambda: PaddleOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
    #     "google":    lambda: GoogleVisionAdapter(kwargs.get("credentials_path", "")),
    #     "azure":     lambda: AzureFormRecognizerAdapter(
    #                      kwargs.get("endpoint", ""), kwargs.get("key", "")),
    #     "aws":       lambda: AWSTextractAdapter(kwargs.get("region", "us-east-1")),
    # }
    adapters = {
        "easyocr": lambda: EasyOCRAdapter(),
        "paddleocr": lambda: PaddleOCRAdapter(),
        "tesseract": lambda: TesseractAdapter(),
        "google": lambda: GoogleVisionAdapter(),
        "azure": lambda: AzureFormRecognizerAdapter(),
        "aws": lambda: AWSTextractAdapter(),
    }
    factory = adapters.get(provider.lower())
    if not factory:
        raise ValueError(
            f"Unknown OCR provider: '{provider}'. Choose from: {list(adapters.keys())}"
        )
    return factory()


_ocr_engine: Optional[BaseOCRAdapter] = None


def get_ocr_engine() -> BaseOCRAdapter:
    """Returns a singleton OCR engine using settings defaults."""
    global _ocr_engine
    if _ocr_engine is None:
        from core.config import settings
        _ocr_engine = create_ocr_engine(
            provider=settings.OCR_PROVIDER,
            use_gpu=settings.PADDLE_USE_GPU,
            credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS,
            endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
            key=settings.AZURE_FORM_RECOGNIZER_KEY,
            region=settings.AWS_REGION,
        )
        logger.info("OCR engine initialized: %s", _ocr_engine.name)
    return _ocr_engine