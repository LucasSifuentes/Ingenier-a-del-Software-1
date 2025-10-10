from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.database.crud import crud_lobby
from src.schemas import lobby
from src.schemas.player import PlayerRead 
from src.endpoints.untils.websocket_manager import ws_manager
from typing import List

lobby_router = APIRouter() 

@lobby_router.post("/create", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
def create_lobby_endpoint(
    lobby_data: lobby.LobbyCreateSchema,
    db: Session = Depends(get_db)
):
    result = crud_lobby.create_lobby(
        db=db, 
        lobby_name=lobby_data.lobby_name, 
        max_players=lobby_data.max_players, 
        min_players=lobby_data.min_players,
        lobby_owner=lobby_data.user_id,
        
    )
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return PlayerRead.from_orm(result["lobby_owner_player"])


@lobby_router.post("/{lobby_id}/join", response_model=PlayerRead, status_code=status.HTTP_200_OK)
async def join_lobby_endpoint(lobby_id: int, request: lobby.JoinLobbyRequest, db: Session = Depends(get_db)):
    result = crud_lobby.join_lobby(db, lobby_id, request.user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=result.get("status_code", status.HTTP_400_BAD_REQUEST),
            detail=result["message"]
        )

    lobby_obj = result["lobby"]
    player_obj = result["player"]
    
    all_players_db = crud_lobby.get_lobby_players(db, lobby_id)
    all_players_pydantic = [PlayerRead.from_orm(p) for p in all_players_db]

    all_players_dict = [
        p.model_dump() if hasattr(p, 'model_dump') else p.dict() 
        for p in all_players_pydantic
    ]

    await ws_manager.broadcast_lobby({
        "event": "player_joined", 
        "lobby_id": lobby_id,
        "player_amount": lobby_obj.player_amount, 
        "max_players": lobby_obj.max_players,
        "current_players": all_players_dict,
    }, lobby_id=lobby_id)
    
    return PlayerRead.from_orm(player_obj) 
    
@lobby_router.get("/", response_model=List[lobby.LobbyListItemSchema])
def list_lobbies_endpoint(db: Session = Depends(get_db)):
    """
    Endpoint para listar Lobbies.
    """
    lobbies = crud_lobby.get_lobbies(db)
    return lobbies

