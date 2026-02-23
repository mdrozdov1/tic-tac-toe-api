from datetime import datetime
from typing import List, Optional

from models import GameStatus, Player
from sqlalchemy.engine import Engine
from sqlmodel import Field, Relationship, SQLModel

DB_FILE = "tictactoe.db"
SQLITE_URL = f"sqlite:///{DB_FILE}"


class GameBase(SQLModel):
    board_size: int = Field(default=3)


class Games(GameBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: GameStatus = Field(default=GameStatus.IN_PROGRESS)
    created_at: datetime = Field(default_factory=datetime.now)
    winner: Optional[Player] = Field(default=None)

    moves: List["Moves"] = Relationship(back_populates="game")


class GameOutput(GameBase):
    id: int
    status: GameStatus
    created_at: datetime
    move_count: int
    visual_board: str


class MoveBase(SQLModel):
    player: Player
    x: int
    y: int
    move_number: int
    created_at: datetime = Field(default_factory=datetime.now)


class Moves(MoveBase, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign Key
    game_id: int = Field(foreign_key="games.id")
    game: Games = Relationship(back_populates="moves")


class MoveHistoryItem(MoveBase):
    game_id: int


def init_db(engine: Engine):
    SQLModel.metadata.create_all(engine)
