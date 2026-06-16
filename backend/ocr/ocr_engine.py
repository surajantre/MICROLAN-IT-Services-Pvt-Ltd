

# """
# OCR Abstraction Layer
# Primary: EasyOCR (stable on Python 3.11, Windows, no version conflicts)
# Secondary: PaddleOCR (with version-safe init)
# Also: Google Vision, Azure Form Recognizer, AWS Textract
# """
# import logging
# import os
# import tempfile
# from abc import ABC, abstractmethod
# from typing import List, Optional, Tuple

# import cv2
# import numpy as np

# logger = logging.getLogger(__name__)


# # ─────────────────────────────────────────────────────────────────────────────
# # Base Interface
# # ─────────────────────────────────────────────────────────────────────────────

# class BaseOCRAdapter(ABC):
#     """Abstract OCR adapter — swap providers without changing business logic."""

#     @abstractmethod
#     def extract_text(
#         self, image: np.ndarray, language: str = "en"
#     ) -> Tuple[List[str], float]:
#         """Returns (list_of_text_lines, avg_confidence_0_to_1)."""
#         ...

#     @property
#     @abstractmethod
#     def name(self) -> str: ...


# # ─────────────────────────────────────────────────────────────────────────────
# # EasyOCR Adapter  ← NEW PRIMARY (Python 3.11 + Windows friendly)
# # ─────────────────────────────────────────────────────────────────────────────

# # EasyOCR language code map
# EASYOCR_LANG_MAP = {
#     "en":   ["en"],
#     "hi":   ["hi", "en"],   # Hindi + English fallback
#     "mr":   ["hi", "en"],   # Marathi uses Devanagari
#     "gu":   ["gu", "en"],   # Gujarati
#     "ta":   ["ta", "en"],   # Tamil
#     "te":   ["te", "en"],   # Telugu
#     "auto": ["en", "hi"],   # Detect both common scripts
# }


# class EasyOCRAdapter(BaseOCRAdapter):
#     """
#     EasyOCR adapter — works perfectly on Python 3.11 + Windows.
#     Free, open-source, no version conflicts, multilingual.
#     Install: pip install easyocr
#     Models (~100MB) auto-downloaded on first use.
#     """

#     def __init__(self, use_gpu: bool = False):
#         self.use_gpu = use_gpu
#         self._readers: dict = {}

#     def _get_reader(self, language: str):
#         langs = EASYOCR_LANG_MAP.get(language, ["en"])
#         key = "_".join(langs)
#         if key not in self._readers:
#             try:
#                 import easyocr
#                 logger.info("Initializing EasyOCR for langs=%s", langs)
#                 self._readers[key] = easyocr.Reader(
#                     langs,
#                     gpu=self.use_gpu,
#                     verbose=False,
#                 )
#                 logger.info("EasyOCR initialized successfully.")
#             except ImportError:
#                 raise RuntimeError(
#                     "EasyOCR not installed. Run: pip install easyocr"
#                 )
#         return self._readers[key]

#     def extract_text(
#         self, image: np.ndarray, language: str = "en"
#     ) -> Tuple[List[str], float]:
#         reader = self._get_reader(language)

#         # EasyOCR accepts numpy arrays directly
#         results = reader.readtext(image, detail=1, paragraph=False)

#         if not results:
#             return [], 0.0

#         lines = []
#         confidences = []
#         for (bbox, text, conf) in results:
#             text = text.strip()
#             if text:
#                 lines.append(text)
#                 confidences.append(float(conf))

#         avg_conf = float(np.mean(confidences)) if confidences else 0.0
#         logger.info("EasyOCR extracted %d text regions, avg_conf=%.3f", len(lines), avg_conf)
#         return lines, avg_conf

#     @property
#     def name(self) -> str:
#         return "EasyOCR"


# # ─────────────────────────────────────────────────────────────────────────────
# # PaddleOCR Adapter (secondary — kept for reference / Linux servers)
# # ─────────────────────────────────────────────────────────────────────────────

# PADDLE_LANG_MAP = {
#     "en":   "en",
#     "hi":   "hindi",
#     "mr":   "hindi",
#     "gu":   "en",
#     "ta":   "ta",
#     "te":   "te",
#     "auto": "en",
# }


# class PaddleOCRAdapter(BaseOCRAdapter):
#     """
#     PaddleOCR adapter.
#     NOTE: On Windows/Python 3.11 use EasyOCR instead — fewer version conflicts.
#     Compatible pairs:
#       paddlepaddle==2.6.2 + paddleocr==2.7.3  (Python ≤3.10)
#       paddlepaddle==3.0.0 + paddleocr==2.9.1  (Python 3.11+, Linux)
#     """

#     def __init__(self, use_gpu: bool = False):
#         self.use_gpu = use_gpu
#         self._engines: dict = {}

