import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app
from database import Base, get_db, User
from auth import hash_password

# Konfiguracja testowej bazy danych
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Nadpisanie zależności bazy danych na potrzeby testów
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Tworzenie tabel przed testami [cite: 162]
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Dodanie testowego admina do bazy 
    if not db.query(User).filter(User.username == "testadmin").first():
        admin = User(
            username="testadmin",
            hashed_password=hash_password("admin123"),
            roles=["ROLE_ADMIN"],
        )
        db.add(admin)
        db.commit()
    db.close()
    yield
    # Usuwanie bazy po testach
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def auth_token():
    # Pobranie tokena JWT niezbędnego do zabezpieczonych endpointów 
    response = client.post(
        "/login", json={"username": "testadmin", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# --- TESTY DLA MOVIES (CRUD) ---


def test_movies_crud(headers):
    # 1. CREATE (POST) - status 201 
    movie_data = {"movieId": 999, "title": "Test Movie", "genres": "Action|Sci-Fi"}
    res_post = client.post("/movies", json=movie_data, headers=headers)
    assert res_post.status_code == 201

    # 2. READ (GET item) - status 200
    res_get = client.get("/movies/999", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["title"] == "Test Movie"

    # 3. UPDATE (PUT) - weryfikacja zmiany w bazie 
    updated_data = {"title": "Updated Title", "genres": "Drama"}
    res_put = client.put("/movies/999", json=updated_data, headers=headers)
    assert res_put.status_code == 200
    assert (
        client.get("/movies/999", headers=headers).json()["title"]
        == "Updated Title"
    )

    # 4. DELETE - usuwanie i weryfikacja 404 
    res_del = client.delete("/movies/999", headers=headers)
    assert res_del.status_code == 204
    assert client.get("/movies/999", headers=headers).status_code == 404[cite:166]


# --- TESTY DLA LINKS (CRUD) ---


def test_links_crud(headers):
    link_data = {"movieId": 888, "imdbId": "tt123", "tmdbId": "456"}
    # CREATE
    assert (
        client.post("/links", json=link_data, headers=headers).status_code
        == 201
    )
    # READ
    assert client.get("/links/888", headers=headers).status_code == 200
    # UPDATE
    assert (
        client.put(
            "/links/888", json={"imdbId": "tt999", "tmdbId": "000"}, headers=headers
        ).status_code
        == 200
    )
    # DELETE
    assert (
        client.delete("/links/888", headers=headers).status_code == 204
    )


# --- TESTY DLA RATINGS (CRUD) ---


def test_ratings_crud(headers):
    rating_data = {"userId": 1, "movieId": 10, "rating": 5.0, "timestamp": 12345}
    # CREATE
    res_post = client.post("/ratings", json=rating_data, headers=headers)
    assert res_post.status_code == 201
    rating_id = 1  # SQLite autoincrement
    # READ
    assert (
        client.get(f"/ratings/{rating_id}", headers=headers).status_code
        == 200
    )
    # UPDATE
    assert (
        client.put(
            f"/ratings/{rating_id}",
            json={"userId": 1, "movieId": 10, "rating": 2.0, "timestamp": 555},
            headers=headers,
        ).status_code
        == 200
    )
    # DELETE
    assert (
        client.delete(f"/ratings/{rating_id}", headers=headers).status_code
        == 204
    )


# --- TESTY DLA TAGS (CRUD) ---


def test_tags_crud(headers):
    tag_data = {"userId": 1, "movieId": 10, "tag": "funny", "timestamp": 123}
    # CREATE
    res_post = client.post("/tags", json=tag_data, headers=headers)
    assert res_post.status_code == 201
    tag_id = 1
    # READ
    assert (
        client.get(f"/tags/{tag_id}", headers=headers).status_code == 200
    )
    # UPDATE
    assert (
        client.put(
            f"/tags/{tag_id}",
            json={"userId": 1, "movieId": 10, "tag": "bored", "timestamp": 999},
            headers=headers,
        ).status_code
        == 200
    )
    # DELETE
    assert (
        client.delete(f"/tags/{tag_id}", headers=headers).status_code
        == 204
    )


# --- TESTY ZABEZPIECZEŃ (AUTH) ---


def test_unauthorized_access():

    response = client.get("/movies")



def test_invalid_token():

    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/movies", headers=headers)
    assert response.status_code == 401
