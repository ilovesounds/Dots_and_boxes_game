from __future__ import annotations
import random
import time
from typing import Tuple, List, Optional
from ..controller import Controller
from ..move import Move
from ..custom_logger import log


HOTSPOT_RADIUS = 3            
LOOKAHEAD_DEPTH = 3           
LOOKAHEAD_CANDIDATES = 8      
MONTE_TIE_ROLLOUTS = 12       
MONTE_PLAYOUT_DEPTH = 30      
ENDGAME_MOVE_THRESHOLD = 60   
MINIMUM_TIME_FOR_LOOKAHEAD = 0.4  

def count_sides(board, r: int, c: int) -> int:
    return (
        board.horizontal_lines[r][c]
        + board.horizontal_lines[r + 1][c]
        + board.vertical_lines[r][c]
        + board.vertical_lines[r][c + 1]
    )


def detect_chains(board) -> List[List[tuple]]:
    visited = [[False for _ in range(board.cols - 1)] for _ in range(board.rows - 1)]
    chains = []
    for r in range(board.rows - 1):
        for c in range(board.cols - 1):
            if visited[r][c]:
                continue
            s = count_sides(board, r, c)
            if 2 <= s < 4:
                stack = [(r, c)]
                chain = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < board.rows - 1 and 0 <= cc < board.cols - 1):
                        continue
                    if visited[cr][cc]:
                        continue
                    cs = count_sides(board, cr, cc)
                    if not (2 <= cs < 4):
                        continue
                    visited[cr][cc] = True
                    chain.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((cr + dr, cc + dc))
                if chain:
                    chains.append(chain)
    return chains


def choose_chain_to_open(chains: List[List[tuple]]) -> List[tuple]:
    return min(chains, key=len)


def get_moves_to_open_chain(board, chain: List[tuple]) -> List[Move]:
    moves = []
    valid = board.get_valid_moves()
    for (r, c) in chain:
        for m in valid:
            if board.is_capturing_move(m):
                continue
            if m.is_horizontal and (m.row == r or m.row == r + 1) and m.col == c:
                moves.append(m)
            elif not m.is_horizontal and (m.col == c or m.col == c + 1) and m.row == r:
                moves.append(m)
    return moves



