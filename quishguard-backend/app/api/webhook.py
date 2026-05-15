import base64
import json
import logging

from fastapi import APIRouter, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/gmail")
async def gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        body = await request.json()
        message = body.get("message", {})
        data_b64 = message.get("data", "")
        
        body_bytes = await request.body()
        if not body_bytes:
            return {"status": "ignored", "detail": "Empty body"}

        if not data_b64:
            return {"status": "no data"}

        decoded = base64.b64decode(data_b64).decode("utf-8")
        payload = json.loads(decoded)
        history_id = str(payload.get("historyId", ""))

        if not history_id:
            return {"status": "no historyId"}

        logger.info(f"Gmail webhook triggered — historyId: {history_id}")
        background_tasks.add_task(_handle_new_emails, history_id, db)
        return {"status": "ok"}
        

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}


async def _handle_new_emails(history_id: str, db: Session):
    try:
        from app.tools.gmail_tool import get_history, fetch_email_by_id, download_all_image_attachments
        from app.services.pipeline import run_pipeline

        new_message_ids = get_history(history_id)
        logger.info(f"Found {len(new_message_ids)} new message(s)")

        for msg_id in new_message_ids:
            email = fetch_email_by_id(msg_id)
            if not email:
                continue

            image_paths = download_all_image_attachments(email)
            if not image_paths:
                continue

            for image_path in image_paths:
                result = await run_pipeline(email=email, image_path=image_path, db=db)
                if result:
                    logger.info(f"Pipeline complete — verdict: {result.verdict} | score: {result.risk_score}")

    except Exception as e:
        logger.error(f"Background email processing failed: {e}")