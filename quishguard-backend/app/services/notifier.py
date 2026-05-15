import json
import logging
from typing import List, Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        # Store active browser connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New dashboard connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Dashboard disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        """Send a message to all connected dashboards."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to dashboard: {e}")
                # Connection might be dead, handled on next disconnect

# Global instance
notifier = Notifier()

async def broadcast_reasoning_step(step: Dict):
    """Bridge function called by the ReasoningLogger."""
    await notifier.broadcast({
        "type": "AGENT_THOUGHT",
        "data": step
    })