def compute_heatmap(board) -> List[List[int]]:
    rows = board.rows - 1
    cols = board.cols - 1
    heat = [[0 for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            heat[r][c] = count_sides(board, r, c)
    return heat


def local_move_score(board, move: Move, heatmap: Optional[List[List[int]]] = None) -> float:

    if board.is_capturing_move(move):
        return 100.0

    score = 0.0
    
    boxes = []
    if move.is_horizontal:
        if move.row > 0:
            boxes.append((move.row - 1, move.col))
        if move.row < board.rows - 1:
            boxes.append((move.row, move.col))
    else:
        if move.col > 0:
            boxes.append((move.row, move.col - 1))
        if move.col < board.cols - 1:
            boxes.append((move.row, move.col))

    
    for (r, c) in boxes:
        s_old = count_sides(board, r, c)
        s_new = s_old + 1
        if s_new == 3:
            score -= 90.0
        elif s_old == 1 and s_new == 2:
            score += 8.0
        elif s_old == 0 and s_new == 1:
            score += 1.0

    
    if heatmap is not None:
        
        total = 0
        cnt = 0
        for (r, c) in boxes:
            for dr in range(-HOTSPOT_RADIUS, HOTSPOT_RADIUS + 1):
                for dc in range(-HOTSPOT_RADIUS, HOTSPOT_RADIUS + 1):
                    rr = r + dr
                    cc = c + dc
                    if 0 <= rr < len(heatmap) and 0 <= cc < len(heatmap[0]):
                        total += heatmap[rr][cc]
                        cnt += 1
        if cnt > 0:
            avg = total / cnt
            
            score += max(0.0, 10.0 - avg)

    
    score += random.random() * 0.001
    return score



def shallow_minimax_score(board, depth: int, my_side, maximizing: bool, time_deadline: float) -> float:

    if time.time() > time_deadline:
        raise TimeoutError()

    if depth == 0 or board.is_completed():
        s = board.get_scores()
        return s[my_side] - s[my_side.opponent()]

    valid = board.get_valid_moves()
    
    captures = [m for m in valid if board.is_capturing_move(m)]
    others = [m for m in valid if not board.is_capturing_move(m)]
    ordered = captures + others[:min(len(others), 20)]  

    if maximizing:
        best = float("-inf")
        for m in ordered:
            if time.time() > time_deadline:
                raise TimeoutError()
            child = board.clone()
            cont = child.make_move(m, my_side)
            next_max = maximizing if cont else False
            val = shallow_minimax_score(child, depth - 1, my_side, next_max, time_deadline)
            if val > best:
                best = val
        return best
    else:
        best = float("inf")
        opp = my_side.opponent()
        for m in ordered:
            if time.time() > time_deadline:
                raise TimeoutError()
            child = board.clone()
            cont = child.make_move(m, opp)
            next_max = False if cont else True
            val = shallow_minimax_score(child, depth - 1, my_side, next_max, time_deadline)
            if val < best:
                best = val
        return best



def monte_tie_breaker(board, my_side, candidates: List[Move], rollouts: int, depth: int) -> Move:
    best = None
    best_score = float("-inf")
    for m in candidates:
        total = 0.0
        for _ in range(rollouts):
            clone = board.clone()
            clone.make_move(m, my_side)
            total += _simulate_random_playout_score(clone, my_side, limit=depth)
        avg = total / max(1, rollouts)
        if avg > best_score:
            best_score = avg
            best = m
    return best if best is not None else random.choice(candidates)


def _simulate_random_playout_score(board, my_side, limit: int) -> float:
    side = my_side
    for _ in range(limit):
        if board.is_completed():
            break
        vm = board.get_valid_moves()
        if not vm:
            break
        mv = random.choice(vm)
        cont = board.make_move(mv, side)
        if not cont:
            side = side.opponent()
    s = board.get_scores()
    return s[my_side] - s[my_side.opponent()]



def make_move(controller: Controller) -> Tuple[bool, Move]:
    t0 = time.time()
    board = controller.get_current_board()
    my_side = controller.get_my_side()
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        return False, Move(0, 0, True)

    
    engine_time_ms = -1
    try:
        engine_time_ms = controller.get_time_ms()
    except Exception:
        engine_time_ms = -1
    if engine_time_ms and engine_time_ms > 0:
        remaining_time = engine_time_ms / 1000.0
    else:
        
        remaining_time = 2.0

    
    capturing = [m for m in valid_moves if board.is_capturing_move(m)]
    if capturing:
        move = random.choice(capturing)
        req = controller.make_move(move)
        log(f"[quick capture] Chosen: {move}")
        return req, move

    
    heatmap = compute_heatmap(board)
    chains = detect_chains(board)
    long_chains = [ch for ch in chains if len(ch) > 2]

    
    scored_moves = []
    safe_moves = []
    risky_moves = []
    three_sided = {(r, c) for r in range(board.rows - 1) for c in range(board.cols - 1) if count_sides(board, r, c) == 3}

    for m in valid_moves:
        
        def touches_three(mv: Move) -> bool:
            if mv.is_horizontal:
                if mv.row > 0 and (mv.row - 1, mv.col) in three_sided:
                    return True
                if mv.row < board.rows - 1 and (mv.row, mv.col) in three_sided:
                    return True
            else:
                if mv.col > 0 and (mv.row, mv.col - 1) in three_sided:
                    return True
                if mv.col < board.cols - 1 and (mv.row, mv.col) in three_sided:
                    return True
            return False

        def touches_long_chain(mv: Move) -> bool:
            for chain in long_chains:
                for (cr, cc) in chain:
                    if (
                        mv.is_horizontal
                        and (mv.row == cr or mv.row == cr + 1)
                        and mv.col == cc
                    ) or (
                        not mv.is_horizontal
                        and (mv.col == cc or mv.col == cc + 1)
                        and mv.row == cr
                    ):
                        return True
            return False

        sc = local_move_score(board, m, heatmap)
        scored_moves.append((sc, m))
        if touches_three(m):
            risky_moves.append(m)
        elif touches_long_chain(m):
            
            risky_moves.append(m)
        else:
            safe_moves.append(m)

    
    if safe_moves:
        scored_moves = [(s, m) for (s, m) in scored_moves if m in safe_moves]
    else:
        
        pass

    
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    candidates = [m for (_, m) in scored_moves][:LOOKAHEAD_CANDIDATES]

    
    moves_left = len(valid_moves)
    if moves_left > 300:
        chosen = candidates[0] if candidates else random.choice(valid_moves)
        req = controller.make_move(chosen)
        log(f"[fast pick] Chosen: {chosen}")
        return req, chosen


    time_deadline = time.time() + min(remaining_time * 0.4, 0.8)  
    can_do_lookahead = (remaining_time >= MINIMUM_TIME_FOR_LOOKAHEAD) and (moves_left <= ENDGAME_MOVE_THRESHOLD)

    if can_do_lookahead and candidates:
        
        best_move = None
        best_score = float("-inf")
        per_candidate_deadline = time_deadline
        for c in candidates:
            
            if time.time() > time_deadline:
                break
            
            try:
                score = shallow_minimax_score(board.clone(), LOOKAHEAD_DEPTH, my_side, True, time_deadline)
            except TimeoutError:
                break

            try:
                clone = board.clone()
                clone.make_move(c, my_side)
                score = shallow_minimax_score(clone, LOOKAHEAD_DEPTH - 1, my_side, False, time_deadline)
            except TimeoutError:
                continue
            if score > best_score:
                best_score = score
                best_move = c

        if best_move:
            req = controller.make_move(best_move)
            log(f"[lookahead] Chosen: {best_move} score={best_score:.2f}")
            return req, best_move

    
    if candidates:
        top_score = scored_moves[0][0] if scored_moves else 0.0
        top_candidates = [m for (s, m) in scored_moves if abs(s - top_score) < 1e-6][:4]
        if len(top_candidates) > 1:
            
            tie_choice = monte_tie_breaker(board, my_side, top_candidates, MONTE_TIE_ROLLOUTS, MONTE_PLAYOUT_DEPTH)
            req = controller.make_move(tie_choice)
            log(f"[mc tiebreak] Chosen: {tie_choice}")
            return req, tie_choice

    
    if candidates:
        chosen = candidates[0]
    elif safe_moves:
        chosen = safe_moves[0]
    else:
        chosen = random.choice(valid_moves)

    req = controller.make_move(chosen)
    log(f"[final pick] Chosen: {chosen}")
    return req, chosen


__all__ = ["make_move"]










