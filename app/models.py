from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Player(str, Enum):
    X = "X"
    O = "O"


class GameStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    X_WON = "X_WON"
    O_WON = "O_WON"
    DRAW = "DRAW"


class MoveInput(BaseModel):
    x: int
    y: int


class MoveOutput(BaseModel):
    player: Player
    x: int
    y: int
    move_number: int
    timestamp: str


class GameOutput(BaseModel):
    game_id: int
    status: GameStatus
    created_at: datetime
    move_count: int
    visual_board: str


class MoveHistoryItem(BaseModel):
    game_id: int
    player: str
    x: int
    y: int
    move_number: int
    created_at: datetime
