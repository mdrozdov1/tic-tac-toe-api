import time
from contextlib import asynccontextmanager
from typing import List

import utils
from config import APP_NAME
from db import SQLITE_URL, GameBase, GameOutput, Games, MoveHistoryItem, init_db
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from logger import logger
from models import GameStatus, MoveInput
from services import game_service
from sqlmodel import Session, create_engine, select

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(engine)
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log_str = f"Validation error on {request.method} {request.url.path}: {exc.errors()}"
    logger.warning(log_str)
    return PlainTextResponse(status_code=400, content=log_str)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"← {request.method} {request.url.path} "
        f"{response.status_code} ({process_time:.2f}ms)"
    )

    return response


@app.post("/games", response_model=GameOutput, status_code=201)
def create_game(game: GameBase):
    """Create a new game of Noughts and Crosses."""
    if game.board_size < 3 or game.board_size > 10:
        raise HTTPException(status_code=400, detail="Size must be between 3 and 10")

    with Session(engine) as session:
        new_game = Games.model_validate(game)
        session.add(new_game)
        session.commit()
        session.refresh(new_game)
        assert new_game.id is not None

        logger.info(f"Game #{new_game.id} created (size={game.board_size})")

        return GameOutput(
            id=new_game.id,
            status=new_game.status,
            created_at=new_game.created_at,
            move_count=0,
            visual_board=utils.format_board_ascii(
                [["."] * game.board_size for _ in range(game.board_size)]
            ),
        )


@app.post("/games/{game_id}/moves/", response_model=GameOutput)
def make_move(game_id: int, move: MoveInput):
    """
    Make a move as Player X.
    The computer (O) will immediately respond with a random move.
    Coordinates are 0-indexed (0, 1, 2, ...).
    """
    with Session(engine) as session:
        game = session.get(Games, game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        if game.status != GameStatus.IN_PROGRESS:
            board = utils.get_board_state(game)
            return GameOutput(
                id=game_id,
                status=GameStatus(game.status),
                created_at=game.created_at,
                move_count=len(game.moves),
                visual_board=utils.format_board_ascii(board),
            )

        try:
            board = game_service.process_move(game, move.x, move.y, session)
        except ValueError as e:
            detail = str(e)
            status_code = 409 if detail == "Square occupied" else 400
            raise HTTPException(status_code=status_code, detail=detail)

        session.add(game)
        session.commit()
        session.refresh(game)

        logger.info(
            f"Game #{game_id}: X played ({move.x},{move.y}), status={game.status}"
            + (f", winner={game.winner}" if game.winner else "")
        )

        return GameOutput(
            id=game_id,
            status=GameStatus(game.status),
            created_at=game.created_at,
            move_count=len(game.moves),
            visual_board=utils.format_board_ascii(board),
        )


@app.get("/games/{game_id}/moves/", response_model=List[MoveHistoryItem])
def get_game_moves(game_id: int):
    """View all moves in a game, chronologically ordered."""
    with Session(engine) as session:
        game = session.get(Games, game_id)

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        return sorted(game.moves, key=lambda m: m.move_number)


@app.get("/games", response_model=List[GameOutput])
def list_games():
    """List all games with their current board state."""
    with Session(engine) as session:
        games = session.exec(select(Games)).all()
        return [
            GameOutput(
                id=game.id,
                status=GameStatus(game.status),
                created_at=game.created_at,
                move_count=len(game.moves),
                visual_board=utils.format_board_ascii(utils.get_board_state(game)),
            )
            for game in games
            if game.id is not None
        ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
