from __future__ import annotations
import time, random, math
from typing import Optional, List
from ..controller import Controller
from ..move import Move
from ..board import Board, PlayerSide
from ..custom_logger import log


TOTAL_GAME_TIME = 60.0  # total seconds for full match
MCTS_START_TIME: Optional[float] = None
MCTS_ROOT: Optional["MCTSNode"] = None


# ---------------- Node Definition ----------------
class MCTSNode:
    def __init__(
        self,
        board: Board,
        move: Optional[Move] = None,
        side: Optional[PlayerSide] = None,
        parent: Optional["MCTSNode"] = None,
    ):
        self.board = board
        self.move = move
        self.side = side
        self.parent = parent
        self.children: List[MCTSNode] = []
        self.untried_moves: List[Move] = board.get_valid_moves()
        self.visits = 0
        self.value = 0.0

    def uct_child(self, c: float = 1.4) -> Optional["MCTSNode"]:
        if not self.children:
            return None
        best_score, best = -1e9, None
        for ch in self.children:
            if ch.visits == 0:
                return ch
            exploit = ch.value / ch.visits
            explore = c * math.sqrt(math.log(self.visits + 1e-9) / ch.visits)
            score = exploit + explore
            if score > best_score:
                best_score, best = score, ch
        return best

    def best_child(self) -> Optional["MCTSNode"]:
        if not self.children:
            return None
        return max(self.children, key=lambda ch: ch.visits)

    def update(self, result: float):
        self.visits += 1
        self.value += result


# ---------------- Rollout ----------------
def simulate_random_game(board: Board, side: PlayerSide) -> float:
    """Play random moves until completion and return +1 / -1 score."""
    b = board.clone()
    s = side
    while not b.is_completed():
        moves = b.get_valid_moves()
        if not moves:
            break
        m = random.choice(moves)
        cont = b.make_move(m, s)
        if not cont:
            s = s.opponent()
    scores = b.get_scores()
    return scores[side] - scores[side.opponent()]


# ---------------- MCTS Core ----------------
def mcts_search(root: MCTSNode, my_side: PlayerSide, sec_budget: float) -> Optional[Move]:
    end_time = time.time() + sec_budget
    iters = 0
    while time.time() < end_time:
        node = root
        board = root.board.clone()
        side = my_side

        # --- Selection ---
        while not node.untried_moves and node.children:
            node = node.uct_child()
            if node is None:
                break
            if node.move:
                cont = board.make_move(node.move, side)
                if not cont:
                    side = side.opponent()

        # --- Expansion ---
        if node and node.untried_moves:
            m = random.choice(node.untried_moves)
            cont = board.make_move(m, side)
            next_side = side if cont else side.opponent()
            child = MCTSNode(board.clone(), move=m, side=next_side, parent=node)
            node.children.append(child)
            node.untried_moves.remove(m)
            node = child
            side = next_side

        # --- Simulation ---
        result = simulate_random_game(board, side)

        # --- Backpropagation ---
        while node:
            if node.side == my_side:
                node.update(result)
            else:
                node.update(-result)
            node = node.parent

        iters += 1

    log(f"[MCTS] {iters} rollouts in {sec_budget:.2f}s")
    best = root.best_child()
    return best.move if best else None


# ---------------- Main Interface ----------------
def make_move(controller: Controller):
    global MCTS_ROOT, MCTS_START_TIME
    board = controller.get_current_board()
    my_side = controller.get_my_side()

    if MCTS_START_TIME is None:
        MCTS_START_TIME = time.time()
    elapsed = time.time() - MCTS_START_TIME
    time_left = max(1.0, TOTAL_GAME_TIME - elapsed)
    valid_moves = board.get_valid_moves()
    if not valid_moves:
        return False, Move(0, 0, True)

    per_move_time = min(time_left / max(1, len(valid_moves)), 1.5)  # ≤1.5 s per move

    # continue from existing subtree if matching state
    if not MCTS_ROOT or not MCTS_ROOT.children:
        MCTS_ROOT = MCTSNode(board.clone(), None, my_side)
    else:
        matched = None
        for ch in MCTS_ROOT.children:
            if (ch.board.horizontal_lines == board.horizontal_lines and
                ch.board.vertical_lines == board.vertical_lines):
                matched = ch
                break
        MCTS_ROOT = matched or MCTSNode(board.clone(), None, my_side)

    move = mcts_search(MCTS_ROOT, my_side, per_move_time)
    if move is None:
        move = random.choice(valid_moves)

    requires_more = controller.make_move(move)
    log(f"[MCTS] Move: {move}, more? {requires_more}")
    return requires_more, move


__all__ = ["make_move"]



