from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator


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

    @field_validator("x", "y")
    @classmethod
    def must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("must be >= 0")
        return v
    