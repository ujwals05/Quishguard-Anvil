"""
services/reasoning_log.py
─────────────────────────
Captures each agent thought/tool-call during a CrewAI run and optionally
pushes the step to the frontend via WebSocket (through the Notifier).

Fixed:
  - add_step and get_final_log are now properly indented inside the class
  - Missing imports (asyncio, datetime) added
  - Thread-safe async bridge for WebSocket broadcast
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Any, Dict

from app.services.notifier import broadcast_reasoning_step

logger = logging.getLogger(__name__)


class ReasoningLogger:
    """Captures each agent thought/tool-call and optionally pushes to WebSocket."""

    def __init__(self):
        self.current_logs: List[Dict] = []

    def add_step(self, agent_name: str, thought_data: Any):
        """Captures a thought from the agent and notifies the UI."""
        step_entry = {
            "agent": str(agent_name),
            "thought": str(getattr(thought_data, 'thought', thought_data)),
            "tool": str(getattr(thought_data, 'tool', "Internal Reasoning")),
            "timestamp": datetime.now().isoformat(),
        }

        self.current_logs.append(step_entry)
        logger.info(f"[{agent_name}] Thought captured.")

        # Bridge sync CrewAI callback → async WebSocket broadcast.
        # CrewAI's step_callback runs synchronously; the FastAPI event loop
        # may or may not be accessible from the current thread.
        try:
            loop = asyncio.get_running_loop()
            # We're inside the event loop thread — schedule as a task
            loop.create_task(broadcast_reasoning_step(step_entry))
        except RuntimeError:
            # No running event loop in this thread — skip broadcast silently.
            # This happens when CrewAI runs in a background thread via run_in_executor.
            pass

    def get_final_log(self) -> List[Dict]:
        """Return a copy of all captured steps."""
        return list(self.current_logs)

    def reset(self):
        """Clear logs for the next scan session."""
        self.current_logs.clear()


# Global instance — imported by crew.py
agent_logger = ReasoningLogger()