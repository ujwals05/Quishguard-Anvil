from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ── Tool result schemas ────────────────────────────────────────────────────

class QRDecodeResult(BaseModel):
    url:      Optional[str] = None
    raw_data: Optional[str] = None
    source:   str = "qr_code"
    success:  bool = False
    error:    Optional[str] = None


class SandboxResult(BaseModel):
    original_url:    str
    final_url:       Optional[str] = None
    redirects:       List[str] = []
    redirect_count:  int = 0
    has_login_form:  bool = False
    page_title:      Optional[str] = None
    screenshot_path: Optional[str] = None
    html_snippet:    Optional[str] = None
    success:         bool = False
    error:           Optional[str] = None


class VirusTotalResult(BaseModel):
    url:             str
    score:           Optional[str] = None
    malicious_count: int = 0
    total_engines:   int = 0
    is_malicious:    bool = False
    error:           Optional[str] = None


class DomainAgeResult(BaseModel):
    domain:        str
    age_days:      Optional[int] = None
    creation_date: Optional[str] = None
    is_new:        bool = False
    error:         Optional[str] = None


# ── API request schemas ────────────────────────────────────────────────────

class ManualScanRequest(BaseModel):
    url:        Optional[str] = None
    image_path: Optional[str] = None


# ── API response schemas ───────────────────────────────────────────────────

class ThreatOut(BaseModel):
    id:               int
    email_id:         Optional[str]
    sender:           Optional[str]
    subject:          Optional[str]
    extracted_url:    Optional[str]
    final_url:        Optional[str]
    domain:           Optional[str]
    risk_score:       float
    verdict:          str
    reasons:          List[str]
    has_login_form:   bool
    redirect_count:   int
    vt_score:         Optional[str]
    domain_age_days:  Optional[int]
    screenshot_path:  Optional[str]
    reasoning_log:    List[Any]
    is_blocked:       bool
    created_at:       Optional[datetime]

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_scanned:  int
    total_phishing: int
    total_blocked:  int
    total_clean:    int
    recent_threats: List[ThreatOut]