#     # def _get_engine(self, lang: str):
#     #     paddle_lang = PADDLE_LANG_MAP.get(lang, "en")
#     #     if paddle_lang not in self._engines:
#     #         try:
#     #             from paddleocr import PaddleOCR
#     #             logger.info("Initializing PaddleOCR for lang=%s", paddle_lang)

#     #             base_kwargs = dict(
#     #                 use_angle_cls=True,
#     #                 lang=paddle_lang,
#     #                 # show_log=False,
#     #             )
#     #             engine = None
#     #             # Try each API variant in order (newest first)
#     #             for extra in [
#     #                 {"device": "gpu" if self.use_gpu else "cpu"},   # >= 2.8
#     #                 {"use_gpu": self.use_gpu},                       # < 2.7
#     #                 {},                                              # plain fallback
#     #             ]:
#     #                 try:
#     #                     engine = PaddleOCR(**base_kwargs, **extra)
#     #                     logger.info("PaddleOCR init OK with extra=%s", list(extra.keys()))
#     #                     break
#     #                 except (TypeError, AttributeError) as e:
#     #                     logger.debug("PaddleOCR attempt failed: %s", e)

#     #             if engine is None:
#     #                 raise RuntimeError(
#     #                     "PaddleOCR version conflict detected.\n"
#     #                     "Fix: pip install paddlepaddle==2.6.2 paddleocr==2.7.3\n"
#     #                     "  OR switch OCR_PROVIDER=easyocr in your .env"
#     #                 )
#     #             self._engines[paddle_lang] = engine

#     #         except ImportError:
#     #             raise RuntimeError(
#     #                 "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle"
#     #             )
#     #     return self._engines[paddle_lang]
    
#     def _get_engine(self, lang: str):
#         paddle_lang = PADDLE_LANG_MAP.get(lang, "en")

#         if paddle_lang not in self._engines:
#             try:
#                 from paddleocr import PaddleOCR

#                 logger.info("Initializing PaddleOCR for lang=%s", paddle_lang)

#                 base_kwargs = {
#                     "use_angle_cls": True,
#                     "lang": paddle_lang,
#                 }

#                 engine = None

#                 # 🔥 TRY NEW API FIRST (PaddleOCR 2.8+ / 3.x)
#                 try:
#                     engine = PaddleOCR(
#                         **base_kwargs,
#                         device="gpu" if self.use_gpu else "cpu"
#                     )
#                     logger.info("PaddleOCR init OK (device API)")
#                 except TypeError as e1:
#                     logger.debug("New API failed: %s", e1)

#                     # 🔥 TRY OLD API (2.6–2.7)
#                     try:
#                         engine = PaddleOCR(
#                             **base_kwargs,
#                             use_gpu=self.use_gpu
#                         )
#                         logger.info("PaddleOCR init OK (use_gpu API)")
#                     except TypeError as e2:
#                         logger.debug("Old API failed: %s", e2)

#                         # 🔥 LAST RESORT (CPU safe mode)
#                         engine = PaddleOCR(**base_kwargs)
#                         logger.info("PaddleOCR init OK (CPU fallback)")

#                 self._engines[paddle_lang] = engine

#             except ImportError:
#                 raise RuntimeError(
#                     "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle"
#                 )

#         return self._engines[paddle_lang]

#     def extract_text(
#         self, image: np.ndarray, language: str = "en"
#     ) -> Tuple[List[str], float]:
#         engine = self._get_engine(language)

#         with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
#             cv2.imwrite(tmp.name, image)
#             tmp_path = tmp.name

#         try:
#             result = engine.ocr(tmp_path, cls=True)
#         finally:
#             try:
#                 os.unlink(tmp_path)
#             except OSError:
#                 pass

#         if not result or not result[0]:
#             return [], 0.0

#         lines, confidences = [], []
#         for block in result:
#             if not block:
#                 continue
#             for line in block:
#                 text = line[1][0]
#                 conf = float(line[1][1])
#                 if text.strip():
#                     lines.append(text.strip())
#                     confidences.append(conf)

#         avg_conf = float(np.mean(confidences)) if confidences else 0.0
#         return lines, avg_conf

#     @property
#     def name(self) -> str:
#         return "PaddleOCR"


# # ─────────────────────────────────────────────────────────────────────────────
# # Google Vision Adapter
# # ─────────────────────────────────────────────────────────────────────────────

# class GoogleVisionAdapter(BaseOCRAdapter):
#     def __init__(self, credentials_path: str = ""):
#         if credentials_path:
#             os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
#         self._client = None

#     def _get_client(self):
#         if self._client is None:
#             try:
#                 from google.cloud import vision
#                 self._client = vision.ImageAnnotatorClient()
#             except ImportError:
#                 raise RuntimeError("Install: pip install google-cloud-vision")
#         return self._client

#     def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
#         from google.cloud import vision
#         client = self._get_client()
#         _, buffer = cv2.imencode(".png", image)
#         gv_image = vision.Image(content=buffer.tobytes())
#         response = client.text_detection(image=gv_image)
#         if response.error.message:
#             raise RuntimeError(f"Google Vision error: {response.error.message}")
#         texts = response.text_annotations
#         if not texts:
#             return [], 0.0
#         lines = [l.strip() for l in texts[0].description.split("\n") if l.strip()]
#         return lines, 0.90

