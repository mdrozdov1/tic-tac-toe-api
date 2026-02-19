import random
import time
from contextlib import asynccontextmanager
from typing import List

import utils
from db import SQLITE_URL, Games, Moves, init_db
from fastapi import FastAPI, HTTPException, Request
from logger import logger
from models import *
from sqlmodel import Session, create_engine, select

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(engine)
    yield


app = FastAPI(title="Ethyca Tic-Tac-Toe", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}ms"

    log_dict = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration": formatted_process_time,
    }

    logger.info(
        f"Request: {log_dict['method']} {log_dict['path']} "
        f"completed in {log_dict['duration']} with status {log_dict['status_code']}"
    )

    return response


@app.post("/games", response_model=GameOutput, status_code=201)
def create_game(size: int = 3):
    """Create a new game of Noughts and Crosses."""
    if size < 3 or size > 10:
        raise HTTPException(status_code=400, detail="Size must be between 3 and 10")

    with Session(engine) as session:
        new_game = Games(board_size=size, status=GameStatus.IN_PROGRESS.value)
        session.add(new_game)
        session.commit()
        session.refresh(new_game)

        return GameOutput(
            game_id=new_game.id,
            status=GameStatus(new_game.status),
            created_at=new_game.created_at,
            move_count=0,
            visual_board=utils.format_board_ascii([["."] * size for _ in range(size)]),
        )


@app.post("/games/{game_id}/move", response_model=GameOutput)
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

        if game.status != GameStatus.IN_PROGRESS.value:
            return GameOutput(
                game_id=game_id,
                status=GameStatus(game.status),
                created_at=game.created_at,
                move_count=0,
                visual_board="Game Over",
            )

        board = utils.get_board_state(game)
        mapped_y = (game.board_size - 1) - move.y

        if not (0 <= move.x < game.board_size and 0 <= move.y < game.board_size):
            raise HTTPException(status_code=400, detail="Out of bounds")
        if board[mapped_y][move.x] != ".":
            raise HTTPException(status_code=409, detail="Square occupied")

        # Record User Move
        new_move = Moves(
            game_id=game.id,
            player=Player.X,
            x=move.x,
            y=move.y,
            move_number=len(game.moves) + 1,
        )
        session.add(new_move)
        board[mapped_y][move.x] = Player.X.value

        # Check if User Won
        winner = utils.check_win(board, game.board_size)

        if winner:
            game.status = GameStatus.X_WON
            game.winner = Player.X
        elif utils.is_board_full(board):
            game.status = GameStatus.DRAW
        else:
            # Computer Move
            available_moves = [
                (r, c)
                for r in range(game.board_size)
                for c in range(game.board_size)
                if board[r][c] == "."
            ]
            if available_moves:
                comp_y, comp_x = random.choice(available_moves)  # Random AI
                comp_mapped_y = (game.board_size - 1) - comp_y

                ai_move = Moves(
                    game_id=game.id,
                    player=Player.O.value,
                    x=comp_x,
                    y=comp_mapped_y,
                    move_number=len(game.moves) + 2,
                )
                session.add(ai_move)
                board[comp_y][comp_x] = Player.O.value

                # Check if Computer Won
                if utils.check_win(board, game.board_size):
                    game.status = GameStatus.O_WON
                    game.winner = Player.O
                elif utils.is_board_full(board):
                    game.status = GameStatus.DRAW

        session.add(game)
        session.commit()
        session.refresh(game)

        return GameOutput(
            game_id=game.id,
            status=GameStatus(game.status),
            created_at=game.created_at,
            move_count=len(game.moves),
            visual_board=utils.format_board_ascii(board),
        )


@app.get("/games/{game_id}/moves", response_model=List[MoveHistoryItem])
def get_game_moves(game_id: int):
    """View all moves in a game, chronologically ordered."""
    with Session(engine) as session:
        game = session.get(Games, game_id)

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        sorted_moves = sorted(game.moves, key=lambda m: m.move_number)

        return sorted_moves


@app.get("/games", response_model=List[GameOutput])
def list_games():
    with Session(engine) as session:
        games = session.exec(select(Games)).all()
        return [
            GameOutput(
                game_id=game.id,
                status=GameStatus(game.status),
                created_at=game.created_at,
                move_count=len(game.moves),
                visual_board=utils.format_board_ascii(utils.get_board_state(game)),
            )
            for game in games
        ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
