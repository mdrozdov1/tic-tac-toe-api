from typing import List

import utils
from db import Games, Moves
from models import GameStatus, Player
from sqlmodel import Session


class GameService:
    def process_move(
        self, game: Games, x: int, y: int, session: Session
    ) -> List[List[str]]:
        """
        Apply the player's move then the AI's response.
        Validates coordinates, updates game status, and persists both moves.
        Returns the final board state.
        Raises ValueError for invalid moves ("Out of bounds" or "Square occupied").
        """
        assert game.id is not None
        board = utils.get_board_state(game)
        row = utils.map_y(y, game.board_size)

        if not (0 <= x < game.board_size and 0 <= y < game.board_size):
            raise ValueError("Out of bounds")
        if board[row][x] != ".":
            raise ValueError("Square occupied")

        base_move_number = len(game.moves)

        # Player move
        session.add(
            Moves(
                game_id=game.id,
                player=Player.X,
                x=x,
                y=y,
                move_number=base_move_number + 1,
            )
        )
        board[row][x] = Player.X

        if utils.check_win(board, game.board_size):
            game.status = GameStatus.X_WON
            game.winner = Player.X
            return board

        if utils.is_board_full(board):
            game.status = GameStatus.DRAW
            return board

        # AI move
        ai_coords = utils.get_ai_move(board, game.board_size)
        if ai_coords:
            ai_x, ai_y = ai_coords
            session.add(
                Moves(
                    game_id=game.id,
                    player=Player.O,
                    x=ai_x,
                    y=ai_y,
                    move_number=base_move_number + 2,
                )
            )
            board[utils.map_y(ai_y, game.board_size)][ai_x] = Player.O

            if utils.check_win(board, game.board_size):
                game.status = GameStatus.O_WON
                game.winner = Player.O
            elif utils.is_board_full(board):
                game.status = GameStatus.DRAW

        return board


game_service = GameService()