#     @property
#     def name(self) -> str:
#         return "GoogleVision"


# # ─────────────────────────────────────────────────────────────────────────────
# # Azure Form Recognizer Adapter
# # ─────────────────────────────────────────────────────────────────────────────

# class AzureFormRecognizerAdapter(BaseOCRAdapter):
#     def __init__(self, endpoint: str, key: str):
#         self.endpoint = endpoint
#         self.key = key
#         self._client = None

#     def _get_client(self):
#         if self._client is None:
#             try:
#                 from azure.ai.formrecognizer import DocumentAnalysisClient
#                 from azure.core.credentials import AzureKeyCredential
#                 self._client = DocumentAnalysisClient(
#                     endpoint=self.endpoint,
#                     credential=AzureKeyCredential(self.key),
#                 )
#             except ImportError:
#                 raise RuntimeError("Install: pip install azure-ai-formrecognizer")
#         return self._client

#     def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
#         client = self._get_client()
#         _, buffer = cv2.imencode(".png", image)
#         poller = client.begin_analyze_document("prebuilt-read", buffer.tobytes())
#         result = poller.result()
#         lines, confidences = [], []
#         for page in result.pages:
#             for line in page.lines:
#                 lines.append(line.content)
#                 if hasattr(line, "confidence") and line.confidence:
#                     confidences.append(line.confidence)
#         return lines, float(np.mean(confidences)) if confidences else 0.85

#     @property
#     def name(self) -> str:
#         return "AzureFormRecognizer"


# # ─────────────────────────────────────────────────────────────────────────────
# # AWS Textract Adapter
# # ─────────────────────────────────────────────────────────────────────────────

# class AWSTextractAdapter(BaseOCRAdapter):
#     def __init__(self, region: str = "us-east-1"):
#         self.region = region
#         self._client = None

#     def _get_client(self):
#         if self._client is None:
#             try:
#                 import boto3
#                 self._client = boto3.client("textract", region_name=self.region)
#             except ImportError:
#                 raise RuntimeError("Install: pip install boto3")
#         return self._client

#     def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
#         client = self._get_client()
#         _, buffer = cv2.imencode(".png", image)
#         response = client.detect_document_text(Document={"Bytes": buffer.tobytes()})
#         lines, confidences = [], []
#         for block in response.get("Blocks", []):
#             if block["BlockType"] == "LINE":
#                 lines.append(block["Text"])
#                 confidences.append(block.get("Confidence", 90.0) / 100.0)
#         return lines, float(np.mean(confidences)) if confidences else 0.85

#     @property
#     def name(self) -> str:
#         return "AWSTextract"


# # ─────────────────────────────────────────────────────────────────────────────
# # Factory
# # ─────────────────────────────────────────────────────────────────────────────

# def create_ocr_engine(provider: str = "easyocr", **kwargs) -> BaseOCRAdapter:
#     adapters = {
#         "easyocr":   lambda: EasyOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
#         "paddleocr": lambda: PaddleOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
#         "google":    lambda: GoogleVisionAdapter(kwargs.get("credentials_path", "")),
#         "azure":     lambda: AzureFormRecognizerAdapter(
#                          kwargs.get("endpoint", ""), kwargs.get("key", "")),
#         "aws":       lambda: AWSTextractAdapter(kwargs.get("region", "us-east-1")),
#     }
#     factory = adapters.get(provider.lower())
#     if not factory:
#         raise ValueError(
#             f"Unknown OCR provider: '{provider}'. Choose from: {list(adapters.keys())}"
#         )
#     return factory()


# _ocr_engine: Optional[BaseOCRAdapter] = None


# def get_ocr_engine() -> BaseOCRAdapter:
#     global _ocr_engine
#     if _ocr_engine is None:
#         from core.config import settings
#         _ocr_engine = create_ocr_engine(
#             provider=settings.OCR_PROVIDER,
#             use_gpu=settings.PADDLE_USE_GPU,
#             credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS,
#             endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
#             key=settings.AZURE_FORM_RECOGNIZER_KEY,
#             region=settings.AWS_REGION,
#         )
#         logger.info("OCR engine initialized: %s", _ocr_engine.name)
#     return _ocr_engine


# """
# OCR Abstraction Layer
# Primary: EasyOCR (stable on Python 3.11, Windows, no version conflicts)
# Secondary: PaddleOCR (with version-safe init)
# Also: Google Vision, Azure Form Recognizer, AWS Textract
# """
# import logging
# import os
# import tempfile
# from abc import ABC, abstractmethod
# from typing import List, Optional, Tuple

# import cv2
# import numpy as np

# logger = logging.getLogger(__name__)


# # ─────────────────────────────────────────────────────────────────────────────
# # Robust Language Normalization Layer
# # ─────────────────────────────────────────────────────────────────────────────

