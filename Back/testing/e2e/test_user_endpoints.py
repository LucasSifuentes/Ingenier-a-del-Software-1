import os
#  BASE DE DATOS ESPECÍFICA PARA TESTS
os.environ["TESTING"] = "1"
import pytest
from datetime import date
from fastapi.testclient import TestClient

from src.main import app
from src.database.models import User
from src.database.db import SessionLocal, init_db




from src.settings import settings


@pytest.fixture(autouse=True)
def clear_db():
    #  Inicializar BD de testing
    init_db()
    
    session = SessionLocal()
    try:
        # Limpiar todos los datos
        session.query(User).delete()
        session.commit()

        # Crear datos de prueba CONTROLADOS
        users = [
            User(user_name="ana_garcia", birthday=date(2000, 3, 15)),
            User(user_name="carlos_lopez", birthday=date(1995, 7, 22)),
            User(user_name="maria_martinez", birthday=date(1998, 11, 10)),
        ]
        session.add_all(users)
        session.commit()
    finally:
        session.close()

    yield  # Se ejecutan los tests aquí

    # Limpieza final opcional
    session = SessionLocal()
    try:
        session.query(User).delete()
        session.commit()
    finally:
        session.close()

#para probar los enpoints sin levantar el servidor
client = TestClient(app)


def test_create_user_returns_201():
    """Test que crear usuario retorna 201 (CREATED)"""
    response = client.post(
        "/users/register",  
        json={
            "user_name": "nuevo_usuario",
            "birthday": "2000-01-01"
        }
    )
    assert response.status_code == 201
    assert "user_id" in response.json()
    assert response.json()["user_name"] == "nuevo_usuario"


def test_create_user_returns_422_if_missing_user_name():
    """Test que crear usuario sin user_name retorna 422"""
    response = client.post(
        "/users/register",
        json={
            "birthday": "2000-01-01"
        }
    )
    assert response.status_code == 422


def test_create_user_returns_422_if_missing_birthday():
    """Test que crear usuario sin birthday retorna 422"""
    response = client.post(
        "/users/register", 
        json={
            "user_name": "nuevo_usuario"
        }
    )
    assert response.status_code == 422


def test_create_user_returns_422_if_invalid_birthday_format():
    """Test que crear usuario con birthday inválido retorna 422"""
    response = client.post(
        "/users/register",
        json={
            "user_name": "nuevo_usuario",
            "birthday": "no-es-una-fecha"
        }
    )
    assert response.status_code == 422


def test_get_user_by_id_returns_200():
    """Test que obtener usuario por ID existente retorna 200"""
    response = client.get("/users/1")
    assert response.status_code == 200
    assert "user_id" in response.json()
    assert response.json()["user_name"] == "ana_garcia"


def test_get_user_by_id_returns_404_if_user_not_found():
    """Test que obtener usuario por ID inexistente retorna 404"""
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Usuario no encontrado"}


def test_get_user_by_id_returns_422_if_invalid_user_id():
    """Test que obtener usuario con ID inválido retorna 422"""
    response = client.get("/users/not-a-number")
    assert response.status_code == 422