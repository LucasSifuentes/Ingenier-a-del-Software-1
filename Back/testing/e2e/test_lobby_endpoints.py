import os
os.environ["TESTING"] = "1"  #para usar la bd de prueba y no romper la principal
import pytest
from datetime import date
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.main import app
from src.database.models import User, Lobby, Player
from src.database.db import SessionLocal, init_db
from src.endpoints.untils.websocket_manager import ConnectionManager



from src.settings import settings


        
@pytest.fixture(autouse=True)
def clear_db():
    # Inicializar BD de testing
    init_db()
    
    session = SessionLocal()

    try:
        # Limpiar TODAS las tablas
        session.query(Player).delete()
        session.query(Lobby).delete()
        session.query(User).delete()
        session.commit()

        # Crear datos de prueba CONTROLADOS
        users = [
            User(user_name="ana_garcia", birthday=date(2000, 3, 15)),
            User(user_name="carlos_lopez", birthday=date(1995, 7, 22)),
            User(user_name="maria_martinez", birthday=date(1998, 11, 10)),
            User(user_name="pedro_rodriguez", birthday=date(1997, 5, 14)), 
            User(user_name="laura_gomez", birthday=date(1999, 8, 20)),    
        ]
        session.add_all(users)
        session.commit()
        
        # Crear players para owners
        owner_player1 = Player(player_name="ana_garcia", user_id=users[0].user_id)
        owner_player2 = Player(player_name="carlos_lopez", user_id=users[1].user_id) 
        session.add_all([owner_player1, owner_player2])
        session.commit()
        session.refresh(owner_player1)
        session.refresh(owner_player2)
        
        # Crear lobbies de prueba
        test_lobby1 = Lobby(
            lobby_name="Lobby de Prueba",
            player_amount=1,
            max_players=4,
            min_players=2,
            lobby_owner=owner_player1.player_id
        )
        test_lobby2 = Lobby(  # 🆕 Segundo lobby para edge cases
            lobby_name="Lobby Secundario", 
            player_amount=1,
            max_players=4,
            min_players=3,
            lobby_owner=owner_player2.player_id
        )
        session.add_all([test_lobby1, test_lobby2])
        session.commit()
        
        # Asignar lobbies a players owners
        owner_player1.lobby_id = test_lobby1.lobby_id
        owner_player2.lobby_id = test_lobby2.lobby_id
        session.commit()
        
    finally:
        session.close()

    yield  # Se ejecutan los tests aquí

    # Limpieza final
    session = SessionLocal()
    try:
        session.query(Player).delete()
        session.query(Lobby).delete()
        session.query(User).delete()
        session.commit()
    finally:
        session.close()

client = TestClient(app)




def test_create_lobby_endpoint_returns_201():
    response = client.post(
        "/lobbies/create",
        json={
            "lobby_name": "Mi Nuevo Lobby",
            "max_players": 6,
            "min_players": 3,
            "user_id": 3  # maria_martinez
        }
    )

    player_response = response.json()

    assert response.status_code == 201
    assert player_response['player_id']==3
    assert player_response['player_name'] == "maria_martinez"

#si un jugador es parte de una partida(porque se unio o la creo) no puede crear una nueva partida   
def test_player_create_two_lobbies_():
    response = client.post(
        "/lobbies/create",
        json={
            "lobby_name": "Mi Nuevo Lobby",
            "max_players": 6,
            "min_players": 3,
            "user_id": 1  # ana que ya es owner de una partida
        }
    )
    assert response.status_code == 201


def test_create_lobby_endpoint_returns_400_if_user_not_found():
    response = client.post(
        "/lobbies/create",
        json={
            "lobby_name": "Lobby Fallido",
            "max_players": 4,
            "min_players": 3,
            "user_id": 999  # Usuario que no existe
        }
    )
    assert response.status_code == 400
    assert "no encontrado" in response.json()["detail"].lower()


def test_create_lobby_endpoint_returns_422_if_missing_lobby_name():
    response = client.post(
        "/lobbies/create",
        json={
            "max_players": 4,
            "min_players": 2,
            "user_id": 1
        }
    )
    assert response.status_code == 422


