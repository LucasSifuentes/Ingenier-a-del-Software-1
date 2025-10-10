from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.database.db import get_db
from src.database.crud import crud_game
from src.schemas import game

game_router = APIRouter()

@game_router.post("/{lobby_id}/start", response_model=game.StartGameResponse)
def start_game_endpoint(
    lobby_id: int, 
    request: game.StartGameRequest,
    db: Session = Depends(get_db)
):
    """Endpoint para iniciar partida dentro del lobby"""
    result = crud_game.start_game(db, lobby_id, request.user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result