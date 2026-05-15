from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class EmailEvent(Base):
    __tablename__ = "email_events"

    id                 = Column(Integer, primary_key=True, index=True)
    gmail_message_id   = Column(String,  unique=True, index=True)
    sender             = Column(String,  nullable=True)
    subject            = Column(String,  nullable=True)
    received_at        = Column(String,  nullable=True)
    has_qr_image       = Column(Boolean, default=False)
    attachment_names   = Column(JSON,    default=list)
    processed          = Column(Boolean, default=False)
    threat_id          = Column(Integer, nullable=True)
    created_at         = Column(DateTime, server_default=func.now())