from __future__ import annotations

import random
from typing import Tuple

from ..controller import Controller
from ..move import Move
from ..custom_logger import log


def make_move(controller: Controller) -> Tuple[bool, Move]:
    """Pick a random valid move, mirroring the default C++ submission."""
    log('Hi from make_move function')
    time_ms = controller.get_time_ms()
    log(f'Time remaining: {time_ms} ms')

    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        dummy_move = Move(0, 0, True)
        return False, dummy_move

    move = random.choice(valid_moves)
    requires_more = controller.make_move(move)
    log(f'Made move: {move}, requires more: {requires_more}')
    return requires_more, move


__all__ = ["make_move"]