# # Maps common variations to standardized 2-letter ISO codes
# LANG_NORM_MAP = {
#     # English
#     "en": "en", "eng": "en", "english": "en",
#     # Hindi
#     "hi": "hi", "hin": "hi", "hindi": "hi",
#     # Marathi
#     "mr": "mr", "mar": "mr", "marathi": "mr",
#     # Gujarati
#     "gu": "gu", "guj": "gu", "gujarati": "gu",
#     # Tamil
#     "ta": "ta", "tam": "ta", "tamil": "ta",
#     # Telugu
#     "te": "te", "tel": "te", "telugu": "te",
#     # Auto
#     "auto": "auto", "detect": "auto"
# }


# def normalize_language_code(language: str) -> str:
#     """Normalizes mixed-case, whitespace-padded, or full-name language codes."""
#     if not language:
#         return "en"
#     clean_lang = str(language).strip().lower()
#     return LANG_NORM_MAP.get(clean_lang, "en")


# # ─────────────────────────────────────────────────────────────────────────────
# # Base Interface
# # ─────────────────────────────────────────────────────────────────────────────

# class BaseOCRAdapter(ABC):
#     """Abstract OCR adapter — swap providers without changing business logic."""

#     @abstractmethod
#     def extract_text(
#         self, image: np.ndarray, language: str = "en"
#     ) -> Tuple[List[str], float]:
#         """Returns (list_of_text_lines, avg_confidence_0_to_1)."""
#         ...

#     @property
#     @abstractmethod
#     def name(self) -> str: ...


# # ─────────────────────────────────────────────────────────────────────────────
# # EasyOCR Adapter  
# # ─────────────────────────────────────────────────────────────────────────────

# EASYOCR_LANG_MAP = {
#     "en":   ["en"],
#     "hi":   ["hi", "en"],   # Hindi + English fallback
#     "mr":   ["mr", "en"],   # EasyOCR natively supports "mr"
#     "gu":   ["gu", "en"],   # Gujarati
#     "ta":   ["ta", "en"],   # Tamil
#     "te":   ["te", "en"],   # Telugu
#     "auto": ["en", "hi"],   # Detect both common scripts
# }


# class EasyOCRAdapter(BaseOCRAdapter):
#     """
#     EasyOCR adapter — compatible with Python 3.11 + Windows.
#     Free, open-source, no version conflicts, multilingual.
#     Install: pip install easyocr
#     Models (~100MB) auto-downloaded on first use.
#     """

#     def __init__(self, use_gpu: bool = False):
#         self.use_gpu = use_gpu
#         self._readers: dict = {}

#     def _get_reader(self, language: str):
#         norm_lang = normalize_language_code(language)
#         langs = EASYOCR_LANG_MAP.get(norm_lang, ["en"])
#         key = "_".join(langs)
        
#         if key not in self._readers:
#             try:
#                 import easyocr
#                 logger.info("Initializing EasyOCR for langs=%s (requested: %s)", langs, language)
#                 self._readers[key] = easyocr.Reader(
#                     langs,
#                     gpu=self.use_gpu,
#                     verbose=False,
#                 )
#                 logger.info("EasyOCR initialized successfully for %s.", key)
#             except ImportError:
#                 raise RuntimeError(
#                     "EasyOCR not installed. Run: pip install easyocr"
#                 )
#         return self._readers[key]

#     def extract_text(
#         self, image: np.ndarray, language: str = "en"
#     ) -> Tuple[List[str], float]:
#         # Defensive check for image array layout/type
#         if not isinstance(image, np.ndarray):
#             raise ValueError("Input image must be a numpy array")
#         if image.dtype != np.uint8:
#             image = image.astype(np.uint8)
#         image = np.ascontiguousarray(image)

#         reader = self._get_reader(language)

#         # EasyOCR accepts numpy arrays directly
#         results = reader.readtext(image, detail=1, paragraph=False)

#         if not results:
#             return [], 0.0

#         lines = []
#         confidences = []
#         for (bbox, text, conf) in results:
#             text = text.strip()
#             if text:
#                 lines.append(text)
#                 confidences.append(float(conf))

#         avg_conf = float(np.mean(confidences)) if confidences else 0.0
#         logger.info("EasyOCR extracted %d regions, language=%s, avg_conf=%.3f", len(lines), language, avg_conf)
#         return lines, avg_conf

#     @property
#     def name(self) -> str:
#         return "EasyOCR"


# # ─────────────────────────────────────────────────────────────────────────────
# # PaddleOCR Adapter 
# # ─────────────────────────────────────────────────────────────────────────────

# PADDLE_LANG_MAP = {
#     "en":   "en",
#     "hi":   "devanagari",
#     "mr":   "devanagari",
#     "gu":   "en",
#     "ta":   "ta",
#     "te":   "te",
#     "auto": "en",
# }


