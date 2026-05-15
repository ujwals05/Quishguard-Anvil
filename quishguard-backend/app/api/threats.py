from fastapi import APIRouter, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session

router = APIRouter()  # ← this line must exist