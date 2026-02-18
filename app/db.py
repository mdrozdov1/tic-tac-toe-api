from datetime import datetime
from typing import List, Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, Relationship, SQLModel

from models import GameStatus

DB_FILE = "tictactoe.db"
SQLITE_URL = f"sqlite:///{DB_FILE}"


class Base:
    __table_args__ = {"extend_existing": True}

    @declared_attr # type: ignore
    def __tablename__(cls) -> str:
        return cls.__name__.lower() # type: ignore


class Games(Base, SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default=GameStatus.IN_PROGRESS.value)
    board_size: int = Field(default=3)
    winner: Optional[str] = None

    moves: List["Moves"] = Relationship(back_populates="game")


class Moves(Base, SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    player: str
    x: int
    y: int
    move_number: int
    created_at: datetime = Field(default_factory=datetime.now)

    # Foreign Key
    game_id: int = Field(foreign_key="games.id")
    game: Games = Relationship(back_populates="moves")


def init_db(engine: Engine):
    SQLModel.metadata.create_all(engine)
