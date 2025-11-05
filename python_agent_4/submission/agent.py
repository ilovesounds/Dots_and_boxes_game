from __future__ import annotations
import random
from typing import Tuple
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


# -------------------- Utility: count how many sides a box has --------------------
def count_sides(board, r: int, c: int) -> int:
    return (
        board.horizontal_lines[r][c]
        + board.horizontal_lines[r + 1][c]
        + board.vertical_lines[r][c]
        + board.vertical_lines[r][c + 1]
    )


# -------------------- Chain detection (DFS) --------------------
def dfs_collect_chain(board, r: int, c: int, visited, chain) -> None:
    if visited[r][c]:
        return
    visited[r][c] = True
    sides = count_sides(board, r, c)
    if sides < 2 or sides == 4:
        return  # Not part of a chain
    chain.append((r, c))
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < board.rows - 1 and 0 <= nc < board.cols - 1:
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


# -------------------- Board evaluation heuristic --------------------
def evaluate_board(board, my_side):
    scores = board.get_scores()
    my_score = scores[my_side]
    opp_score = scores[my_side.opponent()]

    # Penalty for leaving 3-sided boxes (dangerous)
    penalty = 0.0
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            s = count_sides(board, r, c)
            if s == 3:
                penalty += 0.3

    # Bonus for capturing boxes
    return (my_score - opp_score) - penalty


# -------------------- Alpha–Beta Minimax --------------------
def minimax(board, depth, alpha, beta, maximizing, my_side):
    if depth == 0 or board.is_completed():
        return evaluate_board(board, my_side), None

    best_move = None
    valid_moves = board.get_valid_moves()

    # Move ordering: capturing moves first
    capturing = [m for m in valid_moves if board.is_capturing_move(m)]
    others = [m for m in valid_moves if not board.is_capturing_move(m)]
    ordered_moves = capturing + others[:40]  # limit branching

    if maximizing:
        value = float("-inf")
        for move in ordered_moves:
            child = board.clone()
            child.make_move(move, my_side)
            score, _ = minimax(child, depth - 1, alpha, beta, False, my_side)
            if score > value:
                value, best_move = score, move
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = float("inf")
        for move in ordered_moves:
            child = board.clone()
            child.make_move(move, my_side.opponent())
            score, _ = minimax(child, depth - 1, alpha, beta, True, my_side)
            if score < value:
                value, best_move = score, move
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


# -------------------- Main decision logic --------------------
def make_move(controller: Controller) -> Tuple[bool, Move]:
    """
    Hybrid bot:
      - Early game: greedy + chain-aware heuristics
      - Late game: depth-2 minimax for tactical precision
    """
    log("Hi from chain-aware + minimax bot")

    time_ms = controller.get_time_ms()
    log(f"Time remaining: {time_ms} ms")

    board = controller.get_current_board()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        dummy_move = Move(0, 0, True)
        return False, dummy_move

    moves_left = len(valid_moves)
    log(f"Valid moves remaining: {moves_left}")

    # --- Switch to minimax in late game ---
    if moves_left < 100:
        log("🧠 Using minimax (depth=2) for endgame")
        _, move = minimax(
            board,
            depth=2,
            alpha=float("-inf"),
            beta=float("inf"),
            maximizing=True,
            my_side=controller.get_my_side(),
        )
        if move is None:
            move = random.choice(valid_moves)
        requires_more = controller.make_move(move)
        log(f"Minimax chose: {move}, requires_more: {requires_more}")
        return requires_more, move

    # --- Early/midgame: fast greedy logic ---
    chains = find_chains(board)
    long_chains = [chain for chain in chains if len(chain) > 1]
    log(f"Detected {len(chains)} chain(s): {[len(c) for c in chains]}")

    capturing_moves = []
    safe_moves = []
    risky_moves = []

    for move in valid_moves:
        if board.is_capturing_move(move):
            capturing_moves.append(move)
            continue

        test_board = board.clone()
        test_board.make_move(move, controller.get_my_side())

        three_sided_boxes = 0
        for r in range(test_board.rows - 1):
            for c in range(test_board.cols - 1):
                if count_sides(test_board, r, c) == 3:
                    three_sided_boxes += 1

        touches_chain = False
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
                    touches_chain = True
                    break
            if touches_chain:
                break

        if three_sided_boxes == 0 and not touches_chain:
            safe_moves.append(move)
        else:
            risky_moves.append(move)

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
    log(f"Made move: {move}, requires_more: {requires_more}")
    return requires_more, move


__all__ = ["make_move"]