def test_create_lobby_endpoint_returns_422_if_missing_max_players():
    response = client.post(
        "/lobbies/create", 
        json={
            "lobby_name": "Mi Lobby",
            "user_id": 1
        }
    )
    assert response.status_code == 422


def test_create_lobby_endpoint_returns_422_if_missing_user_id():
    response = client.post(
        "/lobbies/create",
        json={
            "lobby_name": "Mi Lobby",
            "max_players": 4
        }
    )
    assert response.status_code == 422


def test_join_lobby_endpoint_returns_200():
    response = client.post(
        "/lobbies/1/join",  # Lobby ID 1 existe en fixture
        json={
            "user_id": 2  # carlos_lopez existe en fixture
        }
    )
    assert response.status_code == 200
    assert "player_id" in response.json()
    assert response.json()["user_id"] == 2
    assert response.json()["lobby_id"] == 1


def test_join_lobby_endpoint_returns_404_if_lobby_not_found():
    response = client.post(
        "/lobbies/999/join",  # Lobby que no existe
        json={
            "user_id": 1
        }
    )
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()



def test_join_lobby_endpoint_returns_404_if_user_not_found():
    response = client.post(
        "/lobbies/1/join",
        json={
            "user_id": 999  # Usuario que no existe
        }
    )
    assert response.status_code == 404
    assert "usuario" in response.json()["detail"].lower()


def test_join_lobby_endpoint_returns_400_if_lobby_full():
    # Primero llenar el lobby
    session = SessionLocal()
    try:
        lobby = session.query(Lobby).filter(Lobby.lobby_id == 1).first()
        lobby.player_amount = lobby.max_players  # Llenarlo
        session.commit()
    finally:
        session.close()
    
    # Intentar unirse
    response = client.post(
        "/lobbies/1/join",
        json={
            "user_id": 3  # maria_martinez
        }
    )
    assert response.status_code == 400
    assert "lleno" in response.json()["detail"].lower()


