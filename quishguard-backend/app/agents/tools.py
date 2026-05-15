"""
agents/tools.py
───────────────
CrewAI tool definitions for the QuishGuard multi-agent pipeline.

Design:
  - Image-dependent tools (QR decode, OCR) use a FACTORY pattern.
    `create_image_tools(path)` returns tools with the real filesystem path
    baked in via closure, so the LLM never needs to guess the path.
  - URL-dependent tools (sandbox, threat intel) remain module-level since
    the LLM correctly passes URLs extracted from earlier task results.

Fixed:
  - Tools no longer expose `image_path: str` in their signature, which
    caused CrewAI's LLM to pass the literal string "string" instead of
    a real path.
"""

import asyncio
import logging

from crewai.tools import tool
from app.tools.qr_tool import decode_qr_from_file
from app.tools.ocr_tool import extract_url_from_image
from app.tools.sandbox_tool import visit_url_async
from app.tools.virustotal_tool import check_virustotal
from app.tools.domain_tool import check_domain_age
from app.services.pipeline import _extract_domain

logger = logging.getLogger(__name__)


# ── Factory: image-bound tools ─────────────────────────────────────────────

def create_image_tools(image_path: str):
    """
    Return (qr_tool, ocr_tool) pre-bound to `image_path`.

    The closure guarantees the tools always operate on the uploaded file,
    regardless of what the LLM passes as arguments.
    """

    @tool("qr_extraction_tool")
    def qr_extraction_tool(placeholder: str = "auto") -> str:
        """Decodes a QR code from the uploaded image.
        The image path is automatically provided — call this tool with no arguments.
        Returns the decoded QR data including any embedded URL."""
        logger.info(f"[qr_extraction_tool] Decoding QR from: {image_path}")
        result = decode_qr_from_file(image_path)
        if result.success:
            return f"QR decode SUCCESS. URL: {result.url}. Raw data: {result.raw_data}"
        return f"QR decode FAILED: {result.error}"

    @tool("ocr_url_tool")
    def ocr_tool(placeholder: str = "auto") -> str:
        """Performs OCR on the uploaded image to find text-based URLs.
        The image path is automatically provided — call this tool with no arguments.
        Use this if the QR extraction tool finds no QR code."""
        logger.info(f"[ocr_url_tool] Running OCR on: {image_path}")
        result = extract_url_from_image(image_path)
        if result.success:
            return f"OCR SUCCESS. URL found: {result.url}. Source: {result.source}"
        return f"OCR FAILED: {result.error}"

    return qr_extraction_tool, ocr_tool


# ── Module-level tools (URL-based, no image dependency) ────────────────────

@tool("sandbox_investigation_tool")
def sandbox_investigation_tool(url: str) -> str:
    """Visits a URL in a secure, headless browser sandbox.
    Returns the final destination URL, redirect count, and
    whether a login/credential-harvesting form was detected.
    Pass the URL extracted by the forensic agent."""
    logger.info(f"[sandbox_investigation_tool] Visiting: {url}")
    try:
        # Run the async Playwright visit in a new event loop.
        # This is safe because CrewAI calls tools synchronously.
        result = asyncio.run(visit_url_async(url))
    except RuntimeError:
        # If an event loop is already running (shouldn't happen in thread pool),
        # create a new loop explicitly.
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(visit_url_async(url))
        finally:
            loop.close()

    if result.success:
        return (
            f"Sandbox visit SUCCESS.\n"
            f"Final URL: {result.final_url}\n"
            f"Redirects: {result.redirect_count}\n"
            f"Login form detected: {result.has_login_form}\n"
            f"Page title: {result.page_title}\n"
            f"Screenshot: {result.screenshot_path}"
        )
    return f"Sandbox visit FAILED: {result.error}"


@tool("reputation_intelligence_tool")
def threat_intelligence_tool(url: str) -> str:
    """Checks the reputation of a URL using VirusTotal and WHOIS data.
    Returns malicious engine count and domain age in days.
    Pass the URL to analyze."""
    logger.info(f"[reputation_intelligence_tool] Checking: {url}")
    domain = _extract_domain(url)
    vt_result = check_virustotal(url)
    domain_result = check_domain_age(domain)

    return (
        f"Threat Intelligence Report:\n"
        f"  VirusTotal score: {vt_result.score}\n"
        f"  Malicious engines: {vt_result.malicious_count}/{vt_result.total_engines}\n"
        f"  Domain: {domain}\n"
        f"  Domain age: {domain_result.age_days} days\n"
        f"  Is new domain (<30 days): {domain_result.is_new}"
    )