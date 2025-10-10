from pydantic import BaseModel
from typing import Optional

class PlayerRead(BaseModel):
    player_id: int
    player_name: str
    user_id: int
    lobby_id: int | None

    model_config = {
        "from_attributes": True 
    }