# class PaddleOCRAdapter(BaseOCRAdapter):
#     """
#     PaddleOCR adapter.
#     NOTE: On Windows/Python 3.11 use EasyOCR instead — fewer version conflicts.
#     Compatible pairs:
#       paddlepaddle==2.6.2 + paddleocr==2.7.3  (Python ≤3.10)
#       paddlepaddle==3.0.0 + paddleocr==2.9.1  (Python 3.11+, Linux)
#     """

#     def __init__(self, use_gpu: bool = False):
#         self.use_gpu = use_gpu
#         self._engines: dict = {}
    
#     def _get_engine(self, lang: str):
#         norm_lang = normalize_language_code(lang)
#         paddle_lang = PADDLE_LANG_MAP.get(norm_lang, "en")

#         if paddle_lang not in self._engines:
#             try:
#                 from paddleocr import PaddleOCR

#                 logger.info("Initializing PaddleOCR for lang=%s (requested: %s)", paddle_lang, lang)

#                 base_kwargs = {
#                     "use_angle_cls": True,
#                     "lang": paddle_lang,
#                 }

#                 engine = None

#                 # 1. TRY STANDARD use_gpu API
#                 try:
#                     engine = PaddleOCR(
#                         **base_kwargs,
#                         use_gpu=self.use_gpu
#                     )
#                     logger.info("PaddleOCR init OK (use_gpu API)")
#                 except (TypeError, ValueError, AttributeError) as e1:
#                     logger.debug("PaddleOCR (use_gpu) init failed, trying (device) API: %s", e1)

#                     # 2. TRY DEVICE API (PaddleOCR 2.8+ / 3.x)
#                     try:
#                         engine = PaddleOCR(
#                             **base_kwargs,
#                             device="gpu" if self.use_gpu else "cpu"
#                         )
#                         logger.info("PaddleOCR init OK (device API)")
#                     except (TypeError, ValueError, AttributeError) as e2:
#                         logger.debug("PaddleOCR (device) init failed, trying fallback: %s", e2)

#                         # 3. CPU FALLBACK
#                         try:
#                             engine = PaddleOCR(**base_kwargs)
#                             logger.info("PaddleOCR init OK (CPU fallback)")
#                         except Exception as e3:
#                             raise RuntimeError(
#                                 f"Failed to initialize PaddleOCR: {e3}\n"
#                                 "Fix: Check your paddlepaddle and paddleocr library compatibility."
#                             )

#                 self._engines[paddle_lang] = engine

#             except ImportError:
#                 raise RuntimeError(
#                     "PaddleOCR not installed. Run: pip install paddleocr paddlepaddle"
#                 )

#         return self._engines[paddle_lang]

#     def extract_text(
#         self, image: np.ndarray, language: str = "en"
#     ) -> Tuple[List[str], float]:
#         # Defensive check for image array layout/type
#         if not isinstance(image, np.ndarray):
#             raise ValueError("Input image must be a numpy array")
#         if image.dtype != np.uint8:
#             image = image.astype(np.uint8)
#         image = np.ascontiguousarray(image)

#         engine = self._get_engine(language)

#         # Avoid expensive file I/O operations by passing the numpy array directly
#         try:
#             result = engine.ocr(image, cls=True)
#         except Exception as e:
#             logger.warning("Direct array inference failed: %s. Falling back to temporary file.", e)
            
#             # Temporary file fallback if direct numpy array inference fails
#             with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
#                 cv2.imwrite(tmp.name, image)
#                 tmp_path = tmp.name

#             try:
#                 result = engine.ocr(tmp_path, cls=True)
#             finally:
#                 try:
#                     os.unlink(tmp_path)
#                 except OSError:
#                     pass

#         if not result or not result[0]:
#             return [], 0.0

#         lines, confidences = [], []
#         for block in result:
#             if not block:
#                 continue
#             for line in block:
#                 text = line[1][0]
#                 conf = float(line[1][1])
#                 if text.strip():
#                     lines.append(text.strip())
#                     confidences.append(conf)

#         avg_conf = float(np.mean(confidences)) if confidences else 0.0
#         logger.info("PaddleOCR extracted %d regions, language=%s, avg_conf=%.3f", len(lines), language, avg_conf)
#         return lines, avg_conf

#     @property
#     def name(self) -> str:
#         return "PaddleOCR"


# # ─────────────────────────────────────────────────────────────────────────────
# # Google Vision Adapter
# # ─────────────────────────────────────────────────────────────────────────────

# class GoogleVisionAdapter(BaseOCRAdapter):
#     def __init__(self, credentials_path: str = ""):
#         if credentials_path:
#             os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
#         self._client = None

#     def _get_client(self):
#         if self._client is None:
#             try:
#                 from google.cloud import vision
#                 self._client = vision.ImageAnnotatorClient()
#             except ImportError:
#                 raise RuntimeError("Install: pip install google-cloud-vision")
#         return self._client

