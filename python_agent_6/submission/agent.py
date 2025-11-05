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


# ---------------- Light chain detection ----------------
def detect_chains(board):
    """
    Detects connected boxes with 2–3 sides filled.
    Returns a list of chains (each is a list of (r, c)).
    """
    visited = [[False for _ in range(board.cols - 1)] for _ in range(board.rows - 1)]
    chains = []
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            if visited[r][c]:
                continue
            sides = count_sides(board, r, c)
            if 2 <= sides < 4:
                chain = []
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if visited[cr][cc]:
                        continue
                    cs = count_sides(board, cr, cc)
                    if not (2 <= cs < 4):
                        continue
                    visited[cr][cc] = True
                    chain.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < board.rows - 1 and 0 <= nc < board.cols - 1:
                            stack.append((nr, nc))
                if chain:
                    chains.append(chain)
    return chains


# ---------------- Main fast, chain-aware bot ----------------
def make_move(controller: Controller) -> Tuple[bool, Move]:
    """
    Ultra-fast chain-aware heuristic bot:
      1. Take captures immediately.
      2. Avoid 3-sided boxes.
      3. Avoid opening long chains.
      4. Otherwise play random safe move.
    """
    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        return False, Move(0, 0, True)

    # --- Phase 1: capture immediately ---
    capturing = [m for m in valid_moves if board.is_capturing_move(m)]
    if capturing:
        move = random.choice(capturing)
        requires_more = controller.make_move(move)
        log(f"🟢 Capturing move chosen: {move}")
        return requires_more, move

    # --- Phase 2: pre-compute side counts ---
    three_sided = set()
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            if count_sides(board, r, c) == 3:
                three_sided.add((r, c))

    # --- Phase 3: detect existing chains ---
    chains = detect_chains(board)
    long_chains = [chain for chain in chains if len(chain) > 2]

    # --- Phase 4: classify safe vs risky vs chain-touching ---
    safe, chain_touch, risky = [], [], []
    for move in valid_moves:
        def touches_three():
            if move.is_horizontal:
                if move.row > 0 and (move.row - 1, move.col) in three_sided:
                    return True
                if move.row < board.rows - 1 and (move.row, move.col) in three_sided:
                    return True
            else:
                if move.col > 0 and (move.row, move.col - 1) in three_sided:
                    return True
                if move.col < board.cols - 1 and (move.row, move.col) in three_sided:
                    return True
            return False

        # Check if move touches a chain
        def touches_chain():
            for chain in long_chains:
                for (cr, cc) in chain:
                    if (
                        move.is_horizontal
                        and (move.row == cr or move.row == cr + 1)
                        and move.col == cc
                    ) or (
                        not move.is_horizontal
                        and (move.col == cc or move.col == cc + 1)
                        and move.row == cr
                    ):
                        return True
            return False

        if touches_three():
            risky.append(move)
        elif touches_chain():
            chain_touch.append(move)
        else:
            safe.append(move)

    # --- Phase 5: choose move by priority ---
    if safe:
        move = random.choice(safe)
        log(f"🟡 Safe move chosen: {move}")
    elif chain_touch:
        move = random.choice(chain_touch)
        log(f"🟠 Chain-touching move chosen: {move}")
    else:
        move = random.choice(risky)
        log(f"🔴 Risky move chosen: {move}")

    requires_more = controller.make_move(move)
    log(f"Made move: {move}, requires_more: {requires_more}")
    return requires_more, move


__all__ = ["make_move"]




