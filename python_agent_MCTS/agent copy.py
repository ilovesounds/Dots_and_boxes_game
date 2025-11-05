from __future__ import annotations

import random
from typing import Tuple

from .controller import Controller
from .move import Move
from .submission.agent import make_move
# import time
# from time import sleep


class Agent:
    """Python port of the starter C++ agent scaffolding."""

    def __init__(self, controller: Controller) -> None:
        self.controller = controller

    def init(self) -> None:
        # Use a fixed seed for deterministic behavior across runs
        # sleep(5)
        random.seed(42)

    def run(self) -> None:
        board = self.controller.get_current_board()
        while not board.is_completed():
            while True:
                requires_more, _ = make_move(self.controller)
                if not requires_more or board.is_completed():
                    break
            if board.is_completed():
                break


__all__ = ["Agent"]
