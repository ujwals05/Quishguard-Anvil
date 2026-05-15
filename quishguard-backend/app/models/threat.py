from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class ThreatRecord(Base):
    __tablename__ = "threats"

    id                = Column(Integer, primary_key=True, index=True)

    # Email metadata
    email_id          = Column(String,  nullable=True, index=True)
    sender            = Column(String,  nullable=True)
    subject           = Column(String,  nullable=True)

    # URL chain
    extracted_url     = Column(String,  nullable=True)   # URL pulled from QR code
    final_url         = Column(String,  nullable=True)   # URL after following redirects
    domain            = Column(String,  nullable=True, index=True)

    # Threat scoring
    risk_score        = Column(Float,   default=0.0)
    verdict           = Column(String,  default="pending")  # pending|clean|low_risk|suspicious|phishing
    reasons           = Column(JSON,    default=list)        # list of reason strings

    # Evidence
    has_login_form    = Column(Boolean, default=False)
    redirect_count    = Column(Integer, default=0)
    vt_score          = Column(String,  nullable=True)       # e.g. "8/90"
    domain_age_days   = Column(Integer, nullable=True)
    screenshot_path   = Column(String,  nullable=True)

    # Full reasoning log (every pipeline step)
    reasoning_log     = Column(JSON,    default=list)

    # Action
    is_blocked        = Column(Boolean, default=False)
    blocked_at        = Column(DateTime, nullable=True)

    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now())