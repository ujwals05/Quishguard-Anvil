
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.schemas import ManualScanRequest, ThreatOut
from app.services.pipeline import run_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ThreatOut)
async def manual_scan(request: ManualScanRequest, db: Session = Depends(get_db)):
    """
    Manually scan a URL or an image path for phishing.
    """
    if not request.url and not request.image_path:
        raise HTTPException(status_code=400, detail="Must provide either a URL or image_path")

    logger.info(f"Manual scan request received: URL={request.url} Image={request.image_path}")
    
    # Run the Phase 2 sequential pipeline
    result = await run_pipeline(
        email=None, 
        image_path=request.image_path, 
        direct_url=request.url, 
        db=db
    )

    if not result:
        raise HTTPException(status_code=422, detail="Pipeline failed to extract or process a URL")

    return result