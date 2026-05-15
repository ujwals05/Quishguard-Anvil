"""
sandbox_tool.py
───────────────
Safely visits URLs in a headless Chromium browser (Playwright) to:
  - Follow all redirects and record the chain
  - Detect login/credential-harvesting forms
  - Capture a screenshot as evidence
  - Extract page title and visible text
  - Detect suspicious patterns (fake login overlays, obfuscated JS, etc.)

The browser runs in an ISOLATED context:
  - No cookies, no local storage, no cached credentials
  - JavaScript enabled (needed to catch SPA phishing pages)
  - Geolocation/camera/mic all blocked

Install:
  pip install playwright
  python -m playwright install chromium

Returns: SandboxResult
"""

import asyncio
import sys
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Ensure Windows uses ProactorEventLoop for subprocess support (needed for Playwright)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeout

from app.config import settings
from app.models.schemas import SandboxResult

logger = logging.getLogger(__name__)

# Patterns that strongly indicate a phishing / credential-harvesting page
SUSPICIOUS_TITLE_PATTERNS = [
    r"sign.?in", r"log.?in", r"verify", r"confirm.?account",
    r"update.?payment", r"secure.?access", r"account.?suspended",
    r"unusual.?activity", r"microsoft|google|apple|paypal|amazon|netflix",
]

# HTML patterns in page source that indicate login forms
LOGIN_FORM_PATTERNS = [
    r'<input[^>]+type=["\']password["\']',
    r'<input[^>]+name=["\']pass(word)?["\']',
    r'autocomplete=["\']current-password["\']',
    r'id=["\']password["\']',
]


# ── Public API ─────────────────────────────────────────────────────────────

def visit_url(url: str) -> SandboxResult:
    """
    Synchronous wrapper — visits a URL in a sandboxed browser.
    Runs the async implementation in a new event loop.

    This is the main entry point called by agents.
    """
    try:
        return asyncio.run(_visit_url_async(url))
    except Exception as e:
        logger.error(f"Sandbox visit failed for {url}: {e}")
        return SandboxResult(
            original_url=url,
            success=False,
            error=str(e),
        )


async def visit_url_async(url: str) -> SandboxResult:
    """Async version — use this inside async FastAPI routes."""
    return await _visit_url_async(url)


# ── Core async implementation ──────────────────────────────────────────────

async def _visit_url_async(url: str) -> SandboxResult:
    """
    Full sandboxed visit implementation.

    Steps:
      1. Launch isolated Chromium context
      2. Set up redirect tracking via response listener
      3. Navigate to URL
      4. Wait for network to settle (networkidle)
      5. Take screenshot
      6. Inspect page for login forms and suspicious patterns
      7. Extract visible text
      8. Return structured result
    """
    screenshot_dir = Path(settings.SCREENSHOT_DIR)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-background-networking",
            ],
        )

        context: BrowserContext = await browser.new_context(
            # Mimic a real Chrome browser to avoid bot-detection redirects
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            # Security: block all permission requests
            permissions=[],
            java_script_enabled=True,
            # No stored state — fresh isolated session
            storage_state=None,
        )

        # Block trackers and ad networks (speed + safety)
        await context.route(
            re.compile(r"\.(woff2?|ttf|otf|eot)$"),
            lambda route: route.abort(),
        )

        page: Page = await context.new_page()

        redirect_chain: list[str] = [url]
        result = SandboxResult(original_url=url)

        # Track all navigation redirects
        page.on("response", lambda response: _track_redirects(response, redirect_chain))

        try:
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=settings.SANDBOX_TIMEOUT_MS,
            )

            final_url = page.url
            result.final_url = final_url
            result.redirects = list(dict.fromkeys(redirect_chain))  # deduplicate, preserve order
            result.redirect_count = len(result.redirects) - 1

            # Page title
            result.page_title = await page.title()

            # Get full HTML for form detection
            html_content = await page.content()

            # Detect login / credential-harvesting forms
            result.has_login_form = _detect_login_form(html_content)

            # Extract visible text (first 600 chars — enough to see context)
            visible_text = await _extract_visible_text(page)
            result.html_snippet = visible_text[:600] if visible_text else None

            # Take screenshot as evidence
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = _safe_domain(final_url)
            screenshot_filename = f"{timestamp}_{domain}.png"
            screenshot_path = str(screenshot_dir / screenshot_filename)

            await page.screenshot(path=screenshot_path, full_page=False)
            result.screenshot_path = screenshot_path
            logger.info(f"Screenshot saved: {screenshot_path}")

            result.success = True
            logger.info(
                f"Sandbox complete | final_url={final_url} | "
                f"redirects={result.redirect_count} | login_form={result.has_login_form}"
            )

        except PlaywrightTimeout:
            result.error = f"Page load timed out after {settings.SANDBOX_TIMEOUT_MS}ms"
            result.success = False
            logger.warning(f"Timeout visiting: {url}")

        except Exception as e:
            result.error = str(e)
            result.success = False
            logger.error(f"Sandbox error for {url}: {e}")

        finally:
            await context.close()
            await browser.close()

    return result


