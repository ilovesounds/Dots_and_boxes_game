from __future__ import annotations

from .agent import Agent
from .controller import Controller


def main() -> None:
    agent = Agent(Controller())
    agent.init()
    agent.run()


if __name__ == "__main__":
    main()
