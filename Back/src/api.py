from fastapi import APIRouter
from src.endpoints.lobby_router import lobby_router  
from src.endpoints.user_router import user_router
from src.endpoints.game_router import game_router
from src.endpoints.ws_router import ws_router

api_router = APIRouter()

api_router.include_router(user_router, prefix="/users")
api_router.include_router(lobby_router, prefix="/lobbies")
api_router.include_router(game_router, prefix="/games")
api_router.include_router(ws_router, tags=["WebSockets"])
