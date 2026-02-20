from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[channel].add(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        if channel in self._connections and websocket in self._connections[channel]:
            self._connections[channel].remove(websocket)
            if not self._connections[channel]:
                del self._connections[channel]

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        sockets = list(self._connections.get(channel, set()))
        for socket in sockets:
            try:
                await socket.send_json(message)
            except Exception:
                self.disconnect(channel, socket)


connection_manager = ConnectionManager()
