from __future__ import annotations
import random
from typing import Tuple
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


# ------------------ Utility: Count how many sides a box has ------------------
def count_sides(board, r: int, c: int) -> int:
    return (
        board.horizontal_lines[r][c]
        + board.horizontal_lines[r + 1][c]
        + board.vertical_lines[r][c]
        + board.vertical_lines[r][c + 1]
    )


# ------------------ DFS chain detection ------------------
def dfs_collect_chain(board, r: int, c: int, visited, chain) -> None:
    if visited[r][c]:
        return
    visited[r][c] = True
    sides = count_sides(board, r, c)
    if sides < 2 or sides == 4:
        return  # Not part of a chain (too open or already captured)

    chain.append((r, c))
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < board.rows - 1 and 0 <= nc < board.cols - 1:
            # Continue the chain if neighbor has 2–3 sides filled
            n_sides = count_sides(board, nr, nc)
            if 2 <= n_sides < 4 and not visited[nr][nc]:
                dfs_collect_chain(board, nr, nc, visited, chain)


def find_chains(board):
    visited = [[False for _ in range(board.cols - 1)] for _ in range(board.rows - 1)]
    chains = []
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            if not visited[r][c]:
                sides = count_sides(board, r, c)
                if 2 <= sides < 4:
                    chain = []
                    dfs_collect_chain(board, r, c, visited, chain)
                    if chain:
                        chains.append(chain)
    return chains


# ------------------ MAIN BOT LOGIC ------------------
def make_move(controller: Controller) -> Tuple[bool, Move]:
    """
    Chain-aware greedy bot:
      1. Capture boxes when possible.
      2. Play safe moves (avoid creating 3-sided boxes).
      3. Avoid opening chains unless forced.
    """
    log("Hi from improved chain-aware make_move function")

    time_ms = controller.get_time_ms()
    log(f"Time remaining: {time_ms} ms")

    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        dummy_move = Move(0, 0, True)
        return False, dummy_move

    # --- Detect chains ---
    chains = find_chains(board)
    long_chains = [chain for chain in chains if len(chain) > 1]
    log(f"Detected {len(chains)} chain(s): {[len(c) for c in chains]}")

    capturing_moves = []
    safe_moves = []
    risky_moves = []

    for move in valid_moves:
        # If it completes a box, always take it
        if board.is_capturing_move(move):
            capturing_moves.append(move)
            continue

        # Clone the board to test move consequences
        test_board = board.clone()
        test_board.make_move(move, controller.get_my_side())

        # Count how many boxes become 3-sided (risky)
        three_sided_boxes = 0
        for r in range(test_board.rows - 1):
            for c in range(test_board.cols - 1):
                if count_sides(test_board, r, c) == 3:
                    three_sided_boxes += 1

        # Check if move touches a chain
        touches_chain = False
        for chain in long_chains:
            for (cr, cc) in chain:
                # If this move draws an edge adjacent to a chain box
                if (
                    move.is_horizontal
                    and (move.row == cr or move.row == cr + 1)
                    and move.col == cc
                ) or (
                    not move.is_horizontal
                    and (move.col == cc or move.col == cc + 1)
                    and move.row == cr
                ):
                    touches_chain = True
                    break
            if touches_chain:
                break

        if three_sided_boxes == 0 and not touches_chain:
            safe_moves.append(move)
        else:
            risky_moves.append(move)

    # --- Choose move by priority ---
    if capturing_moves:
        move = random.choice(capturing_moves)
        log(f"🟢 Capturing move chosen: {move}")
    elif safe_moves:
        move = random.choice(safe_moves)
        log(f"🟡 Safe move chosen: {move}")
    else:
        move = random.choice(risky_moves)
        log(f"🔴 Risky/chain-opening move chosen: {move}")

    requires_more = controller.make_move(move)
    log(f"Made move: {move}, requires more: {requires_more}")
    return requires_more, move


__all__ = ["make_move"]

