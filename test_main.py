import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from main import app
from db import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db: Session = TestSessionLocal()
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

@pytest.fixture
def create_board(auth_headers):
    board = client.post("/boards", json={"title": "Test Board"}, headers=auth_headers)
    return board

@pytest.fixture
def create_list(auth_headers, create_board):
    board_id = create_board.json()['id']
    response = client.post(
        f'/boards/{board_id}/lists',
        json={'title': 'Test List', 'position': 100.0},
        headers=auth_headers
    )
    return response

class TestUser:
    def test_register_user(self):
        user_data = {
            "email": "unique_user@example.com",
            "password": "strong_password_123"  # Довжина > 8
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        assert response.json()["email"] == user_data["email"]


    def test_register_duplicate_user(self):
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


    def test_login_success(self):
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

class TestBoard:
    def test_create_board(self, auth_headers):
        # auth_headers автоматично реєструє auth_user@test.com
        response = client.post("/boards", json={"title": "Test Board"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Test Board"


    def test_get_boards(self, auth_headers):
        # Створюємо одну дошку
        client.post("/boards", json={"title": "Board 1"}, headers=auth_headers)
        # Отримуємо список
        response = client.get("/boards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Board 1"

class TestList:
    def test_create_list(self,auth_headers, create_board):
        board_id = create_board.json()['id']

        response = client.post(f'/boards/{board_id}/lists',
            json={'title': 'List 1', 'position' : 100.0},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()['title'] == 'List 1'

    def test_update_list(self, auth_headers, create_board, create_list):
        board_id = create_board.json()['id']
        list_id = create_list.json()['id']
        response = client.patch(
            f'/boards/{board_id}/lists/{list_id}',
                json={'title': 'List Test', 'position': 200.0},
                headers=auth_headers
                )
        assert response.status_code == 200
        assert response.json()['title'] == 'List Test'


class TestCard:
    def test_create_card(self, auth_headers, create_board, create_list):
        # Дістаємо обидва ID
        board_id = create_board.json()['id']
        list_id = create_list.json()['id']

        card_data = {
            "title": "Налаштувати CI/CD",
            "description": "Додати GitHub Actions",
            "position": 1.0
        }

        # Використовуємо правильний шлях з двома ID
        response = client.post(
            f"/boards/{board_id}/lists/{list_id}/cards",
            json=card_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == card_data["title"]
        assert data["list_id"] == list_id

    def test_card_empty_description(self, auth_headers, create_board, create_list):
        board_id = create_board.json()['id']
        list_id = create_list.json()['id']

        card_data = {
            "title": "Картка без опису",
            "description": "   ",  # Перевірка на пробіли
            "position": 2.0
        }

        response = client.post(
            f"/boards/{board_id}/lists/{list_id}/cards",
            json=card_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["description"] is None

    def test_get_cards(self, auth_headers, create_board, create_list):
        board_id = create_board.json()['id']
        list_id = create_list.json()['id']

        client.post(f"/boards/{board_id}/lists/{list_id}/cards", json={"title": "C1", "position": 1.0},
                    headers=auth_headers)
        client.post(f"/boards/{board_id}/lists/{list_id}/cards", json={"title": "C2", "position": 2.0},
                    headers=auth_headers)

        response = client.get(f"/boards/{board_id}/lists/{list_id}/cards", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_card(self, auth_headers, create_board, create_list):
        board_id = create_board.json()['id']
        list_id = create_list.json()['id']

        # Створюємо картку
        card_res = client.post(
            f"/boards/{board_id}/lists/{list_id}/cards",
            json={"title": "Стара назва", "position": 1.0},
            headers=auth_headers
        )
        card_id = card_res.json()["id"]

        # Оновлюємо картку
        # УВАГА: Якщо твій PATCH маршрут теж містить board_id та list_id, шлях буде таким:
        response = client.patch(
            f"/boards/{board_id}/lists/{list_id}/cards/{card_id}",
            json={"title": "Нова назва", "position": 5.5},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Нова назва"

    def test_delete_card(self, auth_headers, create_board, create_list):
        board_id = create_board.json()['id']
        list_id = create_list.json()['id']

        card_res = client.post(
            f"/boards/{board_id}/lists/{list_id}/cards",
            json={"title": "Видалити мене", "position": 1.0},
            headers=auth_headers
        )
        card_id = card_res.json()["id"]

        # Видаляємо картку
        delete_res = client.delete(
            f"/boards/{board_id}/lists/{list_id}/cards/{card_id}",
            headers=auth_headers
        )
        assert delete_res.status_code in (200, 204)