#     def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
#         from google.cloud import vision
#         client = self._get_client()
#         _, buffer = cv2.imencode(".png", image)
#         gv_image = vision.Image(content=buffer.tobytes())
#         response = client.text_detection(image=gv_image)
#         if response.error.message:
#             raise RuntimeError(f"Google Vision error: {response.error.message}")
#         texts = response.text_annotations
#         if not texts:
#             return [], 0.0
#         lines = [l.strip() for l in texts[0].description.split("\n") if l.strip()]
#         return lines, 0.90

#     @property
#     def name(self) -> str:
#         return "GoogleVision"


# # ─────────────────────────────────────────────────────────────────────────────
# # Azure Form Recognizer Adapter
# # ─────────────────────────────────────────────────────────────────────────────

# class AzureFormRecognizerAdapter(BaseOCRAdapter):
#     def __init__(self, endpoint: str, key: str):
#         self.endpoint = endpoint
#         self.key = key
#         self._client = None

#     def _get_client(self):
#         if self._client is None:
#             try:
#                 from azure.ai.formrecognizer import DocumentAnalysisClient
#                 from azure.core.credentials import AzureKeyCredential
#                 self._client = DocumentAnalysisClient(
#                     endpoint=self.endpoint,
#                     credential=AzureKeyCredential(self.key),
#                 )
#             except ImportError:
#                 raise RuntimeError("Install: pip install azure-ai-formrecognizer")
#         return self._client

#     def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
#         client = self._get_client()
#         _, buffer = cv2.imencode(".png", image)
#         poller = client.begin_analyze_document("prebuilt-read", buffer.tobytes())
#         result = poller.result()
#         lines, confidences = [], []
#         for page in result.pages:
#             for line in page.lines:
#                 lines.append(line.content)
#                 if hasattr(line, "confidence") and line.confidence:
#                     confidences.append(line.confidence)
#         return lines, float(np.mean(confidences)) if confidences else 0.85

#     @property
#     def name(self) -> str:
#         return "AzureFormRecognizer"


# # ─────────────────────────────────────────────────────────────────────────────
# # AWS Textract Adapter
# # ─────────────────────────────────────────────────────────────────────────────

# class AWSTextractAdapter(BaseOCRAdapter):
#     def __init__(self, region: str = "us-east-1"):
#         self.region = region
#         self._client = None

#     def _get_client(self):
#         if self._client is None:
#             try:
#                 import boto3
#                 self._client = boto3.client("textract", region_name=self.region)
#             except ImportError:
#                 raise RuntimeError("Install: pip install boto3")
#         return self._client

#     def extract_text(self, image: np.ndarray, language: str = "en") -> Tuple[List[str], float]:
#         client = self._get_client()
#         _, buffer = cv2.imencode(".png", image)
#         response = client.detect_document_text(Document={"Bytes": buffer.tobytes()})
#         lines, confidences = [], []
#         for block in response.get("Blocks", []):
#             if block["BlockType"] == "LINE":
#                 lines.append(block["Text"])
#                 confidences.append(block.get("Confidence", 90.0) / 100.0)
#         return lines, float(np.mean(confidences)) if confidences else 0.85

#     @property
#     def name(self) -> str:
#         return "AWSTextract"


# # ─────────────────────────────────────────────────────────────────────────────
# # Factory
# # ─────────────────────────────────────────────────────────────────────────────

# def create_ocr_engine(provider: str = "easyocr", **kwargs) -> BaseOCRAdapter:
#     adapters = {
#         "easyocr":   lambda: EasyOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
#         "paddleocr": lambda: PaddleOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
#         "google":    lambda: GoogleVisionAdapter(kwargs.get("credentials_path", "")),
#         "azure":     lambda: AzureFormRecognizerAdapter(
#                          kwargs.get("endpoint", ""), kwargs.get("key", "")),
#         "aws":       lambda: AWSTextractAdapter(kwargs.get("region", "us-east-1")),
#     }
#     factory = adapters.get(provider.lower())
#     if not factory:
#         raise ValueError(
#             f"Unknown OCR provider: '{provider}'. Choose from: {list(adapters.keys())}"
#         )
#     return factory()


# _ocr_engine: Optional[BaseOCRAdapter] = None


# def get_ocr_engine() -> BaseOCRAdapter:
#     global _ocr_engine
#     if _ocr_engine is None:
#         from core.config import settings
#         _ocr_engine = create_ocr_engine(
#             provider=settings.OCR_PROVIDER,
#             use_gpu=settings.PADDLE_USE_GPU,
#             credentials_path=settings.GOOGLE_APPLICATION_CREDENTIALS,
#             endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
#             key=settings.AZURE_FORM_RECOGNIZER_KEY,
#             region=settings.AWS_REGION,
#         )
#         logger.info("OCR engine initialized: %s", _ocr_engine.name)
#     return _ocr_engine














































































































"""
OCR Abstraction Layer
Primary: EasyOCR (stable on Python 3.11, Windows, no version conflicts)
Secondary: PaddleOCR (with version-safe init)
Also: Google Vision, Azure Form Recognizer, AWS Textract
"""
import logging
import os
import tempfile
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Robust Language Normalization Layer
# ─────────────────────────────────────────────────────────────────────────────

