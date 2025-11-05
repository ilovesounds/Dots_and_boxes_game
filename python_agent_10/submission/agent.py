from __future__ import annotations
import random
from typing import Tuple
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


# ---------- helpers ----------
def count_sides(board, r, c):
    return (
        board.horizontal_lines[r][c]
        + board.horizontal_lines[r + 1][c]
        + board.vertical_lines[r][c]
        + board.vertical_lines[r][c + 1]
    )


def local_heat(board, move):
    """Estimate how 'hot' (dangerous) the area around a move is."""
    heat = 0
    if move.is_horizontal:
        for dr in (-1, 0):
            rr = move.row + dr
            if 0 <= rr < board.rows - 1:
                for cc in (move.col, move.col - 1):
                    if 0 <= cc < board.cols - 1:
                        heat += max(0, count_sides(board, rr, cc) - 1)
    else:
        for dc in (-1, 0):
            cc = move.col + dc
            if 0 <= cc < board.cols - 1:
                for rr in (move.row, move.row - 1):
                    if 0 <= rr < board.rows - 1:
                        heat += max(0, count_sides(board, rr, cc) - 1)
    return heat


# ---------- main ultra-fast heuristic bot ----------
def make_move(controller: Controller) -> Tuple[bool, Move]:
    board = controller.get_current_board()
    my_side = controller.get_my_side()
    valid = board.get_valid_moves()
    if not valid:
        return False, Move(0, 0, True)

    # 1️⃣ take captures immediately
    capturing = [m for m in valid if board.is_capturing_move(m)]
    if capturing:
        m = random.choice(capturing)
        req = controller.make_move(m)
        log(f"🟢 capture {m}")
        return req, m

    # 2️⃣ precompute hot boxes
    three = {(r, c)
             for r in range(board.rows - 1)
             for c in range(board.cols - 1)
             if count_sides(board, r, c) == 3}

    best_move, best_score = None, float("-inf")
    for m in random.sample(valid, min(len(valid), 60)):  # check ≤60 moves
        score = 0.0
        # penalty if move borders 3-sided box
        touches_three = False
        if m.is_horizontal:
            if (m.row, m.col) in three or (m.row - 1, m.col) in three:
                touches_three = True
        else:
            if (m.row, m.col) in three or (m.row, m.col - 1) in three:
                touches_three = True
        if touches_three:
            score -= 5

        # smaller heat = safer
        score -= 0.8 * local_heat(board, m)

        # slight randomness for variety
        score += random.random() * 0.01
        if score > best_score:
            best_score, best_move = score, m

    if not best_move:
        best_move = random.choice(valid)

    req = controller.make_move(best_move)
    log(f"🤖 Bot11 chose {best_move}  |  score={best_score:.2f}")
    return req, best_move


__all__ = ["make_move"]












