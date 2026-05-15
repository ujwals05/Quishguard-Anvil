"""app/tools/domain_tool.py"""
import logging
from datetime import datetime, timezone
from typing import Optional

import whois

from app.models.schemas import DomainAgeResult

logger = logging.getLogger(__name__)


def check_domain_age(domain: str) -> DomainAgeResult:
    """
    Look up domain registration date via WHOIS and calculate age in days.
    Domains < 30 days old are flagged as 'new' (strong phishing signal).
    """
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date

        # Some registrars return a list of dates — take the earliest
        if isinstance(creation_date, list):
            creation_date = min(creation_date)

        if not creation_date:
            return DomainAgeResult(domain=domain, error="No creation date in WHOIS record")

        # Ensure timezone-aware comparison
        if creation_date.tzinfo is None:
            creation_date = creation_date.replace(tzinfo=timezone.utc)

        age_days = (datetime.now(timezone.utc) - creation_date).days

        return DomainAgeResult(
            domain=domain,
            age_days=age_days,
            creation_date=creation_date.isoformat(),
            is_new=age_days < 30,
        )

    except Exception as e:
        logger.warning(f"WHOIS lookup failed for {domain}: {e}")
        return DomainAgeResult(domain=domain, error=str(e))