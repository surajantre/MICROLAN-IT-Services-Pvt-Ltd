


"""
OpenCV Image Preprocessing Pipeline
Steps: Validate -> Denoise -> Enhance -> Binarize -> Deskew -> Segment

Two pipeline variants:
  process()            - full pipeline including binarization (best for Latin/English)
  process_for_indic()  - stops before binarization (preserves Indic glyph strokes)
"""
# from curses import meta
import logging
import math
from typing import Tuple
from matplotlib.pyplot import gray
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Full OpenCV preprocessing pipeline for handwritten invoice images."""

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    MIN_DIM = 100
    MAX_DIM = 10000

    def process(self, image_bytes: bytes) -> Tuple[np.ndarray, dict]:
        """
        Full pipeline: validate -> denoise -> enhance -> binarize -> deskew.
        Best for Latin/English text.
        Returns (processed_image_ndarray, metadata_dict).
        """
        meta = {"steps": [], "warnings": []}

        image = self._decode(image_bytes, meta)
        self._validate(image, meta)
        gray = self._to_gray(image, meta)
        denoised = self._denoise(gray, meta)
        enhanced = self._enhance_contrast(denoised, meta)
        binary = self._binarize(enhanced, meta)
        deskewed = self._deskew(binary, meta)

        meta["output_shape"] = deskewed.shape
        logger.info("Preprocessing complete (full). Steps: %s", meta["steps"])
        return deskewed, meta

    def process_for_indic(self, image_bytes: bytes) -> Tuple[np.ndarray, dict]:
        """
        Lite pipeline for Indic scripts: validate -> denoise -> enhance -> deskew.
        Skips binarization — adaptive threshold destroys curved Devanagari/Tamil strokes
        and causes EasyOCR/PaddleOCR to miss characters. Grayscale + CLAHE is sufficient.
        Returns (processed_image_ndarray, metadata_dict).
        """
        meta = {"steps": [], "warnings": []}

        image = self._decode(image_bytes, meta)
        self._validate(image, meta)
        gray = self._to_gray(image, meta)
        denoised = self._denoise(gray, meta)
        enhanced = self._enhance_contrast(denoised, meta)
        deskewed = self._deskew(enhanced, meta)

        meta["output_shape"] = deskewed.shape
        logger.info("Preprocessing complete (indic-safe). Steps: %s", meta["steps"])
        return deskewed, meta

    # ------------------------------------------------------------------ #
    # Step 1: Decode bytes -> ndarray
    # ------------------------------------------------------------------ #
    def _decode(self, image_bytes: bytes, meta: dict) -> np.ndarray:
        arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Cannot decode image. File may be corrupted or unsupported.")
        meta["steps"].append("decode")
        meta["input_shape"] = image.shape
        return image

    # ------------------------------------------------------------------ #
    # Step 2: Validate
    # ------------------------------------------------------------------ #
    def _validate(self, image: np.ndarray, meta: dict):
        h, w = image.shape[:2]
        if h < self.MIN_DIM or w < self.MIN_DIM:
            raise ValueError(f"Image too small: {w}x{h}. Minimum: {self.MIN_DIM}px.")
        if h > self.MAX_DIM or w > self.MAX_DIM:
            meta["warnings"].append(f"Large image ({w}x{h}), may slow processing.")
        meta["steps"].append("validate")

    # ------------------------------------------------------------------ #
    # Step 3: Grayscale
    # ------------------------------------------------------------------ #
    def _to_gray(self, image: np.ndarray, meta: dict) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        meta["steps"].append("grayscale")
        return gray

    # ------------------------------------------------------------------ #
    # Step 4: Noise Removal - Gaussian + Median
    # ------------------------------------------------------------------ #
    # def _denoise(self, gray: np.ndarray, meta: dict) -> np.ndarray:
    #     gaussian = cv2.GaussianBlur(gray, (3, 3), 0)
    #     median = cv2.medianBlur(gaussian, 3)
    #     meta["steps"].append("denoise(gaussian+median)")
    #     return median
    def _denoise(self, gray, meta):

        denoised = cv2.bilateralFilter(
            gray,
            9,
            75,
            75
        )

        meta["steps"].append("bilateral")
        return denoised

    # ------------------------------------------------------------------ #
    # Step 5: Contrast Enhancement - CLAHE
    # ------------------------------------------------------------------ #
    def _enhance_contrast(self, gray: np.ndarray, meta: dict) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        meta["steps"].append("contrast(CLAHE)")
        return enhanced

    # ------------------------------------------------------------------ #
    # Step 6: Binarization - Adaptive + OTSU fallback
    # ------------------------------------------------------------------ #
    # def _binarize(self, gray: np.ndarray, meta: dict) -> np.ndarray:
    #     adaptive = cv2.adaptiveThreshold(
    #         gray, 255,
    #         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    #         cv2.THRESH_BINARY,
    #         blockSize=15, C=8
    #     )
    #     _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    #     adaptive_noise = self._estimate_noise(adaptive)
    #     otsu_noise = self._estimate_noise(otsu)

    #     result = adaptive if adaptive_noise <= otsu_noise else otsu
    #     method = "adaptive" if adaptive_noise <= otsu_noise else "otsu"
    #     meta["steps"].append(f"binarize({method})")
    #     return result
    def _binarize(self, gray, meta):

        _, thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        kernel = np.ones((2,2), np.uint8)

        thresh = cv2.morphologyEx(
            thresh,
            cv2.MORPH_CLOSE,
            kernel
        )

        meta["steps"].append("otsu+morph")

        return thresh

    def _estimate_noise(self, binary: np.ndarray) -> float:
        """Estimate noise as ratio of isolated white pixels."""
        kernel = np.ones((3, 3), np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        diff = cv2.absdiff(binary, opened)
        return float(np.sum(diff)) / (binary.shape[0] * binary.shape[1])

    # ------------------------------------------------------------------ #
    # Step 7: Skew Detection & Deskew
    # ------------------------------------------------------------------ #
    def _deskew(self, binary: np.ndarray, meta: dict) -> np.ndarray:
        angle = self._detect_skew(binary)
        meta["skew_angle"] = round(angle, 2)
        if abs(angle) < 0.5:
            meta["steps"].append("deskew(skipped, angle<0.5deg)")
            return binary
        rotated = self._rotate(binary, angle)
        meta["steps"].append(f"deskew(rotated {angle:.1f}deg)")
        return rotated

    def _detect_skew(self, binary: np.ndarray) -> float:
        """Detect skew using Hough Line Transform."""
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        if lines is None:
            return 0.0
        angles = []
        for line in lines[:20]:
            rho, theta = line[0]
            angle_deg = math.degrees(theta) - 90
            if abs(angle_deg) < 45:
                angles.append(angle_deg)
        return float(np.median(angles)) if angles else 0.0

    def _rotate(self, image: np.ndarray, angle: float) -> np.ndarray:
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated

    def image_to_bytes(self, image: np.ndarray, ext: str = ".png") -> bytes:
        """Convert ndarray back to bytes for OCR engine."""
        success, buffer = cv2.imencode(ext, image)
        if not success:
            raise ValueError("Failed to encode processed image.")
        return buffer.tobytes()