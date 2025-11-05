from __future__ import annotations
import random
from typing import Tuple
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


# ---------------- Utility: count how many sides a box has ----------------
def count_sides(board, r: int, c: int) -> int:
    return (
        board.horizontal_lines[r][c]
        + board.horizontal_lines[r + 1][c]
        + board.vertical_lines[r][c]
        + board.vertical_lines[r][c + 1]
    )


# ---------------- Fast heuristic bot ----------------
def make_move(controller: Controller) -> Tuple[bool, Move]:
    """
    Ultra-fast heuristic bot (<70 ms per move on 30×30):

    Priority:
      1. Capture any box available.
      2. Avoid adding a 3rd side to a box (risky).
      3. Otherwise choose randomly among remaining moves.
    """
    log("Hi from ultra-fast heuristic make_move()")

    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        dummy = Move(0, 0, True)
        return False, dummy

    # -------- Phase 1: take captures immediately --------
    capturing_moves = [m for m in valid_moves if board.is_capturing_move(m)]
    if capturing_moves:
        move = random.choice(capturing_moves)
        requires_more = controller.make_move(move)
        log(f"🟢 Capturing move chosen: {move}")
        return requires_more, move

    # -------- Phase 2: pre-compute 3-sided boxes --------
    three_sided = set()
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            if count_sides(board, r, c) == 3:
                three_sided.add((r, c))

    # -------- Phase 3: classify safe vs risky --------
    safe_moves, risky_moves = [], []

    for move in valid_moves:

        def touches_three() -> bool:
            """Check if move is adjacent to a 3-sided box."""
            if move.is_horizontal:
                # box above
                if move.row > 0 and (move.row - 1, move.col) in three_sided:
                    return True
                # box below
                if move.row < board.rows - 1 and (move.row, move.col) in three_sided:
                    return True
            else:
                # box left
                if move.col > 0 and (move.row, move.col - 1) in three_sided:
                    return True
                # box right
                if move.col < board.cols - 1 and (move.row, move.col) in three_sided:
                    return True
            return False

        if touches_three():
            risky_moves.append(move)
        else:
            safe_moves.append(move)

    # -------- Phase 4: choose move --------
    if safe_moves:
        move = random.choice(safe_moves)
        log(f"🟡 Safe move chosen: {move}")
    else:
        move = random.choice(risky_moves)
        log(f"🔴 Risky move chosen: {move}")

    requires_more = controller.make_move(move)
    log(f"Made move: {move}, requires_more: {requires_more}")
    return requires_more, move


__all__ = ["make_move"]