# Maps common variations to standardized 2-letter ISO codes
LANG_NORM_MAP = {
    # English
    "en": "en", "eng": "en", "english": "en",
    # Hindi
    "hi": "hi", "hin": "hi", "hindi": "hi",
    # Marathi
    "mr": "mr", "mar": "mr", "marathi": "mr",
    # Gujarati
    "gu": "gu", "guj": "gu", "gujarati": "gu",
    # Tamil
    "ta": "ta", "tam": "ta", "tamil": "ta",
    # Telugu
    "te": "te", "tel": "te", "telugu": "te",
    # Auto
    "auto": "auto", "detect": "auto"
}


def normalize_language_code(language: str) -> str:
    """Normalizes mixed-case, whitespace-padded, or full-name language codes."""
    if not language:
        return "en"
    clean_lang = str(language).strip().lower()
    return LANG_NORM_MAP.get(clean_lang, "en")


# ─────────────────────────────────────────────────────────────────────────────
# Base Interface
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# EasyOCR Adapter  
# ─────────────────────────────────────────────────────────────────────────────

EASYOCR_LANG_MAP = {
    "en":   ["en"],
    "hi":   ["hi", "en"],   # Hindi + English fallback (supports multilingual)
    "mr":   ["mr", "en"],   # Marathi + English fallback
    "gu":   ["gu", "en"],   # Gujarati + English fallback
    "ta":   ["ta", "en"],   # Tamil + English fallback
    "te":   ["te", "en"],   # Telugu + English fallback
    "auto": ["en", "hi"],   # Detect both common scripts
}


