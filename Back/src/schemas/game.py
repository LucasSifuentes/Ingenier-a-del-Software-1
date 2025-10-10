from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

class StartGameRequest(BaseModel):
    user_id: int

class PlayerOrderInfo(BaseModel):
    player_id: int
    user_name: str
    birthday: str  # Se formatea como string para la respuesta
    proximity_days: int

class LobbyInfo(BaseModel):
    lobby_owner: int
    player_amount: int
    lobby_name: str
    lobby_id: int

class StartGameResponse(BaseModel):
    success: bool
    message: str
    game_id: Optional[int] = None
    lobby_info: Optional[LobbyInfo] = None
    player_order: Optional[List[PlayerOrderInfo]] = None