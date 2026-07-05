"""WebSocket connection manager for real-time analysis push (PRD §7.8)."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks connected clients per project and broadcasts events to them."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[project_id].add(websocket)
        logger.info("WS client connected to project %s", project_id)

    async def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[project_id].discard(websocket)
        logger.info("WS client disconnected from project %s", project_id)

    async def broadcast(self, project_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to every client subscribed to a project."""
        async with self._lock:
            targets = list(self._connections.get(project_id, set()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception as exc:  # noqa: BLE001 - prune broken sockets
                logger.debug("WS send failed, dropping client: %s", exc)
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[project_id].discard(ws)


manager = ConnectionManager()
