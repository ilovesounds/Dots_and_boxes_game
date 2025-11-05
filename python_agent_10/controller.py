from __future__ import annotations

import sys
from typing import List, Optional

from .board import Board, PlayerSide
from .move import Move
from .token_stream import TokenStream


class Controller:
    """Handles communication with the game engine and mirrors the C++ API."""

    def __init__(
        self,
        board: Optional[Board] = None,
        player_side: Optional[PlayerSide] = None,
        *,
        use_protocol: bool = True,
        tokens: Optional[TokenStream] = None,
    ) -> None:
        self.use_protocol = use_protocol
        self._pending_moves: List[Move] = []
        self._prev_opp_moves: List[Move] = []
        self._are_prev_opp_moves_cached = True
        self._tokens = tokens if tokens is not None else (TokenStream(sys.stdin) if use_protocol else None)

        if board is not None and player_side is not None:
            self.board = board
            self.player_side = player_side
        else:
            if not use_protocol:
                raise ValueError("Snapshot mode requires an explicit board and player side")
            if self._tokens is None:
                raise RuntimeError("Protocol mode requires a token stream")
            self._write_line("!REQ_PLAYER_NUM")
            self.player_side = PlayerSide(self._tokens.next_int())
            self._write_line("!REQ_BOARD")
            self.board = Board.from_token_stream(self._tokens)

    def get_current_board(self) -> Board:
        return self.board

    def get_my_side(self) -> PlayerSide:
        return self.player_side

    def get_opponent_side(self) -> PlayerSide:
        return self.player_side.opponent()

    def get_time_ms(self) -> int:
        if not self.use_protocol:
            return -1
        assert self._tokens is not None
        self._write_line("!REQ_TIME")
        return self._tokens.next_int()

    def make_move(self, move: Move) -> bool:
        self._pending_moves.append(move)
        requires_more = self.board.requires_continuation(move)
        self.board.make_move(move, self.player_side)

        if not requires_more:
            if self.use_protocol:
                self._flush_pending_moves()
                if not self.board.is_completed():
                    for opponent_move in self.get_opponent_moves():
                        self.board.make_move(opponent_move, self.get_opponent_side())
            else:
                self._pending_moves.clear()

        return requires_more

    def make_moves(self, moves: List[Move]) -> bool:
        requires_more = False
        for move in moves:
            requires_more = self.make_move(move)
        return requires_more

    def get_opponent_moves(self) -> List[Move]:
        if self._are_prev_opp_moves_cached or not self.use_protocol:
            return self._prev_opp_moves
        assert self._tokens is not None
        self._write_line("!REQ_MOVES")
        count = self._tokens.next_int()
        self._prev_opp_moves = [Move.from_token_stream(self._tokens) for _ in range(count)]
        self._are_prev_opp_moves_cached = True
        return self._prev_opp_moves

    def _flush_pending_moves(self) -> None:
        if not self._pending_moves:
            return
        self._write_line("!SENDING_MOVES")
        sys.stdout.write(f"{len(self._pending_moves)}\n")
        for move in self._pending_moves:
            sys.stdout.write(move.to_protocol() + "\n")
        sys.stdout.flush()
        self._pending_moves.clear()
        self._are_prev_opp_moves_cached = False

    @staticmethod
    def _write_line(message: str) -> None:
        sys.stdout.write(message + "\n")
        sys.stdout.flush()
