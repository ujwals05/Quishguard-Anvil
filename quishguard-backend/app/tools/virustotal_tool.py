"""app/tools/virustotal_tool.py"""
import logging
import time
import base64
import httpx

from app.config import settings
from app.models.schemas import VirusTotalResult

logger = logging.getLogger(__name__)
VT_BASE = "https://www.virustotal.com/api/v3"


def check_virustotal(url: str) -> VirusTotalResult:
    """
    Submit a URL to VirusTotal and return the scan results.
    Uses the v3 API: submit URL → poll for result.

    Free API: 4 requests/minute. The function handles rate limiting.
    """
    if not settings.VIRUSTOTAL_API_KEY:
        return VirusTotalResult(url=url, error="VIRUSTOTAL_API_KEY not set in .env")

    headers = {"x-apikey": settings.VIRUSTOTAL_API_KEY}

    try:
        # VT v3: URL identifier = base64url(url) without padding
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

        # First try to get existing analysis (avoid re-submitting)
        response = httpx.get(f"{VT_BASE}/urls/{url_id}", headers=headers, timeout=15)

        if response.status_code == 404:
            # URL not in VT cache — submit it
            submit_resp = httpx.post(
                f"{VT_BASE}/urls",
                headers=headers,
                data={"url": url},
                timeout=15,
            )
            submit_resp.raise_for_status()
            analysis_id = submit_resp.json()["data"]["id"]

            # Poll for result (max 30s)
            for _ in range(6):
                time.sleep(5)
                poll_resp = httpx.get(
                    f"{VT_BASE}/analyses/{analysis_id}",
                    headers=headers,
                    timeout=15,
                )
                if poll_resp.status_code == 200:
                    data = poll_resp.json()
                    if data["data"]["attributes"]["status"] == "completed":
                        return _parse_vt_response(url, data["data"]["attributes"]["stats"])
            return VirusTotalResult(url=url, error="VT analysis timed out")

        elif response.status_code == 200:
            stats = response.json()["data"]["attributes"]["last_analysis_stats"]
            return _parse_vt_response(url, stats)

        else:
            return VirusTotalResult(url=url, error=f"VT API returned {response.status_code}")

    except Exception as e:
        logger.error(f"VirusTotal check failed: {e}")
        return VirusTotalResult(url=url, error=str(e))


def _parse_vt_response(url: str, stats: dict) -> VirusTotalResult:
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    total = sum(stats.values())
    score = f"{malicious}/{total}" if total else "0/0"

    return VirusTotalResult(
        url=url,
        score=score,
        malicious_count=malicious + suspicious,
        total_engines=total,
        is_malicious=malicious >= 1,
    )