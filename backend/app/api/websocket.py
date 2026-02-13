"""WebSocket endpoint for real-time stock price streaming."""

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.services.stock_data import fetch_quotes

logger = logging.getLogger(__name__)

ws_router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()


@ws_router.websocket("/ws/stocks")
async def stock_stream(websocket: WebSocket):
    """Stream real-time stock quotes via WebSocket."""
    await manager.connect(websocket)

    # Default symbols
    symbols = settings.DEFAULT_US_STOCKS + settings.DEFAULT_JP_STOCKS

    try:
        # Listen for client messages to update symbol list
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=settings.REFRESH_INTERVAL
                )
                msg = json.loads(data)
                if msg.get("type") == "subscribe":
                    symbols = msg.get("symbols", symbols)
                    logger.info(f"Client subscribed to: {symbols}")
            except asyncio.TimeoutError:
                pass

            # Fetch and send quotes
            quotes = fetch_quotes(symbols)
            if quotes:
                payload = {
                    "type": "quotes",
                    "data": [q.model_dump(mode="json") for q in quotes],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send_text(json.dumps(payload, default=str))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
