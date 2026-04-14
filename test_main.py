import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def auth_headers():
    email = "auth_tester@example.com"
    pwd = "super_secure_password"
    client.post("/auth/register", json={"email": email, "password": pwd})
    res = client.post("/auth/login", data={"username": email, "password": pwd})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_user():
    user_data = {
        "email": "unique_user@example.com",
        "password": "strong_password_123"  # Довжина > 8
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]


def test_register_duplicate_user():
    user_data = {
        "email": "duplicate@example.com",
        "password": "password_long_enough"  # Довжина > 8
    }
    # Перша реєстрація
    client.post("/auth/register", json=user_data)
    # Друга реєстрація
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 400
    assert response.json()["detail"] == "This email is already taken"


def test_login_success():
    user_data = {
        "email": "login_test@example.com",
        "password": "secure_password_888"
    }
    client.post("/auth/register", json=user_data)

    # Для логіну використовуємо data= (OAuth2Form)
    response = client.post("/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_board(auth_headers):
    # auth_headers автоматично реєструє auth_user@test.com
    response = client.post("/boards", json={"title": "Test Board"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Board"


def test_get_boards(auth_headers):
    # Створюємо одну дошку
    client.post("/boards", json={"title": "Board 1"}, headers=auth_headers)
    # Отримуємо список
    response = client.get("/boards", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Board 1"