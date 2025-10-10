import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.db import Base
from src.database import models
from datetime import date
from src.database import models
from src.database.crud import crud_user
from src.schemas import user_schemas


# Engine de SQLite en memoria (no toca tu DB real)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    # Crear engine y tablas
    engine = create_engine(TEST_DATABASE_URL, echo=False, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)

    # Crear sesión
    session = TestingSessionLocal()
    try:
        yield session  # acá corren los tests
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)  # limpia todo después de cada test

@pytest.fixture
def sample_user(db_session):
    """Crea un usuario de prueba en la DB y lo devuelve"""
    user = models.User(user_name="integration_test_user", birthday=date(2000, 1, 1))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user        


def test_create_user_persists_and_returns_user(db_session):
    payload = user_schemas.UserCreateSchema(
        user_name="user_integration",
        birthday=date(1999, 12, 31)
    )

    created = crud_user.create_user(db_session, payload)

    # Verificamos el retorno
    assert created.user_id is not None
    assert created.user_name == "user_integration"

    # Verificamos que esté en la DB
    db_user = db_session.query(type(created)).get(created.user_id)
    assert db_user.user_name == "user_integration"


def test_get_user_returns_existing_user(db_session, sample_user):
    # usamos el fixture sample_user
    found = crud_user.get_user(db_session, sample_user.user_id)

    assert found is not None
    assert found.user_id == sample_user.user_id
    assert found.user_name == "integration_test_user"    


def setup_db():
    from src.database.db import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def test_create_user_exitoso():
    from src.database.crud.crud_user import create_user
    from src.database.models import User
    from src.schemas.user_schemas import UserCreateSchema
    
    db = setup_db()
    
    try:
        user_data = UserCreateSchema(
            user_name="NuevoJugador", 
            birthday=date(1995, 5, 20)
        )
        
        result = create_user(db, user_data)
        
        assert result is not None
        assert result.user_name == "NuevoJugador"
        assert result.birthday == date(1995, 5, 20)
        assert hasattr(result, 'user_id')
        
        # Verificar en base de datos
        user_db = db.query(User).filter(User.user_id == result.user_id).first()
        assert user_db is not None
        assert user_db.user_name == "NuevoJugador"
        
        print("Test crear usuario exitoso")
        
    finally:
        db.close()

def test_create_user_con_nombre_duplicado_exitoso():
    from src.database.crud.crud_user import create_user
    from src.database.models import User
    from src.schemas.user_schemas import UserCreateSchema
    
    db = setup_db()
    test_name = "Milena"
    
    try:
        user_data1 = UserCreateSchema(
            user_name=test_name, 
            birthday=date(1995, 5, 20)
        )
        result1 = create_user(db, user_data1)
        assert result1 is not None
        user_id_1 = result1.user_id
        
        user_data2 = UserCreateSchema(
            user_name=test_name, 
            birthday=date(1990, 1, 1)
        )
        result2 = create_user(db, user_data2)
        
        assert result2 is not None
        user_id_2 = result2.user_id
        
        assert user_id_1 != user_id_2
        
        count = db.query(User).filter(User.user_name == test_name).count()
        assert count == 2
        
        print("Test crear usuario con nombre duplicado")
        
    finally:
        db.close()