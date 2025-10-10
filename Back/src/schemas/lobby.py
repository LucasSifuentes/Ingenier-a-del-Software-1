from pydantic import BaseModel
from typing import List

# Esquema para crear un nuevo lobby (lo que el front envía)
class LobbyCreateSchema(BaseModel):
    lobby_name: str 
    min_players: int     
    max_players: int
    user_id: int
    
class JoinLobbyRequest(BaseModel):
    user_id: int


class LobbyListItemSchema(BaseModel):
    lobby_id: int
    lobby_name: str
    player_amount: int
    max_players: int
    min_players: int
    lobby_owner: str
    
class Config:
        from_attributes = True