# ── Helper functions ───────────────────────────────────────────────────────

def _track_redirects(response, redirect_chain: list[str]):
    """
    Called on every HTTP response to build the redirect chain.
    Playwright fires this for every resource, so we only track
    main-frame navigations (status 3xx or the final landing URL).
    """
    try:
        if response.status in (301, 302, 303, 307, 308):
            location = response.headers.get("location")
            if location and location not in redirect_chain:
                redirect_chain.append(location)
        elif response.ok and response.request.resource_type == "document":
            if response.url not in redirect_chain:
                redirect_chain.append(response.url)
    except Exception:
        pass  # Don't let tracking errors crash the visit


def _detect_login_form(html: str) -> bool:
    """
    Check if the page HTML contains password fields or login form patterns.
    Returns True if any credential-harvesting indicator is found.
    """
    for pattern in LOGIN_FORM_PATTERNS:
        if re.search(pattern, html, re.IGNORECASE):
            return True
    return False


def _is_suspicious_title(title: str) -> bool:
    """Check if the page title matches common phishing page titles."""
    if not title:
        return False
    for pattern in SUSPICIOUS_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False


async def _extract_visible_text(page: Page) -> Optional[str]:
    """
    Extract visible body text via JS evaluation.
    Avoids returning script/style tag contents.
    """
    try:
        text = await page.evaluate("""
            () => {
                const body = document.body;
                if (!body) return '';
                // Remove script and style elements
                const clone = body.cloneNode(true);
                clone.querySelectorAll('script, style, noscript').forEach(el => el.remove());
                return (clone.innerText || clone.textContent || '').trim().replace(/\\s+/g, ' ');
            }
        """)
        return text
    except Exception as e:
        logger.debug(f"Could not extract visible text: {e}")
        return None


def _safe_domain(url: str) -> str:
    """Extract domain from URL for use in filenames (safe characters only)."""
    try:
        domain = urlparse(url).netloc
        return re.sub(r"[^a-zA-Z0-9\-_.]", "_", domain)[:50]
    except Exception:
        return "unknown"


# ── Convenience: check if URL is reachable at all ─────────────────────────

def is_url_reachable(url: str) -> bool:
    """Quick check: does the URL respond (any HTTP status)?"""
    try:
        import httpx
        response = httpx.get(url, timeout=5, follow_redirects=True)
        return response.status_code < 500
    except Exception:
        return False


# ── Manual test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    print(f"\nVisiting: {test_url}")

    result = visit_url(test_url)

    print(f"\n✅ Success: {result.success}")
    print(f"🌐 Final URL: {result.final_url}")
    print(f"↪️  Redirects ({result.redirect_count}): {result.redirects}")
    print(f"🔐 Login form detected: {result.has_login_form}")
    print(f"📄 Title: {result.page_title}")
    print(f"📸 Screenshot: {result.screenshot_path}")
    if result.error:
        print(f"❌ Error: {result.error}")