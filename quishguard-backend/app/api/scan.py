"""
api/scan.py
───────────
Scan endpoints for QuishGuard.

Endpoints:
  POST /scan/upload   — Upload an image for agentic phishing analysis (CrewAI)
  POST /scan/         — Manual scan with URL or pre-existing image path (pipeline)

Fixed:
  - Added proper UploadFile handling that saves to disk
  - Crew runs in a thread pool (run_in_executor) to avoid blocking the event loop
  - Removed duplicate crew+pipeline execution
  - Fixed the missing run_quishguard_crew import
  - Added defensive file validation
"""

import asyncio
import logging
import uuid
from pathlib import Path
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import ManualScanRequest, ThreatOut
from app.services.pipeline import run_pipeline
from app.agents.crew import QuishGuardCrew

router = APIRouter()
logger = logging.getLogger(__name__)

# Directory where uploaded images are saved
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


# ── POST /scan/upload — Agentic scan via file upload ───────────────────────

@router.post("/upload")
async def agentic_scan_upload(file: UploadFile = File(...)):
    """
    Upload an image for autonomous phishing analysis.

    Flow:
      1. Validate and save uploaded file to disk
      2. Pass real filesystem path to QuishGuardCrew
      3. CrewAI agents run: QR decode → OCR → Sandbox → Threat Intel
      4. Return structured JSON with verdict and reasoning chain
    """
    # ── Validate file type ────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # ── Save file to disk with unique name ────────────────────────────
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / unique_name

    try:
        contents = await file.read()
        save_path.write_bytes(contents)
        logger.info(f"Uploaded file saved: {save_path} ({len(contents)} bytes)")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # ── Verify file exists before kicking off the crew ────────────────
    if not save_path.exists():
        raise HTTPException(status_code=500, detail="File save failed — file not found on disk")

    # ── Run CrewAI in a thread pool to avoid blocking the event loop ──
    try:
        crew_instance = QuishGuardCrew(image_path=str(save_path.resolve()))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, crew_instance.run)
    except Exception as e:
        logger.error(f"Crew execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Crew execution failed: {str(e)}")

    return {
        "success": result.get("success", False),
        "image_path": str(save_path),
        "verdict": result.get("verdict", "unknown"),
        "reasoning_chain": result.get("reasoning_chain", []),
    }


# ── POST /scan/ — Manual scan with URL or existing image path (pipeline) ──

@router.post("/", response_model=ThreatOut)
async def manual_scan(request: ManualScanRequest, db: Session = Depends(get_db)):
    """
    Manually scan a URL or an existing image path for phishing.
    Uses the sequential pipeline (non-agentic).
    """
    if not request.url and not request.image_path:
        raise HTTPException(status_code=400, detail="Must provide either a URL or image_path")

    # Validate image path exists if provided
    if request.image_path:
        image_file = Path(request.image_path)
        if not image_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Image file not found: {request.image_path}. "
                       f"Use POST /scan/upload to upload a file instead.",
            )

    logger.info(f"Manual scan request: URL={request.url} Image={request.image_path}")

    # Run the sequential pipeline (Phase 2)
    result = await run_pipeline(
        email=None,
        image_path=request.image_path,
        direct_url=request.url,
        db=db,
    )

    if not result:
        raise HTTPException(status_code=422, detail="Pipeline failed to extract or process a URL")

    return result