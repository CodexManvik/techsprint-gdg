"""Asynchronous turn scoring service using the shared interview engine model."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from backend.config.settings import settings
from backend.core.interview.engine import InterviewEngine
from backend.db.repository import DatabaseRepository

logger = logging.getLogger(__name__)


class TurnScoringService:
    """Background scoring queue that never blocks the real-time interviewer path."""

    def __init__(self, engine: InterviewEngine, db: DatabaseRepository):
        self.engine = engine
        self.db = db
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=settings.SCORING_QUEUE_MAXSIZE)
        self.worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self.worker_task = asyncio.create_task(self._worker_loop(), name="turn-scoring-worker")
        logger.info("Turn scoring worker started")

    async def stop(self):
        if not self._running:
            return

        self._running = False
        if self.worker_task is not None:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Turn scoring worker stopped")

    async def enqueue(self, payload: dict[str, Any]) -> bool:
        """Queue one scoring job. Returns False if queue is full."""
        try:
            self.queue.put_nowait(payload)
            return True
        except asyncio.QueueFull:
            logger.warning("Scoring queue full; dropping scoring payload for session=%s", payload.get("session_id"))
            return False

    async def _worker_loop(self):
        while self._running:
            payload = await self.queue.get()
            try:
                await self._process_payload(payload)
            except Exception:
                logger.exception("Scoring worker failed to process payload")
            finally:
                self.queue.task_done()

    async def _process_payload(self, payload: dict[str, Any]):
        message_id = payload.get("message_id")
        if not message_id:
            return

        score = await self.engine.score_turn(payload)
        rating = max(1, min(100, int(score.get("rating", 70))))
        feedback = str(score.get("feedback", ""))
        improved_answer = str(score.get("improved_answer", ""))

        await self.db.update_message_analysis(message_id, rating, feedback, improved_answer)
