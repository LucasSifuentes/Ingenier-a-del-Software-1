from sqlalchemy.orm import Session
from src.database import models
import random
import json
from datetime import datetime, date
from src.schemas.player import PlayerRead

def start_game(db: Session, lobby_id: int, user_id: int, player_id: int):
    """
    Iniciar partida dentro del lobby
    1. Verificar que el lobby existe
    2. Verificar que el player es el owner
    3. Verificar que hay jugadores (mínimo 2) y máximo 6
    4. Ordenar por proximidad al 15/09
    5. Crear la entidad Game asociada al lobby
    """
    try:
        # 1. Buscar el lobby
        lobby = db.query(models.Lobby).filter(models.Lobby.lobby_id == lobby_id).first()
        if not lobby:
            return {"success": False, "message": "Lobby no encontrado"}
        
        initiator_player = db.query(models.Player).filter(
            models.Player.user_id == user_id,
            models.Player.lobby_id == lobby_id
        ).first()
        
        if not initiator_player:
            return {"success": False, "message": "Usuario no encontrado en el lobby"}

        # Ahora comparamos el Player ID (lobby_owner) con el Player ID del iniciador
        if lobby.lobby_owner != initiator_player.player_id:
            return {"success": False, "message": "No tienes permiso para iniciar la partida (No eres el dueño)"}
        
        # 3. Verificar que hay jugadores (mínimo 2 y máximo 6)
        players_in_lobby = db.query(models.Player).filter(
            models.Player.lobby_id == lobby_id
        ).all()
        
        player_count = len(players_in_lobby)
        if player_count < 2:
            return {"success": False, "message": "Se necesitan al menos 2 jugadores para iniciar"}
        if player_count > 6:
            return {"success": False, "message": "Máximo 6 jugadores permitidos"}
            
        # 4. Obtener información de usuarios y calcular proximidad al 15/09
        players_with_proximity = []
        target_day = 15
        target_month = 9
        
        for player in players_in_lobby:
            user = db.query(models.User).filter(models.User.user_id == player.user_id).first()
            if user and user.birthday:
                # Extraer día y mes del objeto Date (ignoramos el año)
                birth_day = user.birthday.day
                birth_month = user.birthday.month
                
                # Calcular distancia al 15/09
                days_difference = calculate_proximity(birth_day, birth_month, target_day, target_month)
                
                players_with_proximity.append({
                    'player_id': player.player_id,
                    'user_name': user.user_name,
                    'birthday': user.birthday,
                    'proximity': days_difference,
                    'birth_month': birth_month,  # Para desempate
                    'birth_day': birth_day       # Para desempate
                })
            else:
                # Si no tiene cumpleaños, usar máxima proximidad
                players_with_proximity.append({
                    'player_id': player.player_id,
                    'user_name': user.user_name if user else "Unknown",
                    'birthday': None,
                    'proximity': 365,  # Máxima distancia
                    'birth_month': 13,  # Para que vaya último
                    'birth_day': 32     # Para que vaya último
                })
        
        # 5. Ordenar por proximidad y luego por fecha como desempate
        players_with_proximity.sort(key=lambda x: (
            x['proximity'], 
            x['birth_month'], 
            x['birth_day']
        ))
        
        player_order = [player['player_id'] for player in players_with_proximity]

        # 6. Crear la partida con id único
        game_id = random.randint(1000, 9999)
        
        new_game = models.Game(
            game_id=game_id,
            game_name=f"Partida de {lobby.lobby_name}",
            player_order=json.dumps(player_order),  # "[]" o "[1,2,3]"
            current_turn=player_order[0] if player_order else 0,
            main_deck="[]",  # Mazo principal vacío al inicio
            discard_deck="[]"  # Mazo de descarte vacío al inicio
        )
        db.add(new_game)
        
        # Actualizar players para asociarlos al juego
        for player in players_in_lobby:
            player.game_id = game_id
            player.lobby_id = None

        #Eliminar el lobby después de crear la partida
        db.delete(lobby)
        
        db.commit()
        
        response_data = {
            "success": True, 
            "message": "Partida iniciada exitosamente", 
            "game_id": game_id,
            "lobby_info": {
                "lobby_owner": lobby.lobby_owner,
                "player_amount": lobby.player_amount,
                "lobby_name": lobby.lobby_name,
                "lobby_id": lobby.lobby_id
            },
            "player_order": [{
                "player_id": p['player_id'],
                "user_name": p['user_name'],
                "birthday": p['birthday'].strftime('%d/%m'),
                "proximity_days": p['proximity']
            } for p in players_with_proximity]
        }
        
        return response_data
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al iniciar partida: {str(e)}"}

def calculate_proximity(birth_day, birth_month, target_day=15, target_month=9):
    """
    Calcula la proximidad en días al 15/09 considerando la circularidad del año.
    """
    # Días por mes (no bisiesto) - CORREGIDO
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Calcular día del año para la fecha de nacimiento
    # Sumar días de meses completos ANTES del mes actual
    birth_doy = sum(days_in_month[:birth_month-1]) + birth_day
    
    # Calcular día del año para el target (15/09)
    target_doy = sum(days_in_month[:target_month-1]) + target_day
    
    # Calcular ambas posibles distancias
    diff1 = abs(birth_doy - target_doy)  # Distancia directa
    diff2 = 365 - diff1  # Distancia circular
    
    # Retornar la menor
    return min(diff1, diff2)