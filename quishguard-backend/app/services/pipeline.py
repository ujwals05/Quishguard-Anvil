"""
services/pipeline.py
─────────────────────
Phase 2 sequential pipeline — runs tools in order WITHOUT agents.
Get this working first. Once it's solid, swap with the CrewAI crew.

Flow:
  image_path or direct_url
       ↓
  QR decode (→ fallback OCR)
       ↓
  Sandbox visit
       ↓
  VirusTotal check
       ↓
  Domain age check
       ↓
  Threat scoring
       ↓
  Save to DB + auto-block if score ≥ threshold
"""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config import settings
from app.models.threat import ThreatRecord
from app.tools.qr_tool import decode_qr_from_file
from app.tools.ocr_tool import extract_url_from_image
from app.tools.sandbox_tool import visit_url
from app.tools.virustotal_tool import check_virustotal
from app.tools.domain_tool import check_domain_age

logger = logging.getLogger(__name__)


async def run_pipeline(
    email: Optional[dict],
    image_path: Optional[str],
    direct_url: Optional[str] = None,
    db: Session = None,
) -> Optional[ThreatRecord]:
    """
    Run the full detection pipeline.
    Returns a saved ThreatRecord, or None if we couldn't extract a URL.
    """
    log_steps = []

    def log(step: str, detail: str = ""):
        entry = {"step": step, "detail": detail}
        log_steps.append(entry)
        logger.info(f"[Pipeline] {step}: {detail}")

    # ── Step 1: Extract URL ───────────────────────────────────────────────
    extracted_url = direct_url

    if not extracted_url and image_path:
        log("QR Decode", f"Attempting QR decode on {image_path}")
        qr_result = decode_qr_from_file(image_path)

        if qr_result.success and qr_result.url:
            extracted_url = qr_result.url
            log("QR Decode", f"✅ URL extracted: {extracted_url}")
        else:
            log("QR Decode", f"❌ Failed: {qr_result.error} — trying OCR fallback")

            ocr_result = extract_url_from_image(image_path)
            if ocr_result.success and ocr_result.url:
                extracted_url = ocr_result.url
                log("OCR Fallback", f"✅ URL extracted via OCR: {extracted_url}")
            else:
                log("OCR Fallback", f"❌ No URL found: {ocr_result.error}")

    if not extracted_url:
        log("Pipeline", "❌ No URL found — aborting")
        return None

    domain = _extract_domain(extracted_url)

    # ── Step 2: Sandbox Visit ─────────────────────────────────────────────
    log("Sandbox", f"Visiting {extracted_url}")
    sandbox = visit_url(extracted_url)

    if sandbox.success:
        log("Sandbox", f"✅ Final URL: {sandbox.final_url} | Redirects: {sandbox.redirect_count} | Login form: {sandbox.has_login_form}")
    else:
        log("Sandbox", f"⚠️ Visit failed: {sandbox.error}")

    # ── Step 3: VirusTotal ────────────────────────────────────────────────
    log("VirusTotal", f"Checking {extracted_url}")
    vt_result = check_virustotal(extracted_url)
    if vt_result.error:
        log("VirusTotal", f"⚠️ {vt_result.error}")
    else:
        log("VirusTotal", f"Score: {vt_result.score} | Malicious: {vt_result.malicious_count}")

    # ── Step 4: Domain Age ────────────────────────────────────────────────
    log("Domain Age", f"Checking {domain}")
    domain_result = check_domain_age(domain)
    if domain_result.error:
        log("Domain Age", f"⚠️ {domain_result.error}")
    else:
        log("Domain Age", f"Age: {domain_result.age_days} days | New: {domain_result.is_new}")

    # ── Step 5: Threat Scoring ────────────────────────────────────────────
    score, reasons = _calculate_risk_score(sandbox, vt_result, domain_result)
    verdict = _score_to_verdict(score)
    log("Threat Score", f"Score: {score} | Verdict: {verdict} | Reasons: {reasons}")

    # ── Step 6: Save to DB ────────────────────────────────────────────────
    should_block = score >= settings.RISK_SCORE_BLOCK_THRESHOLD

    record = ThreatRecord(
        email_id=email["id"] if email else None,
        sender=email["sender"] if email else None,
        subject=email["subject"] if email else None,
        extracted_url=extracted_url,
        final_url=sandbox.final_url,
        domain=domain,
        risk_score=score,
        verdict=verdict,
        reasons=reasons,
        has_login_form=sandbox.has_login_form,
        redirect_count=sandbox.redirect_count,
        vt_score=vt_result.score,
        domain_age_days=domain_result.age_days,
        screenshot_path=sandbox.screenshot_path,
        reasoning_log=log_steps,
        is_blocked=should_block,
        blocked_at=datetime.utcnow() if should_block else None,
    )

    if db:
        db.add(record)
        db.commit()
        db.refresh(record)
        log("DB", f"Saved as ThreatRecord id={record.id}")

    if should_block:
        log("Auto-Block", f"🚫 Domain {domain} auto-blocked (score={score})")

    return record


# ── Scoring ────────────────────────────────────────────────────────────────

def _calculate_risk_score(sandbox, vt_result, domain_result) -> tuple[float, list[str]]:
    """
    Simple weighted scoring. Each signal adds to the base score.
    Max score = 100.

    Adjust weights as you gather data on what's most predictive.
    """
    score = 0.0
    reasons = []

    # Login form (+35 points — strongest single signal)
    if sandbox.has_login_form:
        score += 35
        reasons.append("Page contains a login / password form")

    # VirusTotal positives
    if vt_result.malicious_count >= 5:
        score += 30
        reasons.append(f"VirusTotal: {vt_result.malicious_count} engines flagged as malicious")
    elif vt_result.malicious_count >= 1:
        score += 15
        reasons.append(f"VirusTotal: {vt_result.malicious_count} engine(s) flagged as malicious")

    # New domain (< 30 days)
    if domain_result.is_new:
        score += 20
        reasons.append(f"Domain is very new ({domain_result.age_days} days old)")
    elif domain_result.age_days and domain_result.age_days < 90:
        score += 10
        reasons.append(f"Domain is relatively new ({domain_result.age_days} days old)")

    # Multiple redirects
    if sandbox.redirect_count >= 3:
        score += 15
        reasons.append(f"URL redirected {sandbox.redirect_count} times before landing")
    elif sandbox.redirect_count >= 1:
        score += 5
        reasons.append(f"URL redirected {sandbox.redirect_count} time(s)")

    # Final URL differs significantly from original (domain hopping)
    if sandbox.final_url and sandbox.original_url:
        orig_domain = _extract_domain(sandbox.original_url)
        final_domain = _extract_domain(sandbox.final_url)
        if orig_domain != final_domain:
            score += 10
            reasons.append(f"Redirected from {orig_domain} to different domain {final_domain}")

    return min(score, 100.0), reasons


def _score_to_verdict(score: float) -> str:
    if score >= 70:
        return "phishing"
    elif score >= 40:
        return "suspicious"
    elif score > 0:
        return "low_risk"
    return "clean"


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return url