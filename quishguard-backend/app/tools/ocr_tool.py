"""
ocr_tool.py
───────────
Extracts URLs from images using OCR (pytesseract).

Used as a FALLBACK when QR decoding fails — some phishing emails
embed a URL as plain text in an image instead of a QR code.

Also used to extract URLs from screenshots taken by the sandbox.

Handles:
  - PNG, JPEG, WEBP images
  - Low-contrast text via preprocessing
  - Multiple URLs per image (returns all found)
  - Cleaning up OCR noise around URLs

Install:
  pip install pytesseract Pillow opencv-python
  # Also install Tesseract binary:
  # Ubuntu/Debian: sudo apt-get install tesseract-ocr
  # macOS:         brew install tesseract
  # Windows:       https://github.com/UB-Mannheim/tesseract/wiki
"""

import logging
import re
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pytesseract
from PIL import Image

from app.models.schemas import QRDecodeResult

logger = logging.getLogger(__name__)

# Patterns for extracting URLs from noisy OCR text
URL_PATTERN = re.compile(
    r"https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+",
    re.IGNORECASE,
)

# Common OCR misreads in URLs
OCR_CORRECTIONS = {
    "htlps": "https",
    "htips": "https",
    "hllps": "https",
    "http;//": "http://",
    "https;//": "https://",
    "http:/ /": "http://",
    "https:/ /": "https://",
    "WWW.": "www.",
    "|": "l",   # pipe → l (common OCR error)
}


# ── Public API ─────────────────────────────────────────────────────────────

def extract_url_from_image(image_path: str) -> QRDecodeResult:
    """
    Primary entry point: run OCR on an image and extract the first URL found.

    Strategy:
      1. Load and preprocess image
      2. Run tesseract OCR
      3. Apply URL pattern matching
      4. Clean up common OCR errors in the URL

    Returns QRDecodeResult with source="ocr".
    """
    path = Path(image_path)
    if not path.exists():
        return QRDecodeResult(success=False, error=f"File not found: {image_path}", source="ocr")

    logger.info(f"Running OCR on: {image_path}")

    img = _load_and_preprocess(image_path)
    if img is None:
        return QRDecodeResult(success=False, error="Failed to load image", source="ocr")

    text = _run_ocr(img)
    if not text.strip():
        return QRDecodeResult(success=False, error="OCR returned empty text", source="ocr")

    logger.debug(f"OCR raw text:\n{text[:300]}")

    # Clean text and find URLs
    cleaned_text = _fix_ocr_errors(text)
    urls = extract_all_urls_from_text(cleaned_text)

    if not urls:
        return QRDecodeResult(
            success=False,
            error="No URLs found in OCR output",
            raw_data=text[:500],
            source="ocr",
        )

    primary_url = urls[0]
    logger.info(f"OCR extracted URL: {primary_url}")

    return QRDecodeResult(
        url=primary_url,
        raw_data=text[:500],
        source="ocr",
        success=True,
    )


def extract_all_urls_from_image(image_path: str) -> list[str]:
    """
    Run OCR and return ALL URLs found in the image.
    Useful when an email image contains multiple suspicious links.
    """
    img = _load_and_preprocess(image_path)
    if img is None:
        return []

    text = _run_ocr(img)
    cleaned = _fix_ocr_errors(text)
    return extract_all_urls_from_text(cleaned)


def extract_all_urls_from_text(text: str) -> list[str]:
    """
    Extract all URLs from a plain text string.
    Used by the sandbox tool to scan page source for embedded links.
    """
    raw_urls = URL_PATTERN.findall(text)

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in raw_urls:
        # Strip trailing punctuation that OCR sometimes attaches
        url = url.rstrip(".,;:!?\"'")
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def extract_text_from_image(image_path: str) -> Optional[str]:
    """
    Return the full OCR text from an image (no URL filtering).
    Used to extract email body text from embedded images.
    """
    img = _load_and_preprocess(image_path)
    if img is None:
        return None
    return _run_ocr(img)


# ── Preprocessing ──────────────────────────────────────────────────────────

def _load_and_preprocess(image_path: str) -> Optional[np.ndarray]:
    """
    Load image and apply preprocessing to improve OCR accuracy:
      - Convert to grayscale
      - Scale up small images (Tesseract works best at 300+ DPI)
      - Denoise
      - Threshold to high-contrast B&W
    """
    try:
        pil_img = Image.open(image_path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Upscale if image is small — Tesseract accuracy drops below ~200px height
        h, w = gray.shape
        if h < 400:
            scale = 400 / h
            gray = cv2.resize(gray, (int(w * scale), 400), interpolation=cv2.INTER_CUBIC)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Threshold: Otsu's method auto-selects the best threshold value
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    except Exception as e:
        logger.error(f"Image preprocessing failed for {image_path}: {e}")
        return None


def _run_ocr(img: np.ndarray) -> str:
    """
    Run Tesseract OCR with optimized config for URL extraction.

    Config breakdown:
      --oem 3   → Use LSTM engine (most accurate)
      --psm 6   → Assume a uniform block of text (best for email body images)
      -c tessedit_char_whitelist → Only expected URL characters
    """
    try:
        # First pass: full character set for context
        full_text = pytesseract.image_to_string(
            img,
            config="--oem 3 --psm 6",
        )

        # Second pass: URL-character-only for more accurate link detection
        url_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=%"
        url_text = pytesseract.image_to_string(
            img,
            config=f"--oem 3 --psm 6 -c tessedit_char_whitelist={url_chars}",
        )

        # Merge: use full_text as primary, url_text for URL extraction
        return full_text + "\n" + url_text

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed or not in PATH. "
            "Ubuntu: sudo apt-get install tesseract-ocr | macOS: brew install tesseract"
        )
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""


def _fix_ocr_errors(text: str) -> str:
    """Apply known OCR misread corrections for URL components."""
    for wrong, correct in OCR_CORRECTIONS.items():
        text = text.replace(wrong, correct)
    return text


# ── Manual test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python -m app.tools.ocr_tool <image_path>")
        sys.exit(1)

    result = extract_url_from_image(sys.argv[1])
    print(f"\nSuccess: {result.success}")
    print(f"URL: {result.url}")
    print(f"Source: {result.source}")
    if result.error:
        print(f"Error: {result.error}")