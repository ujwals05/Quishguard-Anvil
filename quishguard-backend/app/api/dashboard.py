# from fastapi import APIRouter, Request, BackgroundTasks, Depends
# from sqlalchemy.orm import Session

# router = APIRouter()  # ← this line must exist



from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.threat import ThreatRecord
from app.models.schemas import DashboardStats

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Fetch summary statistics for the dashboard.
    """
    total = db.query(ThreatRecord).count()
    phishing = db.query(ThreatRecord).filter(ThreatRecord.verdict == "phishing").count()
    blocked = db.query(ThreatRecord).filter(ThreatRecord.is_blocked == True).count()
    clean = db.query(ThreatRecord).filter(ThreatRecord.verdict == "clean").count()

    # Get 10 most recent threat events
    recent = db.query(ThreatRecord).order_by(ThreatRecord.created_at.desc()).limit(10).all()

    return DashboardStats(
        total_scanned=total,
        total_phishing=phishing,
        total_blocked=blocked,
        total_clean=clean,
        recent_threats=recent
    )