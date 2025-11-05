from __future__ import annotations
import random
from typing import Tuple
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


def make_move(controller: Controller) -> Tuple[bool, Move]:
    """Smarter greedy bot that captures boxes and avoids risky moves."""
    log("Hi from improved make_move function")

    time_ms = controller.get_time_ms()
    log(f"Time remaining: {time_ms} ms")

    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        dummy_move = Move(0, 0, True)
        return False, dummy_move

    # Categorize moves
    capturing_moves = []
    safe_moves = []
    risky_moves = []

    for move in valid_moves:
        # Simulate the move locally
        test_board = board.clone()

        # Is this a capturing move (completes a box)?
        captures = test_board.is_capturing_move(move)
        if captures:
            capturing_moves.append(move)
            continue

        # Otherwise, check if it creates a "3-sided box" (risky move)
        test_board.make_move(move, controller.get_my_side())
        # Count boxes with exactly 3 sides filled → bad
        three_sided_boxes = 0
        for r in range(test_board.rows - 1):
            for c in range(test_board.cols - 1):
                lines_filled = (
                    test_board.horizontal_lines[r][c]
                    + test_board.horizontal_lines[r + 1][c]
                    + test_board.vertical_lines[r][c]
                    + test_board.vertical_lines[r][c + 1]
                )
                if lines_filled == 3:
                    three_sided_boxes += 1

        if three_sided_boxes == 0:
            safe_moves.append(move)
        else:
            risky_moves.append(move)

    # Priority 1: Take captures
    if capturing_moves:
        move = random.choice(capturing_moves)
        log(f"🟢 Capturing move chosen: {move}")
    # Priority 2: Play safe
    elif safe_moves:
        move = random.choice(safe_moves)
        log(f"🟡 Safe move chosen: {move}")
    # Priority 3: Last resort
    else:
        move = random.choice(risky_moves)
        log(f"🔴 Risky move chosen: {move}")

    requires_more = controller.make_move(move)
    log(f"Made move: {move}, requires more: {requires_more}")
    return requires_more, move


__all__ = ["make_move"]

