import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, User, Lobby, Player
from src.database.crud import crud_lobby

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DATABASE_URL, echo=False, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(db_session):
    user = User(user_name="test_user", birthday=date(2000, 1, 1))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_lobby(db_session, sample_user):
    """Lobby de prueba con owner"""
    # Primero crear player para el owner
    owner_player = Player(
        player_name=sample_user.user_name,
        user_id=sample_user.user_id
    )
    db_session.add(owner_player)
    db_session.commit()
    db_session.refresh(owner_player)
    
    # Crear lobby
    lobby = Lobby(
        lobby_name="Test Lobby",
        player_amount=1,
        max_players=4,
        min_players=2,
        lobby_owner=owner_player.player_id
    )
    db_session.add(lobby)
    db_session.commit()
    db_session.refresh(lobby)
    
    # Asignar lobby al player
    owner_player.lobby_id = lobby.lobby_id
    db_session.commit()
    
    return lobby

def test_create_lobby_persists_in_db(db_session, sample_user):
    # Ejecutar
    result = crud_lobby.create_lobby(
        db=db_session,
        lobby_name="Lobby de Integración", 
        max_players=6,
        min_players=2,
        lobby_owner=sample_user.user_id
    )
    
    # Verificar resultado
    assert result["success"] == True
    assert "lobby_id" in result
    
    # Verificar que el lobby existe en BD
    lobby_from_db = db_session.query(Lobby).filter(Lobby.lobby_id == result["lobby_id"]).first()
    assert lobby_from_db is not None
    assert lobby_from_db.lobby_name == "Lobby de Integración"
    assert lobby_from_db.max_players == 6
    assert lobby_from_db.min_players == 2
    assert lobby_from_db.player_amount == 1  # Solo el owner
    
    # Verificar que el player owner existe
    player_from_db = db_session.query(Player).filter(Player.lobby_id == result["lobby_id"]).first()
    assert player_from_db is not None
    assert player_from_db.user_id == sample_user.user_id

def test_join_lobby_increases_player_count(db_session, sample_lobby):
    # Crear otro usuario para unirse
    new_user = User(user_name="new_user", birthday=date(1999, 5, 15))
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    
    # Verificar estado inicial
    initial_count = sample_lobby.player_amount
    
    # Ejecutar join
    result = crud_lobby.join_lobby(
        db=db_session,
        lobby_id=sample_lobby.lobby_id,
        user_id=new_user.user_id
    )
    
    # Verificar resultado
    new_player = result['player']

    assert new_player.user_id == new_user.user_id
    assert new_player.lobby_id == sample_lobby.lobby_id
    
    # Verificar que se actualizó el contador en BD
    db_session.refresh(sample_lobby)  # Recargar desde BD
    assert sample_lobby.player_amount == initial_count + 1
    
    # Verificar que el player está en BD
    player_from_db = db_session.query(Player).filter(Player.player_id == new_player.player_id).first()
    assert player_from_db is not None

def test_get_lobbies_returns_all_lobbies(db_session, sample_lobby):
    # Crear otro lobby
    another_user = User(user_name="user2", birthday=date(1998, 3, 20))
    db_session.add(another_user)
    db_session.commit()
    db_session.refresh(another_user)
    
    another_player = Player(player_name="user2", user_id=another_user.user_id)
    db_session.add(another_player)
    db_session.commit()
    db_session.refresh(another_player)
    
    another_lobby = Lobby(
        lobby_name="Otro Lobby",
        player_amount=1,
        max_players=4,
        lobby_owner=another_player.player_id
    )
    db_session.add(another_lobby)
    db_session.commit()
    
    # Ejecutar
    lobbies = crud_lobby.get_lobbies(db_session)
    
    # Verificar
    assert len(lobbies) == 2  # sample_lobby + another_lobby
    
    # Verificar estructura de datos (tuplas con join)
    for lobby_data in lobbies:
        assert len(lobby_data) == 6  # (lobby_id, lobby_name, player_amount, max_players,min_players lobby_owner_name)
        assert lobby_data[1] in ["Test Lobby", "Otro Lobby"]  # lobby_name

def test_join_lobby_fails_when_full(db_session, sample_lobby):
    # Llenar el lobby
    sample_lobby.player_amount = sample_lobby.max_players
    db_session.commit()
    
    # Crear usuario que intenta unirse
    new_user = User(user_name="full_user", birthday=date(1997, 8, 10))
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    
    # Verificar que lanza false
    result = crud_lobby.join_lobby(
        db=db_session,
        lobby_id=sample_lobby.lobby_id,
        user_id=new_user.user_id
    )
    # Verificar mensaje de error
    assert result['success'] == False
    assert result['message'] == 'Lobby lleno'

