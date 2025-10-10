from fastapi import WebSocket
from typing import Dict, List, Any
import json

class ConnectionManager:
    """
    Gestor de conexiones WebSocket:
    - active_connections: lista de conexiones globales
    - lobby_connections: diccionario de conexiones por lobby_id
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

        self.lobby_connections: Dict[int, List[WebSocket]] = {}

    # Métodos generales
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        json_string = json.dumps(data, default=str)
        for connection in self.active_connections:
            await connection.send_text(json_string)

    # Métodos específicos para lobbies
    async def connect_lobby(self, websocket: WebSocket, lobby_id: int):
        await websocket.accept()
        if lobby_id not in self.lobby_connections:
            self.lobby_connections[lobby_id] = []
        self.lobby_connections[lobby_id].append(websocket)

    def disconnect_lobby(self, websocket: WebSocket, lobby_id: int):
        if lobby_id in self.lobby_connections:
            self.lobby_connections[lobby_id].remove(websocket)
            if not self.lobby_connections[lobby_id]:
                del self.lobby_connections[lobby_id]

    async def broadcast_lobby(self, data: Dict[str, Any], lobby_id: int):
        if lobby_id not in self.lobby_connections:
            return
        json_string = json.dumps(data, default=str)
        for connection in self.lobby_connections[lobby_id]:
            await connection.send_text(json_string)


ws_manager = ConnectionManager()