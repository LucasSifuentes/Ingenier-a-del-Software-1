from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter
from sqlalchemy.orm import Session
from src.database.crud import crud_lobby 
from src.database.db import get_db
from src.endpoints.untils.websocket_manager import ws_manager
from src.database.models import Lobby 
from ..schemas.player import PlayerRead 

ws_router = APIRouter()

@ws_router.websocket("/ws/lobbies/{lobby_id}")
async def websocket_lobby(
    websocket: WebSocket,
    lobby_id: int,
    player_id: int,
    db: Session = Depends(get_db)
):
    lobby_obj = db.query(Lobby).filter(Lobby.lobby_id == lobby_id).one_or_none()
    if lobby_obj is None:
        await websocket.close(code=1008) 
        return

    await ws_manager.connect_lobby(websocket, lobby_id=lobby_id)

    try:
        all_players_db = crud_lobby.get_lobby_players(db, lobby_id)
        all_players_pydantic = [PlayerRead.from_orm(p) for p in all_players_db]
        
        # FIX CRÍTICO: Convertir Pydantic a Diccionario para JSON
        all_players_dict = [
            p.model_dump() if hasattr(p, 'model_dump') else p.dict() 
            for p in all_players_pydantic
        ]
        
        await websocket.send_json({
            "event": "initial_state",
            "lobby_id": lobby_id,
            "player_amount": lobby_obj.player_amount,
            "max_players": lobby_obj.max_players,
            "current_players": all_players_dict, # <-- ¡FIXEADO!
        })
        
        # Bucle principal para mantener la conexión VIVA y recibir mensajes
        while True:
            try:
                # Esto es necesario para mantener la conexión abierta
                _ = await websocket.receive_text() 
            except WebSocketDisconnect:
                break 
            except RuntimeError:
                break 

    # Bloque de limpieza CRÍTICO
    finally:
        ws_manager.disconnect_lobby(websocket, lobby_id=lobby_id)