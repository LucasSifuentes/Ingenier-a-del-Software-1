from sqlalchemy.orm import Session
from .. import models
from ..models import Lobby, Player, User 

def create_lobby(db: Session, lobby_name: str, max_players: int, min_players: int, lobby_owner: int):
    """Crea un nuevo lobby y asocia al usuario que lo crea, usando una sola transacción."""
    user = db.query(models.User).filter(models.User.user_id == lobby_owner).one_or_none()
    if not user:
        return {"success": False, "message": "Usuario no encontrado"}
    
    if not (2<= min_players <= max_players<= 6):
        return {"success": False, "message":"El rango de jugadores debe ser entre 2 y 6"}
    
    new_player = models.Player(player_name=user.user_name, user_id=user.user_id)
    db.add(new_player)
    db.flush() # Obtiene new_player.player_id

    new_lobby = models.Lobby(
        lobby_name=lobby_name, 
        player_amount=1, 
        max_players=max_players,
        min_players=min_players,  
        lobby_owner=new_player.player_id
    )
    db.add(new_lobby)
    db.flush() 

    new_player.lobby_id = new_lobby.lobby_id
    db.commit() 
    
    final_player = db.query(models.Player).filter(models.Player.player_id == new_player.player_id).one()

    return {
        "success": True,
        "message": "Lobby creado exitosamente",
        "lobby_id": new_lobby.lobby_id,
        "lobby_owner_player": final_player 
    }

def join_lobby(db: Session, lobby_id: int, user_id: int): 
    lobby = db.query(Lobby).filter(Lobby.lobby_id == lobby_id).one_or_none()
    
    if not lobby: 
        return {"success": False, "message": "Lobby no encontrado", "status_code": 404}
    user = db.query(User).filter(User.user_id == user_id).one_or_none()
    
    if not user: 
        return {"success": False, "message": "Usuario no encontrado", "status_code": 404}
    existing_player = db.query(Player).filter(Player.user_id == user_id, Player.lobby_id == lobby_id).first()
    
    if existing_player: 
        return {"success": True, "message": "Ya eres miembro del lobby", "player": existing_player, "lobby": lobby}
    
    if lobby.player_amount >= lobby.max_players: 
        return {"success": False, "message": "Lobby lleno", "status_code": 400}
    
    new_player = Player(player_name=user.user_name, user_id=user.user_id, lobby_id=lobby.lobby_id, game_id=None)
    db.add(new_player)
    lobby.player_amount += 1
    db.commit()
    db.refresh(new_player)
    db.refresh(lobby) 

    return {"success": True, "message": "Unido al lobby exitosamente", "player": new_player, "lobby": lobby}

def get_lobby_players(db: Session, lobby_id: int):
    """
    Obtiene la lista de todos los objetos Player (no solo IDs)
    actualmente unidos a un Lobby.
    """
    return db.query(Player).filter(Player.lobby_id == lobby_id).all()


def get_lobbies(db: Session, limit: int = 100):
    """
    Obtiene los lobbies y se une a la tabla de jugadores para obtener el nombre del dueño.
    """
    # Esta consulta une las dos tablas.
    results = (
        db.query(
            models.Lobby.lobby_id,
            models.Lobby.lobby_name,
            models.Lobby.player_amount,
            models.Lobby.max_players,
            models.Lobby.min_players,
            models.Player.player_name.label("lobby_owner")
        )
        .join(models.Player, models.Lobby.lobby_owner == models.Player.player_id)
        .limit(limit)
        .all()
    )
    
    # Devolvemos el resultado directamente.
    return results