"""
qr_tool.py
──────────
Decode QR codes from image files using pyzbar + OpenCV.

3-attempt strategy:
  1. Raw image
  2. Preprocessed (grayscale + threshold)
  3. Upscaled (for small/thumbnail images)

Install:
  pip install pyzbar opencv-python Pillow
  Windows: also download libzbar-64.dll → place in project root
"""

import logging
import re
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode as pyzbar_decode, ZBarSymbol

from app.models.schemas import QRDecodeResult

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


# ── Public API ─────────────────────────────────────────────────────────────

def decode_qr_from_file(image_path: str) -> QRDecodeResult:
    """Decode a QR code from an image file. Returns QRDecodeResult."""
    path = Path(image_path)
    if not path.exists():
        return QRDecodeResult(success=False, error=f"File not found: {image_path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return QRDecodeResult(success=False, error=f"Unsupported format: {path.suffix}")

    img = _load_image(image_path)
    if img is None:
        return QRDecodeResult(success=False, error="Could not load image")

    # Attempt 1: raw
    raw = _try_decode(img)
    if raw:
        return _build_result(raw)

    # Attempt 2: preprocessed
    raw = _try_decode(_preprocess(img))
    if raw:
        logger.info("QR found after preprocessing")
        return _build_result(raw)

    # Attempt 3: upscaled (for small thumbnails)
    if img.shape[0] < 300 or img.shape[1] < 300:
        raw = _try_decode(_upscale(img))
        if raw:
            logger.info("QR found after upscaling")
            return _build_result(raw)

    return QRDecodeResult(success=False, error="No QR code found in image")


def decode_qr_from_bytes(image_bytes: bytes) -> QRDecodeResult:
    """Decode a QR code from raw bytes (e.g. direct from email attachment)."""
    try:
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return QRDecodeResult(success=False, error="Could not decode image bytes")

        raw = _try_decode(img) or _try_decode(_preprocess(img))
        if raw:
            return _build_result(raw)

        return QRDecodeResult(success=False, error="No QR code found in image bytes")
    except Exception as e:
        return QRDecodeResult(success=False, error=str(e))


# ── Internals ──────────────────────────────────────────────────────────────

def _load_image(image_path: str) -> Optional[np.ndarray]:
    try:
        pil = Image.open(image_path).convert("RGB")
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        return None


def _try_decode(img: np.ndarray) -> Optional[str]:
    try:
        codes = pyzbar_decode(img, symbols=[ZBarSymbol.QRCODE])
        if codes:
            return codes[0].data.decode("utf-8", errors="replace").strip()

        # Fallback to OpenCV built-in
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data:
            return data.strip()
    except Exception:
        pass
    return None


def _preprocess(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11, C=2,
    )
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(thresh, -1, kernel)


def _upscale(img: np.ndarray, scale: float = 3.0) -> np.ndarray:
    h, w = img.shape[:2]
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)


def _extract_url(raw: str) -> Optional[str]:
    if URL_PATTERN.match(raw):
        return raw
    match = URL_PATTERN.search(raw)
    return match.group(0) if match else None


def _build_result(raw: str) -> QRDecodeResult:
    url = _extract_url(raw)
    return QRDecodeResult(url=url, raw_data=raw, source="qr_code", success=True)


# ── Manual test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python -m app.tools.qr_tool <image_path>")
        sys.exit(1)
    r = decode_qr_from_file(sys.argv[1])
    print(f"Success : {r.success}")
    print(f"URL     : {r.url}")
    print(f"Raw data: {r.raw_data}")
    if r.error:
        print(f"Error   : {r.error}")