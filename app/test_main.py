import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import main
from db import init_db

TEST_SQLITE_URL = "sqlite:///:memory:"


test_engine = create_engine(
    TEST_SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Fresh DB and patched engine for every test."""

    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    main.engine = test_engine

    yield


@pytest.fixture
def client():
    """Provides a test client for the FastAPI app."""
    return TestClient(main.app)


def test_lifespan_initializes_db():

    SQLModel.metadata.drop_all(test_engine)

    with TestClient(main.app) as test_client:

        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "games" in tables
        assert "moves" in tables


def test_create_game_default_size(client):
    """Test that a game is created with the default size (3)."""
    response = client.post("/games")
    assert response.status_code == 201
    data = response.json()
    assert data["game_id"] == 1
    assert data["status"] == "IN_PROGRESS"

    assert "2 |" in data["visual_board"]
    assert "0 |" in data["visual_board"]


def test_create_game_custom_size(client):
    """Test creating a 5x5 game."""
    response = client.post("/games?size=5")
    assert response.status_code == 201
    data = response.json()

    assert "4 |" in data["visual_board"]


def test_create_game_invalid_size(client):
    """Test that the API rejects sizes outside 3-10."""
    response = client.post("/games?size=2")
    assert response.status_code == 400
    assert response.json()["detail"] == "Size must be between 3 and 10"


def test_make_move_success(client):
    """Test making a valid move at (0,0) - the bottom left."""
    client.post("/games?size=3")
    response = client.post("/games/1/move", json={"x": 0, "y": 0})

    assert response.status_code == 200
    data = response.json()

    assert "0 | X" in data["visual_board"]

    assert data["move_count"] == 2


def test_make_move_out_of_bounds(client):
    """Test that moving to (5,5) on a 3x3 board fails."""
    client.post("/games?size=3")
    response = client.post("/games/1/move", json={"x": 5, "y": 5})
    assert response.status_code == 400
    assert response.json()["detail"] == "Out of bounds"


def test_make_move_occupied_square(client):
    """Test that you cannot move where someone has already played."""
    client.post("/games?size=3")

    client.post("/games/1/move", json={"x": 1, "y": 1})

    response = client.post("/games/1/move", json={"x": 1, "y": 1})
    assert response.status_code == 409
    assert response.json()["detail"] == "Square occupied"


def test_get_game_history(client):
    """Verify chronological move history."""
    client.post("/games?size=3")
    client.post("/games/1/move", json={"x": 0, "y": 0})

    response = client.get("/games/1/moves")
    assert response.status_code == 200
    moves = response.json()

    assert len(moves) == 2
    assert moves[0]["player"] == "X"
    assert moves[0]["move_number"] == 1
    assert moves[1]["player"] == "O"
    assert moves[1]["move_number"] == 2


def test_list_all_games(client):
    """Verify that multiple games are listed correctly."""
    client.post("/games?size=3")
    client.post("/games?size=4")

    response = client.get("/games")
    assert response.status_code == 200
    assert len(response.json()) == 2
