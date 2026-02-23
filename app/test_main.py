import main
import pytest
import utils
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

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


@pytest.fixture
def new_game(client):
    """Creates a fresh 3x3 game and returns its JSON response."""
    return client.post("/games", json={"board_size": 3}).json()


def test_lifespan_initializes_db():
    SQLModel.metadata.drop_all(test_engine)

    with TestClient(main.app) as test_client:
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "games" in tables
        assert "moves" in tables


def test_create_game_default_size(client):
    """Test that a game is created with the default size (3)."""
    response = client.post("/games", json={})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "IN_PROGRESS"
    assert "2 |" in data["visual_board"]
    assert "0 |" in data["visual_board"]


def test_create_game_custom_size(client):
    """Test creating a 5x5 game."""
    response = client.post("/games", json={"board_size": 5})
    assert response.status_code == 201
    assert "4 |" in response.json()["visual_board"]


def test_create_game_invalid_size(client):
    """Test that the API rejects sizes outside 3-10."""
    response = client.post("/games", json={"board_size": 2})
    assert response.status_code == 400
    assert response.json()["detail"] == "Size must be between 3 and 10"


def test_make_move_success(client, new_game):
    """Test making a valid move at (0,0) - the bottom left."""
    response = client.post(f"/games/{new_game['id']}/moves/", json={"x": 0, "y": 0})

    assert response.status_code == 200
    data = response.json()
    assert "0 | X" in data["visual_board"]
    assert data["move_count"] == 2


def test_make_move_out_of_bounds(client, new_game):
    """Test that moving to (5,5) on a 3x3 board fails."""
    response = client.post(f"/games/{new_game['id']}/moves/", json={"x": 5, "y": 5})
    assert response.status_code == 400
    assert response.json()["detail"] == "Out of bounds"


def test_make_move_negative_coordinates(client, new_game):
    """Test that negative coordinates are rejected by the model validator."""
    response = client.post(f"/games/{new_game['id']}/moves/", json={"x": -1, "y": 0})
    assert response.status_code == 422


def test_make_move_occupied_square(client, new_game):
    """Test that you cannot move where someone has already played."""
    game_id = new_game["id"]
    client.post(f"/games/{game_id}/moves/", json={"x": 1, "y": 1})

    response = client.post(f"/games/{game_id}/moves/", json={"x": 1, "y": 1})
    assert response.status_code == 409
    assert response.json()["detail"] == "Square occupied"


def test_ai_move_appears_on_board(client, new_game):
    """Verify that O's move is rendered on the board after player's turn."""
    response = client.post(f"/games/{new_game['id']}/moves/", json={"x": 0, "y": 0})
    data = response.json()
    assert "X" in data["visual_board"]
    assert "O" in data["visual_board"]
    assert data["move_count"] == 2


def test_game_over_returns_board_not_string(client, new_game, monkeypatch):
    """After a game ends, further move requests return the actual board, not a placeholder."""
    o_moves = iter([(2, 0), (2, 1)])
    monkeypatch.setattr(utils, "get_ai_move", lambda x, y: next(o_moves))

    game_id = new_game["id"]
    client.post(f"/games/{game_id}/moves/", json={"x": 0, "y": 0})
    client.post(f"/games/{game_id}/moves/", json={"x": 0, "y": 1})
    win_resp = client.post(f"/games/{game_id}/moves/", json={"x": 0, "y": 2})
    assert win_resp.json()["status"] == "X_WON"

    post_game = client.post(f"/games/{game_id}/moves/", json={"x": 1, "y": 1})
    assert post_game.status_code == 200
    data = post_game.json()
    assert data["status"] == "X_WON"
    assert "|" in data["visual_board"]
    assert "X" in data["visual_board"]


def test_draw_condition(client, new_game, monkeypatch):
    """A fully filled board with no winner is detected as DRAW."""
    o_moves = iter([(1, 2), (2, 1), (0, 0), (1, 1)])
    monkeypatch.setattr(utils, "get_ai_move", lambda x, y: next(o_moves))

    game_id = new_game["id"]
    client.post(f"/games/{game_id}/moves/", json={"x": 0, "y": 2})
    client.post(f"/games/{game_id}/moves/", json={"x": 0, "y": 1})
    client.post(f"/games/{game_id}/moves/", json={"x": 2, "y": 2})
    client.post(f"/games/{game_id}/moves/", json={"x": 1, "y": 0})
    response = client.post(f"/games/{game_id}/moves/", json={"x": 2, "y": 0})

    assert response.status_code == 200
    assert response.json()["status"] == "DRAW"


def test_get_game_history(client, new_game):
    """Verify chronological move history."""
    game_id = new_game["id"]
    client.post(f"/games/{game_id}/moves/", json={"x": 0, "y": 0})

    response = client.get(f"/games/{game_id}/moves")
    assert response.status_code == 200
    moves = response.json()

    assert len(moves) == 2
    assert moves[0]["player"] == "X"
    assert moves[0]["move_number"] == 1
    assert moves[1]["player"] == "O"
    assert moves[1]["move_number"] == 2


def test_list_all_games(client):
    """Verify that multiple games are listed correctly."""
    client.post("/games", json={"board_size": 3})
    client.post("/games", json={"board_size": 4})

    response = client.get("/games")
    assert response.status_code == 200
    assert len(response.json()) == 2
