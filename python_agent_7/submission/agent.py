from __future__ import annotations
import random
from typing import Tuple
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


# ---------------- Utility: count sides ----------------
def count_sides(board, r, c):
    return (
        board.horizontal_lines[r][c]
        + board.horizontal_lines[r + 1][c]
        + board.vertical_lines[r][c]
        + board.vertical_lines[r][c + 1]
    )


# ---------------- Chain detection ----------------
def detect_chains(board):
    visited = [[False for _ in range(board.cols - 1)] for _ in range(board.rows - 1)]
    chains = []
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            if visited[r][c]:
                continue
            sides = count_sides(board, r, c)
            if 2 <= sides < 4:
                stack = [(r, c)]
                chain = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < board.rows - 1 and 0 <= cc < board.cols - 1):
                        continue
                    if visited[cr][cc]:
                        continue
                    s = count_sides(board, cr, cc)
                    if not (2 <= s < 4):
                        continue
                    visited[cr][cc] = True
                    chain.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((cr + dr, cc + dc))
                if chain:
                    chains.append(chain)
    return chains


# ---------------- Chain-control helpers ----------------
def choose_chain_to_open(chains):
    # Pick the shortest chain to sacrifice
    return min(chains, key=len)

def chain_risk_score(board, move):
    # Fewer neighboring 2-sided boxes → safer
    boxes = []
    if move.is_horizontal:
        if move.row > 0: boxes.append((move.row-1, move.col))
        if move.row < board.rows-1: boxes.append((move.row, move.col))
    else:
        if move.col > 0: boxes.append((move.row, move.col-1))
        if move.col < board.cols-1: boxes.append((move.row, move.col))
    risk = sum(1 for (r,c) in boxes if count_sides(board,r,c) >= 2)
    return risk + random.random()*0.01

def get_moves_to_open_chain(board, chain):
    # All valid non-capturing moves that touch this chain
    moves = []
    for (r, c) in chain:
        for m in board.get_valid_moves():
            if board.is_capturing_move(m):
                continue
            if m.is_horizontal and (m.row == r or m.row == r + 1) and m.col == c:
                moves.append(m)
            elif not m.is_horizontal and (m.col == c or m.col == c + 1) and m.row == r:
                moves.append(m)
    return moves


# ---------------- Main Bot 8 ----------------
def make_move(controller: Controller) -> Tuple[bool, Move]:
    """
    Bot 8: chain-control heuristic
      1. Captures immediately.
      2. Avoids 3-sided boxes.
      3. Avoids long chains midgame.
      4. When forced, opens the shortest chain (chain control).
      5. Otherwise random safe move.
    """
    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        return False, Move(0, 0, True)

    # --- Phase 1: capture immediately ---
    capturing = [m for m in valid_moves if board.is_capturing_move(m)]
    if capturing:
        move = random.choice(capturing)
        req = controller.make_move(move)
        log(f"🟢 Capture: {move}")
        return req, move

    # --- Phase 2: precompute 3-sided boxes ---
    three_sided = {(r, c)
                   for r in range(board.rows - 1)
                   for c in range(board.cols - 1)
                   if count_sides(board, r, c) == 3}

    # --- Phase 3: detect chains ---
    chains = detect_chains(board)
    long_chains = [ch for ch in chains if len(ch) > 2]

    # --- Phase 4: classify moves ---
    safe, chain_touch, risky = [], [], []
    for m in valid_moves:

        def touches_three():
            if m.is_horizontal:
                return (
                    (m.row > 0 and (m.row - 1, m.col) in three_sided)
                    or (m.row < board.rows - 1 and (m.row, m.col) in three_sided)
                )
            else:
                return (
                    (m.col > 0 and (m.row, m.col - 1) in three_sided)
                    or (m.col < board.cols - 1 and (m.row, m.col) in three_sided)
                )

        def touches_chain():
            for chain in long_chains:
                for (cr, cc) in chain:
                    if (
                        m.is_horizontal
                        and (m.row == cr or m.row == cr + 1)
                        and m.col == cc
                    ) or (
                        not m.is_horizontal
                        and (m.col == cc or m.col == cc + 1)
                        and m.row == cr
                    ):
                        return True
            return False

        if touches_three():
            risky.append(m)
        elif touches_chain():
            chain_touch.append(m)
        else:
            safe.append(m)

    # --- Phase 5: choose move ---
    moves_left = len(valid_moves)
    total_boxes = (board.rows - 1) * (board.cols - 1)

    # Enter chain-control phase when few safe moves or many 3-sided boxes
    if (not safe and not chain_touch) or (len(three_sided) > 0.2 * total_boxes):
        if chains:
            if len(chains) % 2 == 0:
    # even chains: open smallest *2-chain* or safest chain start
               target = min(chains, key=len)
            else:
    # odd chains: same logic as before
               target = choose_chain_to_open(chains)




            openers = get_moves_to_open_chain(board, target)
            if openers:
                move = random.choice(openers)
                log(f"⚙️ Chain-control: opening chain of len={len(target)} → {move}")
                req = controller.make_move(move)
                return req, move

    # Otherwise follow normal priority
    if safe:
        move = min(safe, key=lambda m: chain_risk_score(board, m))

        log(f"🟡 Safe: {move}")
    elif chain_touch:
        move = random.choice(chain_touch)
        log(f"🟠 Chain-touch: {move}")
    else:
        move = random.choice(risky)
        log(f"🔴 Risky: {move}")

    req = controller.make_move(move)
    log(f"Move made: {move}, requires_more={req}")
    return req, move


__all__ = ["make_move"]