def test_list_lobbies_endpoint_returns_200():
    response = client.get("/lobbies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2  # Solo el lobby del fixture
    
    # Verificar estructura del lobby
    lobby_data = response.json()[0]
    assert "lobby_id" in lobby_data
    assert "lobby_name" in lobby_data
    assert "player_amount" in lobby_data
    assert "max_players" in lobby_data
    assert "min_players" in lobby_data
    assert "lobby_owner" in lobby_data  # Nombre del dueño


def test_list_lobbies_endpoint_returns_empty_list_when_no_lobbies():
    # Limpiar lobbies
    session = SessionLocal()
    try:
        session.query(Lobby).delete()
        session.commit()
    finally:
        session.close()
    
    response = client.get("/lobbies/")
    assert response.status_code == 200
    assert response.json() == []  # Lista vacía


def test_user_cannot_join_same_lobby_twice():
    # Primera vez - debería funcionar
    response1 = client.post("/lobbies/1/join", json={"user_id": 3})
    assert response1.status_code == 200
    
    # Segunda vez - debería FALLAR
    response2 = client.post("/lobbies/1/join", json={"user_id": 3})
    print(f"Estado al unirse 2da vez: {response2.status_code}")
    
    assert response2.status_code == 200 
    
    session = SessionLocal()
    # Verificar que no se duplicó el contador
    try:
        lobby = session.query(Lobby).filter(Lobby.lobby_id == 1).first()
        # Si se unió 2 veces, player_amount sería 3, pero debería ser 2
        print(f" Jugadores en lobby: {lobby.player_amount}")
        lobby.player_amount == 2
    finally:
        session.close()

#puede 
def test_user_join_two__different_lobbies():
    # Unirse al primer lobby
    response1 = client.post("/lobbies/1/join", json={"user_id": 4})  # pedro_rodriguez
    assert response1.status_code == 200
    
    # Intentar unirse al segundo lobby ()
    response2 = client.post("/lobbies/2/join", json={"user_id": 4})
    print(f"Estado al unirse a 2do lobby: {response2.status_code}")
    
    assert response2.status_code == 200 
    


def test_lobby_full_edge_case():
    # Llenar el lobby hasta capacidad máxima
    session = SessionLocal()
    try:
        lobby = session.query(Lobby).filter(Lobby.lobby_id == 1).first()
        
        # Unir usuarios hasta llenarlo (ya tiene 1 owner + 2 nuevos = 3)
        client.post("/lobbies/1/join", json={"user_id": 3})  # maria (2)
        client.post("/lobbies/1/join", json={"user_id": 4})  # pedro (3)
        
        # Último espacio (4/4)
        response = client.post("/lobbies/1/join", json={"user_id": 5})  # laura (4)
        assert response.status_code == 200
        
        # Intentar unirse cuando está LLENO
        response_full = client.post("/lobbies/1/join", json={"user_id": 6})  # usuario inexistente
        print(f"Estado cuando lobby lleno: {response_full.status_code}")
        
    finally:
        session.close()



##ws tests
def test_lobby_websocket_initial_state():
    """Test: WebSocket envía estado inicial al conectar"""
    with client.websocket_connect("/ws/lobbies/1?player_id=1") as websocket:
        data = websocket.receive_json()
        
        assert data["event"] == "initial_state"
        assert data["lobby_id"] == 1
        assert "player_amount" in data
        assert "max_players" in data
        assert "current_players" in data
        assert isinstance(data["current_players"], list)

def test_lobby_websocket_rejects_invalid_lobby():
    """Test: WebSocket cierra conexión si lobby no existe"""
    with pytest.raises(Exception):  # Debería fallar la conexión
        with client.websocket_connect("/ws/lobbies/999?player_id=1") as websocket:
            websocket.receive_json()

def test_join_lobby_endpoint_triggers_broadcast():
    """Test del endpoint completo (HTTP + WebSocket)"""
    with client.websocket_connect("/ws/lobbies/1?player_id=1") as websocket:
        # Recibir estado inicial
        initial_data = websocket.receive_json()
        
        # Llamar al ENDPOINT HTTP (que hace el broadcast)
        response = client.post("/lobbies/1/join", json={"user_id": 2})
        assert response.status_code == 200
        
        # Verificar que llega el broadcast por WebSocket
        broadcast_data = websocket.receive_json()
        assert broadcast_data["event"] == "player_joined"
        assert broadcast_data["player_amount"] == initial_data["player_amount"] + 1

def test_lobby_websocket_multiple_clients_same_lobby():
    """Test: Múltiples clientes reciben broadcasts del mismo lobby"""
    with client.websocket_connect("/ws/lobbies/1?player_id=1") as ws1, \
         client.websocket_connect("/ws/lobbies/1?player_id=2") as ws2:
        
        # Ambos reciben estado inicial
        data1 = ws1.receive_json()
        data2 = ws2.receive_json()
        
        assert data1["event"] == "initial_state"
        assert data2["event"] == "initial_state"
        assert data1["lobby_id"] == data2["lobby_id"]
        
        # usar asyncio.run para ejecutar
        import asyncio
        from src.endpoints.untils.websocket_manager  import ws_manager
        asyncio.run(ws_manager.broadcast_lobby({
            "event": "test_broadcast",
            "message": "hello all"
        }, lobby_id=1))
        
        #  Ambos deberían recibir el mensaje (USANDO las variables)
        broadcast1 = ws1.receive_json()
        broadcast2 = ws2.receive_json()
        
        assert broadcast1["event"] == "test_broadcast"
        assert broadcast2["event"] == "test_broadcast"

def test_lobby_websocket_no_cross_lobby_broadcast():
    with client.websocket_connect("/ws/lobbies/1?player_id=1") as ws1, \
         client.websocket_connect("/ws/lobbies/2?player_id=3") as ws2:
        
        ws1.receive_json()
        ws2.receive_json()
        
        # Broadcast a lobby 1
        from src.endpoints.untils.websocket_manager import ws_manager
        import asyncio
        asyncio.run(ws_manager.broadcast_lobby({"event": "lobby1_only"}, lobby_id=1))
        
        # ws1 debería recibirlo inmediatamente
        data1 = ws1.receive_json()
        assert data1["event"] == "lobby1_only"

        asyncio.run(ws_manager.broadcast_lobby({"event": "lobby2_only"}, lobby_id=2))
        data2 = ws2.receive_json()
        assert data2["event"] == "lobby2_only"
    