def test_create_lobby_fails_with_invalid_user(db_session):
    result = crud_lobby.create_lobby(
        db=db_session,
        lobby_name="Lobby Fallido",
        max_players=4,
        min_players=2,
        lobby_owner=999  # Usuario que no existe
    )
    
    assert result["success"] == False
    assert "no encontrado" in result["message"].lower()



def test_create_lobby_concurrente():
    """Test creación concurrente de lobbies por diferentes usuarios"""
    from src.database.crud.crud_lobby import create_lobby
    from src.database.models import User, Lobby
    from src.database.db import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Crear múltiples usuarios
        users = [
            User(user_id=1, user_name="User1", birthday=date(2000, 1, 1)),
            User(user_id=2, user_name="User2", birthday=date(2000, 2, 2)),
            User(user_id=3, user_name="User3", birthday=date(2000, 3, 3))
        ]
        db.add_all(users)
        db.commit()
        
        # Crear lobbies concurrentemente (en secuencia para el test)
        lobby_ids = []
        for i, user in enumerate(users):
            result = create_lobby(db, f"Lobby {i+1}", 4, 2, user.user_id)
            assert result["success"] == True
            lobby_ids.append(result["lobby_id"])
        
        # Verificar que todos los lobbies son únicos
        assert len(set(lobby_ids)) == len(lobby_ids)
        
        # Verificar que cada usuario tiene su lobby
        lobbies = db.query(Lobby).all()
        assert len(lobbies) == 3
        
        print(" Test creación concurrente")
        
    finally:
        db.close()

#------------------- test para get_lobbies ----------------------

def setup_db_with_users_and_lobbies(db_session, num_lobbies=3):
    users = []
    for i in range(num_lobbies):
        user = User(user_id=i+1, user_name=f"User{i+1}", birthday=date(2000, 1, 1+i))
        db_session.add(user)
        users.append(user)
    db_session.commit()
    
    lobby_ids = []
    for i in range(num_lobbies):
        result = create_lobby(db_session, f"Sala {i+1}", max_players=4, owner_id=users[i].user_id)
        lobby_ids.append(result["lobby_id"])
        
    return lobby_ids

def test_get_lobbies_vacia():
    from src.database.crud.crud_lobby import get_lobbies
    from src.database.db import Base
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        lobbies = get_lobbies(db)
        
        assert isinstance(lobbies, list)
        assert len(lobbies) == 0
        
        print("Test get_lobbies vacía")
        
    finally:
        db.close()

def test_get_lobbies_con_contenido():
    from src.database.crud.crud_lobby import create_lobby, get_lobbies 
    from src.database.models import User, Lobby
    from src.database.db import Base
    
    def setup_db_with_users_and_lobbies(db_session, num_lobbies=3):
        users = []
        for i in range(num_lobbies):
            user = User(user_id=i+1, user_name=f"User{i+1}", birthday=date(2000, 1, 1+i))
            db_session.add(user)
            users.append(user)
        db_session.commit()
        
        lobby_ids = []
        for i in range(num_lobbies):
            result = create_lobby(db_session, f"Sala {i+1}", 4, 2, users[i].user_id)
            lobby_ids.append(result["lobby_id"])
            
        return lobby_ids

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        lobby_ids = setup_db_with_users_and_lobbies(db, num_lobbies=3)
        
        lobbies = get_lobbies(db)
        
        assert isinstance(lobbies, list)
        assert len(lobbies) == 3

        for lobby in lobbies:
            assert hasattr(lobby, 'lobby_id')
            assert hasattr(lobby, 'lobby_name')
            assert hasattr(lobby, 'player_amount')
            assert hasattr(lobby, 'max_players')
            assert hasattr(lobby, 'min_players')
            assert hasattr(lobby, 'lobby_owner')  

        nombres = [l.lobby_name for l in lobbies]
        ids_obtenidos = [l.lobby_id for l in lobbies]
        
        assert "Sala 1" in nombres
        assert "Sala 3" in nombres
        assert all(id in ids_obtenidos for id in lobby_ids)
        
        for lobby in lobbies:
            assert lobby.player_amount == 1 
            
        print("Test get_lobbies con contenido")
            
    finally:
        db.close()

