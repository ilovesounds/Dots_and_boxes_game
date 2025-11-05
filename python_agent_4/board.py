from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
from typing import Dict, Iterable, List, Sequence, Tuple

from .move import Move
from .token_stream import TokenStream


class PlayerSide(IntEnum):
    FIRST_PLAYER = 1
    SECOND_PLAYER = 2

    def opponent(self) -> "PlayerSide":
        return PlayerSide.SECOND_PLAYER if self is PlayerSide.FIRST_PLAYER else PlayerSide.FIRST_PLAYER


class GridOwner(IntEnum):
    UNSPECIFIED = 0
    FIRST_PLAYER = 1
    SECOND_PLAYER = 2
    PRE_FILLED = 3

    @staticmethod
    def from_side(side: PlayerSide) -> "GridOwner":
        if side is PlayerSide.FIRST_PLAYER:
            return GridOwner.FIRST_PLAYER
        if side is PlayerSide.SECOND_PLAYER:
            return GridOwner.SECOND_PLAYER
        raise ValueError(f"Unsupported player side: {side}")


class Board:
    """Game board state mirroring the behaviour of the C++ reference."""

    def __init__(
        self,
        rows: int,
        cols: int,
        horizontal_lines: Sequence[Sequence[int]],
        vertical_lines: Sequence[Sequence[int]],
        grid_owner: Sequence[Sequence[int | GridOwner]],
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.horizontal_lines: List[List[int]] = [list(row) for row in horizontal_lines]
        self.vertical_lines: List[List[int]] = [list(row) for row in vertical_lines]
        self.grid_owner: List[List[GridOwner]] = [
            [cell if isinstance(cell, GridOwner) else GridOwner(cell) for cell in row]
            for row in grid_owner
        ]

        self.scores: Dict[PlayerSide, int] = {
            PlayerSide.FIRST_PLAYER: 0,
            PlayerSide.SECOND_PLAYER: 0,
        }
        self.num_empty_grids = 0
        self.num_horizontal_lines_left = 0
        self.num_vertical_lines_left = 0
        self._recompute_metadata()

    @classmethod
    def from_token_stream(cls, tokens: TokenStream) -> "Board":
        rows = tokens.next_int()
        cols = tokens.next_int()
        horizontal = [[tokens.next_int() for _ in range(cols - 1)] for _ in range(rows)]
        vertical = [[tokens.next_int() for _ in range(cols)] for _ in range(rows - 1)]
        owners = [[tokens.next_int() for _ in range(cols - 1)] for _ in range(rows - 1)]
        return cls(rows, cols, horizontal, vertical, owners)

    def clone(self) -> "Board":
        return Board(
            self.rows,
            self.cols,
            deepcopy(self.horizontal_lines),
            deepcopy(self.vertical_lines),
            deepcopy(self.grid_owner),
        )

    def _recompute_metadata(self) -> None:
        self.num_horizontal_lines_left = sum(1 for row in self.horizontal_lines for cell in row if cell == 0)
        self.num_vertical_lines_left = sum(1 for row in self.vertical_lines for cell in row if cell == 0)
        self.num_empty_grids = 0
        self.scores[PlayerSide.FIRST_PLAYER] = 0
        self.scores[PlayerSide.SECOND_PLAYER] = 0
        for row in self.grid_owner:
            for owner in row:
                if owner is GridOwner.UNSPECIFIED:
                    self.num_empty_grids += 1
                elif owner is GridOwner.FIRST_PLAYER:
                    self.scores[PlayerSide.FIRST_PLAYER] += 1
                elif owner is GridOwner.SECOND_PLAYER:
                    self.scores[PlayerSide.SECOND_PLAYER] += 1

    def is_valid_move(self, move: Move) -> bool:
        if move.is_horizontal:
            if move.row < 0 or move.row >= self.rows:
                return False
            if move.col < 0 or move.col >= self.cols - 1:
                return False
            return self.horizontal_lines[move.row][move.col] == 0
        if move.row < 0 or move.row >= self.rows - 1:
            return False
        if move.col < 0 or move.col >= self.cols:
            return False
        return self.vertical_lines[move.row][move.col] == 0

    def requires_continuation(self, move: Move) -> bool:
        return self.is_capturing_move(move) and not self.is_completing_move(move)

    def is_completing_move(self, move: Move) -> bool:
        return (self.num_horizontal_lines_left + self.num_vertical_lines_left) == 1

    def is_capturing_move(self, move: Move) -> bool:
        return bool(get_capturing_grids(self, move))

    def make_move(self, move: Move, side: PlayerSide) -> bool:
        if not self.is_valid_move(move):
            raise ValueError(f"Invalid move attempted: {move}")

        capturing_grids = get_capturing_grids(self, move)
        is_completing = self.is_completing_move(move)

        for grid_row, grid_col in capturing_grids:
            previous_owner = self.grid_owner[grid_row][grid_col]
            if previous_owner is GridOwner.UNSPECIFIED:
                self.num_empty_grids -= 1
            elif previous_owner in (GridOwner.FIRST_PLAYER, GridOwner.SECOND_PLAYER):
                previous_side = PlayerSide(previous_owner.value)
                self.scores[previous_side] -= 1
            owner = GridOwner.from_side(side)
            self.grid_owner[grid_row][grid_col] = owner
            self.scores[side] += 1

        if move.is_horizontal:
            self.horizontal_lines[move.row][move.col] = 1
            self.num_horizontal_lines_left -= 1
        else:
            self.vertical_lines[move.row][move.col] = 1
            self.num_vertical_lines_left -= 1

        return bool(capturing_grids) and not is_completing

    def is_completed(self) -> bool:
        return self.num_empty_grids == 0

    def get_scores(self) -> Dict[PlayerSide, int]:
        return dict(self.scores)

    def get_valid_moves(self) -> List[Move]:
        moves: List[Move] = []
        for r in range(self.rows):
            for c in range(self.cols - 1):
                if self.horizontal_lines[r][c] == 0:
                    moves.append(Move(r, c, True))
        for r in range(self.rows - 1):
            for c in range(self.cols):
                if self.vertical_lines[r][c] == 0:
                    moves.append(Move(r, c, False))
        return moves


def get_capturing_grids(board: Board, move: Move) -> List[Tuple[int, int]]:
    capturing: List[Tuple[int, int]] = []
    if _is_capturing_above(board, move):
        capturing.append((move.row - 1, move.col))
    if _is_capturing_below(board, move):
        capturing.append((move.row, move.col))
    if _is_capturing_left(board, move):
        capturing.append((move.row, move.col - 1))
    if _is_capturing_right(board, move):
        capturing.append((move.row, move.col))
    return capturing


def _line_drawn(value: int) -> bool:
    return value != 0


def _is_capturing_above(board: Board, move: Move) -> bool:
    if not move.is_horizontal or move.row <= 0:
        return False
    return (
        _line_drawn(board.vertical_lines[move.row - 1][move.col])
        and _line_drawn(board.vertical_lines[move.row - 1][move.col + 1])
        and _line_drawn(board.horizontal_lines[move.row - 1][move.col])
    )


def _is_capturing_below(board: Board, move: Move) -> bool:
    if not move.is_horizontal or move.row >= board.rows - 1:
        return False
    return (
        _line_drawn(board.vertical_lines[move.row][move.col])
        and _line_drawn(board.vertical_lines[move.row][move.col + 1])
        and _line_drawn(board.horizontal_lines[move.row + 1][move.col])
    )


def _is_capturing_left(board: Board, move: Move) -> bool:
    if move.is_horizontal or move.col <= 0:
        return False
    return (
        _line_drawn(board.horizontal_lines[move.row][move.col - 1])
        and _line_drawn(board.horizontal_lines[move.row + 1][move.col - 1])
        and _line_drawn(board.vertical_lines[move.row][move.col - 1])
    )


def _is_capturing_right(board: Board, move: Move) -> bool:
    if move.is_horizontal or move.col >= board.cols - 1:
        return False
    return (
        _line_drawn(board.horizontal_lines[move.row][move.col])
        and _line_drawn(board.horizontal_lines[move.row + 1][move.col])
        and _line_drawn(board.vertical_lines[move.row][move.col + 1])
    )
