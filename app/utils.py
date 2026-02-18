from typing import List, Optional

from db import Games, Moves
from models import *


def get_board_state(game: Games):
    """Reconstructs the board from the list of moves in the game object."""
    size = game.board_size
    board = [["." for _ in range(size)] for _ in range(size)]
    for m in game.moves:
        mapped_y = (size - 1) - m.y
        board[mapped_y][m.x] = m.player
    return board


def check_win(board: List[List[str]], size: int) -> Optional[Player]:
    for i in range(size):
        if all(board[i][j] == board[i][0] != "." for j in range(size)):
            return Player(board[i][0])
        if all(board[j][i] == board[0][i] != "." for j in range(size)):
            return Player(board[0][i])

    if all(board[i][i] == board[0][0] != "." for i in range(size)):
        return Player(board[0][0])
    if all(board[i][size - 1 - i] == board[0][size - 1] != "." for i in range(size)):
        return Player(board[0][size - 1])

    return None


def is_board_full(board: List[List[str]]) -> bool:
    return all(cell != "." for row in board for cell in row)


def format_board_ascii(board: List[List[str]]) -> str:
    """The visualizer."""
    display = "\n"
    size = len(board)
    divider_length = (4 * size) - 3
    divider_line = "  | " + "-" * divider_length + "\n"
    for i, row in enumerate(board):
        y_label = (size - 1) - i
        display += f"{y_label} | " + " | ".join(row) + " \n"
        if i < size - 1:
            display += divider_line

    display += "  +" + "=" * (divider_length + 1) + "\n"

    x_labels = "    " + "   ".join(str(x) for x in range(size)) + "\n"
    display += x_labels

    return display
