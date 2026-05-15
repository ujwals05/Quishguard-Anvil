import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import webhook, threats, scan, dashboard
from app.database import create_tables
from fastapi import WebSocket, WebSocketDisconnect
from app.services.notifier import notifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    print("✅ Database tables created")
    yield
    # Shutdown
    print("👋 Shutting down QuishGuard")


app = FastAPI(
    title="QuishGuard API",
    description="AI-powered QR phishing detection using multi-agent system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(threats.router, prefix="/threats", tags=["Threats"])
app.include_router(scan.router, prefix="/scan", tags=["Scan"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "QuishGuard"}

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        notifier.disconnect(websocket)