class EasyOCRAdapter(BaseOCRAdapter):
    """
    EasyOCR adapter — compatible with Python 3.11 + Windows.
    Free, open-source, no version conflicts, multilingual.
    Install: pip install easyocr
    Models (~100MB) auto-downloaded on first use.
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
                logger.info("EasyOCR initialized successfully for %s.", key)
            except ImportError:
                raise RuntimeError(
                    "EasyOCR not installed. Run: pip install easyocr"
                )
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

        # EasyOCR accepts numpy arrays directly
        results = reader.readtext(image, detail=1, paragraph=False)

        if not results:
            return [], 0.0

        lines = []
        confidences = []
        for (bbox, text, conf) in results:
            text = text.strip()
            if text:
                lines.append(text)
                confidences.append(float(conf))

        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        logger.info("EasyOCR extracted %d regions, language=%s, avg_conf=%.3f", len(lines), language, avg_conf)
        return lines, avg_conf

    @property
    def name(self) -> str:
        return "EasyOCR"


# ─────────────────────────────────────────────────────────────────────────────
# PaddleOCR Adapter 
# ─────────────────────────────────────────────────────────────────────────────

PADDLE_LANG_MAP = {
    "en":   "en",
    "hi":   "devanagari",
    "mr":   "devanagari",
    "gu":   "en",
    "ta":   "ta",
    "te":   "te",
    "auto": "en",
}


class PaddleOCRAdapter(BaseOCRAdapter):
    """
    PaddleOCR adapter.
    NOTE: On Windows/Python 3.11 use EasyOCR instead — fewer version conflicts.
    Compatible pairs:
      paddlepaddle==2.6.2 + paddleocr==2.7.3  (Python ≤3.10)
      paddlepaddle==3.0.0 + paddleocr==2.9.1  (Python 3.11+, Linux)
    """

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._engines: dict = {}
    
    def _get_engine(self, lang: str):
        norm_lang = normalize_language_code(lang)
        paddle_lang = PADDLE_LANG_MAP.get(norm_lang, "en")

        if paddle_lang not in self._engines:
            try:
                from paddleocr import PaddleOCR

                logger.info("Initializing PaddleOCR for lang=%s (requested: %s)", paddle_lang, lang)

                base_kwargs = {
                    "use_angle_cls": True,
                    "lang": paddle_lang,
                }

                engine = None

                # 1. TRY STANDARD use_gpu API
                try:
                    engine = PaddleOCR(
                        **base_kwargs,
                        use_gpu=self.use_gpu
                    )
                    logger.info("PaddleOCR init OK (use_gpu API)")
                except (TypeError, ValueError, AttributeError) as e1:
                    logger.debug("PaddleOCR (use_gpu) init failed, trying (device) API: %s", e1)

                    # 2. TRY DEVICE API (PaddleOCR 2.8+ / 3.x)
                    try:
                        engine = PaddleOCR(
                            **base_kwargs,
                            device="gpu" if self.use_gpu else "cpu"
                        )
                        logger.info("PaddleOCR init OK (device API)")
                    except (TypeError, ValueError, AttributeError) as e2:
                        logger.debug("PaddleOCR (device) init failed, trying fallback: %s", e2)

                        # 3. CPU FALLBACK
                        try:
                            engine = PaddleOCR(**base_kwargs)
                            logger.info("PaddleOCR init OK (CPU fallback)")
                        except Exception as e3:
                            raise RuntimeError(
                                f"Failed to initialize PaddleOCR: {e3}\n"
                                "Fix: Check your paddlepaddle and paddleocr library compatibility."
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
            logger.warning("Direct array inference failed: %s. Falling back to temporary file.", e)
            
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
        logger.info("PaddleOCR extracted %d regions, language=%s, avg_conf=%.3f", len(lines), language, avg_conf)
        return lines, avg_conf

    @property
    def name(self) -> str:
        return "PaddleOCR"


# ─────────────────────────────────────────────────────────────────────────────
# Cloud Adapters (kept for fallback / compliance)
# ─────────────────────────────────────────────────────────────────────────────

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
        lines = [l.strip() for l in texts[0].description.split("\n") if l.strip()]
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


# ─────────────────────────────────────────────────────────────────────────────
# PDF Rendering Engines
# ─────────────────────────────────────────────────────────────────────────────

def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[np.ndarray]:
    """Converts PDF pages into numpy arrays (BGR format) using PyMuPDF."""
    images = []
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            raise RuntimeError(
                "Please install PyMuPDF to handle PDF files: pip install pymupdf"
            )

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        # DPI translation mapping (72 is the default PDF document layout resolution)
        zoom = dpi / 72
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Parse pixel buffer to RGB shape
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        # Convert RGB to OpenCV BGR color space
        img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
        images.append(img_bgr)
        
    doc.close()
    return images


def convert_pdf_to_images_fallback(pdf_bytes: bytes) -> List[np.ndarray]:
    """Alternative PDF converter using pdf2image if PyMuPDF is not configured."""
    try:
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(pdf_bytes, dpi=200)
        images = []
        for page in pages:
            img_bgr = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            images.append(img_bgr)
        return images
    except ImportError:
        raise RuntimeError("Neither PyMuPDF nor pdf2image are available.")


# ─────────────────────────────────────────────────────────────────────────────
# Factory & Driver Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def create_ocr_engine(provider: str = "easyocr", **kwargs) -> BaseOCRAdapter:
    adapters = {
        "easyocr":   lambda: EasyOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
        "paddleocr": lambda: PaddleOCRAdapter(use_gpu=kwargs.get("use_gpu", False)),
        "google":    lambda: GoogleVisionAdapter(kwargs.get("credentials_path", "")),
        "azure":     lambda: AzureFormRecognizerAdapter(
                         kwargs.get("endpoint", ""), kwargs.get("key", "")),
        "aws":       lambda: AWSTextractAdapter(kwargs.get("region", "us-east-1")),
    }
    factory = adapters.get(provider.lower())
    if not factory:
        raise ValueError(
            f"Unknown OCR provider: '{provider}'. Choose from: {list(adapters.keys())}"
        )
    return factory()


_ocr_engine: Optional[BaseOCRAdapter] = None


def get_ocr_engine() -> BaseOCRAdapter:
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


# ─────────────────────────────────────────────────────────────────────────────
# Unified End-to-End Processing Driver
# ─────────────────────────────────────────────────────────────────────────────

def ocr_file_bytes(
    file_bytes: bytes, 
    provider: str = "easyocr", 
    language: str = "en", 
    **kwargs
) -> Tuple[List[str], float]:
    """
    Identifies the document type (Image vs. PDF), parses PDF pages, 
    and returns combined text lines and aggregated confidence scores.
    """
    if not file_bytes:
        return [], 0.0

    # Read PDF Magic Header Byte (%PDF)
    is_pdf = file_bytes.startswith(b"%PDF")
    images = []

    if is_pdf:
        logger.info("Rendering PDF pages for OCR extraction...")
        try:
            images = convert_pdf_to_images(file_bytes)
        except Exception as e:
            logger.warning("Primary PyMuPDF processor failed: %s. Loading fallback.", e)
            try:
                images = convert_pdf_to_images_fallback(file_bytes)
            except Exception as e_fb:
                logger.error("All PDF preprocessing modules failed: %s", e_fb)
                raise RuntimeError(
                    "PDF decoding failed. Ensure 'pymupdf' is installed via pip."
                )
    else:
        # Standard OpenCV image decoding pipeline
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(
                "Preprocessing failed: Cannot decode image. File may be corrupted or unsupported."
            )
        images = [image]

    # Initialize requested OCR pipeline
    engine = create_ocr_engine(provider, **kwargs)
    
    all_lines = []
    all_confidences = []
    
    for idx, img in enumerate(images):
        logger.info("Executing OCR page (%d/%d) using backend: %s", idx + 1, len(images), engine.name)
        lines, conf = engine.extract_text(img, language=language)
        all_lines.extend(lines)
        if conf > 0:
            all_confidences.append(conf)

    avg_conf = float(np.mean(all_confidences)) if all_confidences else 0.0
    return all_lines, avg_conf